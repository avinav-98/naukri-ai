import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from backend.automation.browser_manager import get_browser
from backend.automation.session_manager import load_session
from backend.config import DATABASE_PATHS
from backend.models.settings_model import save_keyword_list
from backend.services.resume_analyzer_service import (
    extract_meaningful_keywords,
    resume_match_score_for_job,
)
from backend.utils.activity_logger import log_activity
from backend.utils.db_migrations import ensure_jobs_directory_schema
from backend.utils.job_deduplicator import job_exists
from backend.utils.job_filters import evaluate_job_filters


def _text_or_empty(node):
    return node.inner_text().strip() if node else ""


def _first_match(card, selectors: list[str]):
    for sel in selectors:
        node = card.query_selector(sel)
        if node:
            return node
    return None


def _norm(text: str) -> str:
    return (text or "").strip().lower()


def _posted_text_to_ts(posted_text: str) -> int:
    text = (posted_text or "").strip().lower()
    now = datetime.now(timezone.utc)
    try:
        if "just now" in text or "today" in text:
            return int(now.timestamp())
        if "yesterday" in text:
            return int((now - timedelta(days=1)).timestamp())
        if "hour" in text:
            n = int("".join(ch for ch in text if ch.isdigit()) or "1")
            return int((now - timedelta(hours=n)).timestamp())
        if "minute" in text:
            n = int("".join(ch for ch in text if ch.isdigit()) or "1")
            return int((now - timedelta(minutes=n)).timestamp())
        if "day" in text:
            n = int("".join(ch for ch in text if ch.isdigit()) or "1")
            return int((now - timedelta(days=n)).timestamp())
        if "week" in text:
            n = int("".join(ch for ch in text if ch.isdigit()) or "1")
            return int((now - timedelta(weeks=n)).timestamp())
        if "month" in text:
            n = int("".join(ch for ch in text if ch.isdigit()) or "1")
            return int((now - timedelta(days=n * 30)).timestamp())
    except Exception:
        pass
    return int(now.timestamp())


