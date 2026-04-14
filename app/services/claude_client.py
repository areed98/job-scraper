"""
Claude API client for:
1. Scoring a job against the resume (0-100 + reasoning)
2. Tailoring the resume for a specific job + generating an HTML diff
"""
import os
import re
import difflib
import anthropic
from flask import current_app


def _client() -> anthropic.Anthropic:
    api_key = current_app.config.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")
    return anthropic.Anthropic(api_key=api_key)


def score_job(resume_text: str, job_title: str, job_description: str) -> tuple[int, str]:
    """
    Ask Claude to score how well the resume matches the job.
    Returns (score: int 0-100, analysis: str).
    """
    model = current_app.config.get("CLAUDE_MODEL", "claude-opus-4-5")
    prompt = f"""You are a recruiting expert. Given a resume and a job posting, rate how well the candidate matches the role.

Respond in this exact format (no other text):
SCORE: <integer 0-100>
ANALYSIS: <2-3 sentence explanation>

--- RESUME ---
{resume_text[:6000]}

--- JOB TITLE ---
{job_title}

--- JOB DESCRIPTION ---
{job_description[:4000]}
"""
    try:
        message = _client().messages.create(
            model=model,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        score_match = re.search(r"SCORE:\s*(\d+)", text)
        analysis_match = re.search(r"ANALYSIS:\s*(.+)", text, re.DOTALL)
        score = int(score_match.group(1)) if score_match else 0
        score = max(0, min(100, score))
        analysis = analysis_match.group(1).strip() if analysis_match else text
        return score, analysis
    except Exception as e:
        print(f"[claude] score_job error: {e}")
        return 0, "Could not score this job."


def tailor_resume(resume_text: str, job_title: str, job_description: str) -> tuple[str, str]:
    """
    Ask Claude to produce a lightly tailored version of the resume for the given job.
    Returns (tailored_text: str, diff_html: str).
    Only minor keyword/phrasing adjustments — no fabrication.
    """
    model = current_app.config.get("CLAUDE_MODEL", "claude-opus-4-5")
    prompt = f"""You are a professional resume writer. Given a resume and a job posting, make MINOR adjustments to the resume to better align with the job requirements.

Rules:
- Do NOT fabricate experience, skills, or accomplishments that are not already in the resume.
- Only reword, reorder, or add keywords that are truthfully implied by existing content.
- Keep the same overall structure and length.
- Return ONLY the full tailored resume text, no commentary.

--- ORIGINAL RESUME ---
{resume_text[:6000]}

--- JOB TITLE ---
{job_title}

--- JOB DESCRIPTION ---
{job_description[:4000]}
"""
    try:
        message = _client().messages.create(
            model=model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        tailored = message.content[0].text.strip()
        diff_html = _build_diff_html(resume_text, tailored)
        return tailored, diff_html
    except Exception as e:
        print(f"[claude] tailor_resume error: {e}")
        return resume_text, "<p>Could not generate tailored resume.</p>"


def _build_diff_html(original: str, tailored: str) -> str:
    """Build an HTML side-by-side diff using difflib."""
    differ = difflib.HtmlDiff(wrapcolumn=80)
    return differ.make_table(
        original.splitlines(),
        tailored.splitlines(),
        fromdesc="Original",
        todesc="Tailored",
        context=True,
        numlines=3,
    )
