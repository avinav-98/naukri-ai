import sqlite3
import re
from typing import List

from backend.config import DATABASE_PATHS
from backend.models.settings_model import get_keywords
from backend.utils.db_migrations import ensure_jobs_directory_schema


def _normalize(text: str) -> str:
    return " ".join((text or "").lower().split())


_STOPWORDS = {
    "and", "the", "with", "for", "you", "your", "our", "are", "this", "that", "will", "from",
    "have", "has", "had", "was", "were", "can", "able", "using", "use", "used", "job", "role",
    "work", "works", "working", "team", "years", "year", "month", "months", "location", "salary",
    "experience", "skills", "requirements", "preferred", "good", "strong", "knowledge",
}


def _extract_keywords(raw_keywords: str) -> List[str]:
    items = []
    for part in (raw_keywords or "").replace("\n", ",").split(","):
        token = part.strip()
        if token:
            items.append(token)
    unique = []
    seen = set()
    for kw in items:
        key = kw.lower()
        if key not in seen:
            seen.add(key)
            unique.append(kw)
    return unique


def _tokenize_keywords(text: str) -> List[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+.#-]{1,}", (text or "").lower())
    return [t for t in tokens if t not in _STOPWORDS and len(t) >= 3]


def extract_meaningful_keywords(text: str, limit: int = 30) -> List[str]:
    ranked: dict[str, int] = {}
    for tok in _tokenize_keywords(text):
        ranked[tok] = ranked.get(tok, 0) + 1
    ordered = sorted(ranked.items(), key=lambda x: (-x[1], x[0]))
    return [k for k, _ in ordered[:limit]]


def _settings_keywords(settings: dict | None) -> List[str]:
    if not settings:
        return []
    chunks = [
        settings.get("job_role", ""),
        settings.get("preferred_location", ""),
        settings.get("experience", ""),
        settings.get("salary", ""),
        settings.get("keywords", ""),
    ]
    return extract_meaningful_keywords(" ".join(chunks), limit=40)


def _keyword_score(job_text: str, resume_text: str, keywords: List[str]):
    matched = []
    for kw in keywords:
        low = kw.lower()
        if low in job_text or low in resume_text:
            matched.append(kw)
    if not keywords:
        return 0.0, matched
    return (len(matched) / len(keywords)) * 100.0, matched


def _overlap_score(job_text: str, resume_text: str):
    job_tokens = {t for t in job_text.split() if len(t) > 2}
    resume_tokens = {t for t in resume_text.split() if len(t) > 2}
    if not job_tokens or not resume_tokens:
        return 0.0
    overlap = len(job_tokens & resume_tokens)
    return (overlap / max(1, len(job_tokens))) * 100.0


def analyze_resume_matches(user_id: int, resume_text: str, keywords_raw: str = "", limit: int = 200):
    conn = sqlite3.connect(DATABASE_PATHS["jobs"])
    ensure_jobs_directory_schema(conn)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT job_title, company, location, experience, salary, job_description, job_url
        FROM jobs_directory
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = cur.fetchall()
    conn.close()

    stored_keywords = get_keywords(user_id=user_id)
    keywords = _extract_keywords(keywords_raw)
    for kw in stored_keywords:
        if kw not in keywords:
            keywords.append(kw)

    resume_norm = _normalize(resume_text)
    results = []
    for row in rows:
        title, company, location, experience, salary, description, url = row
        job_text = _normalize(f"{title} {company} {location} {experience} {salary} {description}")
        overlap = _overlap_score(job_text, resume_norm)
        keyword_part, matched = _keyword_score(job_text, resume_norm, keywords)
        score = round((0.65 * overlap) + (0.35 * keyword_part), 2)
        results.append(
            {
                "title": title,
                "company": company,
                "location": location,
                "job_url": url,
                "score": score,
                "matched_keywords": matched,
            }
        )
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def resume_match_score_for_job(job: dict, resume_text: str, keywords_raw: str = "") -> dict:
    title = job.get("title", "")
    company = job.get("company", "")
    location = job.get("location", "")
    experience = job.get("experience", "")
    salary = job.get("salary", "")
    description = job.get("description", "")
    job_text = _normalize(f"{title} {company} {location} {experience} {salary} {description}")
    resume_norm = _normalize(resume_text)
    base_keywords = _extract_keywords(keywords_raw)
    settings_keywords = _settings_keywords(job.get("settings"))
    jd_keywords = extract_meaningful_keywords(f"{title} {description}")
    overlap = _overlap_score(job_text, resume_norm)
    control_blob = _normalize(" ".join(base_keywords + settings_keywords))
    matched = [kw for kw in jd_keywords if kw in resume_norm or kw in control_blob]
    keyword_part = (len(matched) / len(jd_keywords) * 100.0) if jd_keywords else 0.0
    score = round((0.55 * overlap) + (0.45 * keyword_part), 2)
    return {"score": score, "matched_keywords": matched, "extracted_keywords": jd_keywords}