def _dedupe_jobs(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_url: dict[str, dict[str, Any]] = {}
    without_url: list[dict[str, Any]] = []

    for job in jobs:
        url = (job.get("url") or "").strip()
        if not url:
            without_url.append(job)
            continue
        old = by_url.get(url)
        if not old or int(job.get("posted_ts", 0)) >= int(old.get("posted_ts", 0)):
            by_url[url] = job

    merged = list(by_url.values()) + without_url
    by_company_role: dict[tuple[str, str, str], dict[str, Any]] = {}
    for job in merged:
        key = (
            _norm(job.get("title", "")),
            _norm(job.get("company", "")),
            _norm(job.get("location", "")),
        )
        old = by_company_role.get(key)
        if not old or int(job.get("posted_ts", 0)) >= int(old.get("posted_ts", 0)):
            by_company_role[key] = job
    return list(by_company_role.values())


def _dismiss_blocking_overlays(page):
    selectors = [
        "button:has-text('Got it')",
        "button:has-text('No Thanks')",
        "button:has-text('Close')",
        "span:has-text('Close')",
        "[aria-label='close']",
        ".crossIcon",
    ]
    for sel in selectors:
        try:
            node = page.query_selector(sel)
            if node:
                node.click(timeout=1500)
                page.wait_for_timeout(300)
        except Exception:
            continue


def _safe_click(page, selector: str) -> bool:
    try:
        page.click(selector, timeout=5000)
        return True
    except Exception:
        pass
    try:
        page.click(selector, timeout=5000, force=True)
        return True
    except Exception:
        pass
    try:
        node = page.query_selector(selector)
        if node:
            page.evaluate("(el) => el.click()", node)
            return True
    except Exception:
        pass
    return False


def _safe_fill(page, selector: str, value: str) -> bool:
    try:
        locator = page.locator(selector).first
        locator.fill(value, timeout=5000)
        return True
    except Exception:
        pass
    try:
        page.eval_on_selector(
            selector,
            """(el, val) => {
                el.value = val;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            }""",
            value,
        )
        return True
    except Exception:
        return False


def _go_to_search_results(page, search_query: str, settings: dict[str, Any] | None):
    role = ((settings or {}).get("job_role") or search_query or "").strip()
    location = ((settings or {}).get("preferred_location") or "").strip()
    experience = str(((settings or {}).get("experience") or "")).strip()

    page.goto("https://www.naukri.com")
    page.wait_for_timeout(2000)
    _dismiss_blocking_overlays(page)

    keyword_selector = "input[placeholder*='keyword'], input[placeholder*='designation'], input.suggestor-input"
    keyword_input = page.query_selector(keyword_selector)
    if keyword_input and role:
        _safe_fill(page, keyword_selector, role)

    if location:
        location_selector = "input[placeholder*='location'], input[placeholder*='Location'], input.suggestor-location"
        location_input = page.query_selector(location_selector)
        if location_input:
            _safe_fill(page, location_selector, location)

    if experience:
        try:
            exp_selector = "input[placeholder*='experience'], div:has-text('Select experience')"
            exp_trigger = page.query_selector(exp_selector)
            if exp_trigger:
                _safe_click(page, exp_selector)
                page.wait_for_timeout(500)
                option = page.query_selector(
                    f"li:has-text('{experience} year'), li:has-text('{experience} years'), div:has-text('{experience} year')"
                )
                if option:
                    option.click(timeout=3000, force=True)
        except Exception:
            pass

    searched = False
    if keyword_input and role:
        try:
            page.locator(keyword_selector).first.press("Enter", timeout=5000)
            searched = True
        except Exception:
            searched = False

    if not searched:
        searched = _safe_click(page, "button:has-text('Search')")

    if searched:
        page.wait_for_timeout(2500)
    elif role:
        slug = "-".join(role.strip().lower().split()) or "data-analyst"
        page.goto(f"https://www.naukri.com/{slug}-jobs")
        page.wait_for_timeout(2500)


def _extract_full_description(context, job_url: str) -> str:
    if not job_url:
        return ""
    detail = context.new_page()
    try:
        detail.goto(job_url, timeout=30000)
        detail.wait_for_timeout(1500)
        node = (
            detail.query_selector(".styles_JDC__dang-inner-html")
            or detail.query_selector(".job-desc")
            or detail.query_selector(".dang-inner-html")
            or detail.query_selector("section:has-text('Job description')")
        )
        return _text_or_empty(node)
    except Exception:
        return ""
    finally:
        detail.close()


def scrape_jobs(
    user_id=1,
    pages=3,
    search_query="data analyst",
    filter_settings=None,
    resume_text: str = "",
    keywords: str = "",
):
    browser = get_browser()
    context = browser.new_context()

    session_loaded = load_session(context, user_id)
    page = context.new_page()
    page.goto("https://www.naukri.com")
    page.wait_for_timeout(3000)

    login_btn = page.query_selector("a:has-text('Login')")
    if login_btn:
        context.close()
        if not session_loaded:
            raise RuntimeError("Naukri session not found. Use 'Link Naukri Profile' first.")
        raise RuntimeError("Naukri session expired. Re-link Naukri Profile and retry.")

    _go_to_search_results(page, search_query, filter_settings or {})
    jobs = []
    extracted_keywords_all: set[str] = set()
    filtered_out = 0

    for p in range(pages):
        print(f"Scraping page {p + 1}")
        page.wait_for_timeout(3000)

        cards = page.query_selector_all("div.srp-jobtuple-wrapper")
        for card in cards:
            title = _first_match(card, ["a.title", "a[title][class*='title']"])
            company = _first_match(card, ["a.comp-name", "a.subTitle", "span.comp-name", "a[title][class*='comp']"])
            location = _first_match(card, [".locWdth", ".loc-wrap", "span.locWdth"])
            experience = _first_match(card, [".expwdth", ".exp-wrap", "span.expwdth"])
            salary = _first_match(card, [".sal-wrap", ".salary", "span.sal-wrap"])
            description = _first_match(card, [".job-desc", ".job-description", ".jobTupleFooter", ".job-snippet"])
            posted_node = _first_match(card, [".job-post-day", ".job-post-daytime", ".jobTupleFooter .fleft", "span:has-text('ago')"])

            if not title:
                continue

            job_title = _text_or_empty(title)
            job_url = title.get_attribute("href")
            if not job_url:
                continue

            company_name = _text_or_empty(company)
            location_name = _text_or_empty(location)
            experience_text = _text_or_empty(experience)
            salary_text = _text_or_empty(salary)
            description_text = _text_or_empty(description)
            posted_text = _text_or_empty(posted_node)
            posted_ts = _posted_text_to_ts(posted_text)

            if len(description_text) < 40:
                description_text = _extract_full_description(context, job_url) or description_text

            if company_name.lower() == job_title.lower():
                alt_company = _first_match(card, ["a.subTitle", "a.comp-name", "span.comp-name"])
                company_name = _text_or_empty(alt_company)

            candidate = {
                "user_id": user_id,
                "title": job_title,
                "company": company_name,
                "location": location_name,
                "experience": experience_text,
                "salary": salary_text,
                "description": description_text,
                "posted_date_text": posted_text,
                "posted_ts": posted_ts,
                "url": job_url,
                "settings": filter_settings or {},
            }
            analyzer = resume_match_score_for_job(candidate, resume_text=resume_text, keywords_raw=keywords)
            candidate["resume_match_score"] = analyzer["score"]
            candidate["matched_keywords"] = analyzer["matched_keywords"]
            candidate["extracted_keywords"] = analyzer.get("extracted_keywords", [])
            if not candidate["extracted_keywords"]:
                candidate["extracted_keywords"] = extract_meaningful_keywords(
                    f"{job_title} {description_text}", limit=30
                )
            for kw in candidate["extracted_keywords"]:
                extracted_keywords_all.add(kw)

            matches, _reason = evaluate_job_filters(candidate, filter_settings or {})
            if not matches:
                filtered_out += 1
                continue

            if not job_exists(
                job_url,
                user_id=user_id,
                job_title=job_title,
                company=company_name,
                location=location_name,
            ):
                jobs.append(candidate)

        next_btn = page.query_selector("a[title='Next']")
        if next_btn:
            next_btn.click()
        else:
            break

    jobs = _dedupe_jobs(jobs)
    save_jobs(jobs)
    save_keyword_list(user_id=user_id, keywords=sorted(extracted_keywords_all))
    log_activity("Jobs Scraped", f"{len(jobs)} jobs added, {filtered_out} filtered out")
    context.close()
    return {"added_count": len(jobs), "filtered_out_count": filtered_out}


def save_jobs(jobs):
    conn = sqlite3.connect(DATABASE_PATHS["jobs"])
    ensure_jobs_directory_schema(conn)
    cursor = conn.cursor()

    for job in jobs:
        payload = (
            job.get("user_id", 1),
            job["title"],
            job["company"],
            job["location"],
            job.get("experience", ""),
            job.get("salary", ""),
            job.get("description", ""),
            float(job.get("resume_match_score", 0.0)),
            job.get("posted_date_text", ""),
            int(job.get("posted_ts", 0)),
            _norm(job["title"]),
            _norm(job["company"]) or _norm(job["url"]) or "unknown",
            _norm(job["location"]) or "unknown",
            job["url"],
        )

        cursor.execute(
            """
            INSERT INTO jobs_directory
            (user_id, job_title, company, location, experience, salary, job_description, resume_match_score,
             posted_date_text, posted_ts, normalized_title, normalized_company, normalized_location, job_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, job_url) DO UPDATE SET
                job_title = excluded.job_title,
                company = excluded.company,
                location = excluded.location,
                experience = excluded.experience,
                salary = excluded.salary,
                job_description = excluded.job_description,
                resume_match_score = excluded.resume_match_score,
                posted_date_text = excluded.posted_date_text,
                posted_ts = CASE
                    WHEN coalesce(excluded.posted_ts, 0) >= coalesce(jobs_directory.posted_ts, 0) THEN excluded.posted_ts
                    ELSE jobs_directory.posted_ts
                END,
                normalized_title = excluded.normalized_title,
                normalized_company = excluded.normalized_company,
                normalized_location = excluded.normalized_location,
                scraped_at = CURRENT_TIMESTAMP
            """,
            payload,
        )

        try:
            cursor.execute(
                """
                INSERT INTO jobs_directory
                (user_id, job_title, company, location, experience, salary, job_description, resume_match_score,
                 posted_date_text, posted_ts, normalized_title, normalized_company, normalized_location, job_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, normalized_title, normalized_company, normalized_location) DO UPDATE SET
                    job_title = excluded.job_title,
                    company = excluded.company,
                    location = excluded.location,
                    experience = excluded.experience,
                    salary = excluded.salary,
                    job_description = excluded.job_description,
                    resume_match_score = excluded.resume_match_score,
                    posted_date_text = CASE
                        WHEN coalesce(excluded.posted_ts, 0) >= coalesce(jobs_directory.posted_ts, 0) THEN excluded.posted_date_text
                        ELSE jobs_directory.posted_date_text
                    END,
                    posted_ts = CASE
                        WHEN coalesce(excluded.posted_ts, 0) >= coalesce(jobs_directory.posted_ts, 0) THEN excluded.posted_ts
                        ELSE jobs_directory.posted_ts
                    END,
                    job_url = CASE
                        WHEN coalesce(excluded.posted_ts, 0) >= coalesce(jobs_directory.posted_ts, 0) THEN excluded.job_url
                        ELSE jobs_directory.job_url
                    END,
                    normalized_title = excluded.normalized_title,
                    normalized_company = excluded.normalized_company,
                    normalized_location = excluded.normalized_location,
                    scraped_at = CURRENT_TIMESTAMP
                """,
                payload,
            )
        except sqlite3.IntegrityError:
            # Keep existing row when URL uniqueness conflicts with another latest record.
            pass

    conn.commit()
    conn.close()
