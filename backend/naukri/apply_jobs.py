import random
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from backend.automation.browser_manager import get_browser
from backend.automation.session_manager import load_session
from backend.config import DATABASE_PATHS
from backend.models.ext_jobs_model import upsert_ext_job
from backend.utils.activity_logger import log_activity
from backend.utils.db_migrations import ensure_applied_jobs_schema, ensure_standard_jobs_schema
from backend.utils.logger import log


EXTERNAL_BTN_PATTERN = re.compile(r"apply on company site|apply on company website", re.I)
APPLY_BTN_PATTERN = re.compile(r"easy apply|apply", re.I)


def _contains_any_text(page, selectors):
    for sel in selectors:
        try:
            if page.query_selector(sel):
                return True
        except Exception:
            continue
    return False


def _looks_like_applied(page):
    return _contains_any_text(
        page,
        [
            "text=Successfully applied",
            "text=Application submitted",
            "text=You have already applied",
            "text=Already Applied",
            "button:has-text('Applied')",
            "span:has-text('Applied')",
        ],
    )


def _looks_like_failure(page):
    return _contains_any_text(
        page,
        [
            "text=Something went wrong",
            "text=Try again",
            "text=Unable to apply",
            "text=Login to continue",
            "text=Session expired",
        ],
    )


def _is_naukri_url(url: str) -> bool:
    if not url:
        return True
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return True
    return "naukri.com" in host


def _safe_text(locator) -> str:
    try:
        return (locator.inner_text(timeout=1500) or "").strip()
    except Exception:
        return ""


def _safe_attr(locator, name: str) -> str:
    try:
        return (locator.get_attribute(name, timeout=1500) or "").strip()
    except Exception:
        return ""


def _capture_error_screenshot(page, user_id: int, job_title: str):
    try:
        safe_title = re.sub(r"[^a-zA-Z0-9_-]+", "_", (job_title or "job"))[:80]
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = Path(f"storage/logs/screenshots/user_{user_id}/{ts}_{safe_title}.png")
        path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(path), full_page=True)
        return str(path)
    except Exception:
        return ""


def _find_apply_control(page):
    # Prefer robust role-based selectors; fallback to text-based locator.
    candidates = [
        page.get_by_role("button", name=EXTERNAL_BTN_PATTERN),
        page.get_by_role("link", name=EXTERNAL_BTN_PATTERN),
        page.get_by_role("button", name=APPLY_BTN_PATTERN),
        page.get_by_role("link", name=APPLY_BTN_PATTERN),
        page.locator(
            "button:has-text('Apply on company site'), "
            "button:has-text('Apply on company website'), "
            "a:has-text('Apply on company site'), "
            "a:has-text('Apply on company website'), "
            "button:has-text('Easy Apply'), "
            "button:has-text('Apply'), "
            "a:has-text('Easy Apply'), "
            "a:has-text('Apply')"
        ),
    ]

    for loc in candidates:
        try:
            if loc.count() > 0:
                first = loc.first
                text = _safe_text(first).lower()
                href = _safe_attr(first, "href")
                is_external_btn = bool(EXTERNAL_BTN_PATTERN.search(text))
                return {
                    "locator": first,
                    "text": text,
                    "href": href,
                    "is_external_button": is_external_btn,
                }
        except Exception:
            continue
    return None


def _attempt_internal_submit(page) -> bool:
    submit_selectors = [
        "button:has-text('Submit application')",
        "button:has-text('Submit')",
        "button:has-text('Send Application')",
        "button:has-text('Apply')",
        "input[type='submit']",
    ]
    for sel in submit_selectors:
        try:
            btn = page.query_selector(sel)
            if not btn:
                continue
            btn.click(timeout=4000, force=True)
            page.wait_for_timeout(1500)
            return True
        except Exception:
            continue
    return False


def _click_apply_and_capture_external(page, context, locator):
    before_pages = len(context.pages)
    popup = None

    try:
        with page.expect_popup(timeout=4000) as popup_info:
            locator.click(timeout=8000, force=True)
        popup = popup_info.value
        popup.wait_for_load_state()
    except PlaywrightTimeoutError:
        popup = None

    try:
        page.wait_for_load_state("load", timeout=12000)
    except Exception:
        page.wait_for_timeout(2500)

    if popup is None and len(context.pages) > before_pages:
        popup = context.pages[-1]

    popup_url = ""
    if popup is not None:
        try:
            popup.wait_for_load_state("load", timeout=10000)
        except Exception:
            pass
        popup_url = popup.url or ""
        try:
            popup.close()
        except Exception:
            pass

    current_url = page.url or ""
    external_url = ""
    if popup_url and not _is_naukri_url(popup_url):
        external_url = popup_url
    elif current_url and not _is_naukri_url(current_url):
        external_url = current_url

    return {
        "external_url": external_url,
        "popup_url": popup_url,
        "current_url": current_url,
    }


def save_applied_job(user_id, job_title, company, location, experience, job_url):
    conn = sqlite3.connect(DATABASE_PATHS["applied"])
    ensure_applied_jobs_schema(conn)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO applied_jobs
        (user_id, job_title, company, location, experience, job_url, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, job_url) DO UPDATE SET
            job_title=excluded.job_title,
            company=excluded.company,
            location=excluded.location,
            experience=excluded.experience,
            status='applied',
            applied_at=CURRENT_TIMESTAMP
        """,
        (user_id, job_title, company, location, experience, job_url, "applied"),
    )
    conn.commit()
    conn.close()


def save_external_job(
    user_id,
    job_title,
    company,
    location,
    experience,
    resume_match_score,
    job_url,
    external_apply_url,
):
    upsert_ext_job(
        user_id=user_id,
        job_title=job_title,
        company=company,
        location=location,
        experience=experience,
        resume_match_score=resume_match_score,
        job_url=job_url,
        external_apply_url=external_apply_url,
    )


def save_job_status(user_id, job_title, company, location, job_url, status):
    conn = sqlite3.connect(DATABASE_PATHS["standard"])
    ensure_standard_jobs_schema(conn)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO standard_jobs
        (user_id, job_title, company, location, job_url, status)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, job_url) DO UPDATE SET
            job_title=excluded.job_title,
            company=excluded.company,
            location=excluded.location,
            status=excluded.status
        """,
        (user_id, job_title, company, location, job_url, status),
    )
    conn.commit()
    conn.close()


def apply_to_job(user_id, job_title, company, location, experience, job_url, job_id=None, resume_match_score=0.0):
    browser = get_browser()
    context = browser.new_context()
    page = context.new_page()

    try:
        load_session(context, user_id)

        log(f"Opening job for apply: {job_title}")
        page.goto("https://www.naukri.com", timeout=30000)
        page.wait_for_timeout(random.randint(1200, 2500))
        page.goto(job_url, timeout=35000)
        page.wait_for_timeout(random.randint(2000, 3500))

        apply_meta = _find_apply_control(page)
        button_type = "unknown"

        # Step 1: button text / type classification
        if apply_meta:
            button_type = "external" if apply_meta["is_external_button"] else "internal"

        if apply_meta and apply_meta["is_external_button"]:
            click_info = _click_apply_and_capture_external(page, context, apply_meta["locator"])
            external_url = click_info["external_url"]
            if not external_url:
                href = apply_meta.get("href") or ""
                if href and not _is_naukri_url(href):
                    external_url = href
            if not external_url:
                external_url = click_info["popup_url"] or click_info["current_url"] or (apply_meta.get("href") or "")
            save_external_job(
                user_id,
                job_title,
                company,
                location,
                experience,
                resume_match_score,
                job_url,
                external_url,
            )
            save_job_status(user_id, job_title, company, location, job_url, "external")
            log_activity("External Apply", f"{job_title} | external button", user_id=user_id)
            return {
                "status": "external",
                "external_apply_url": external_url,
                "apply_button_type": button_type,
                "job_id": job_id,
                "error_message": "",
            }

        if not apply_meta:
            if _looks_like_applied(page):
                save_applied_job(user_id, job_title, company, location, experience, job_url)
                save_job_status(user_id, job_title, company, location, job_url, "applied")
                log_activity("Job Applied", f"{job_title} | already applied", user_id=user_id)
                return {
                    "status": "applied",
                    "apply_button_type": "none",
                    "job_id": job_id,
                    "error_message": "",
                }

            save_job_status(user_id, job_title, company, location, job_url, "filtered_out")
            return {
                "status": "filtered_out",
                "reason": "apply_control_not_found",
                "apply_button_type": "none",
                "job_id": job_id,
                "error_message": "apply_control_not_found",
            }

        click_info = _click_apply_and_capture_external(page, context, apply_meta["locator"])
        external_url = click_info["external_url"]
        if not external_url:
            href = apply_meta.get("href") or ""
            if href and not _is_naukri_url(href):
                external_url = href

        if external_url:
            save_external_job(
                user_id,
                job_title,
                company,
                location,
                experience,
                resume_match_score,
                job_url,
                external_url,
            )
            save_job_status(user_id, job_title, company, location, job_url, "external")
            log_activity("External Apply", f"{job_title} | redirect: {external_url}", user_id=user_id)
            return {
                "status": "external",
                "external_apply_url": external_url,
                "apply_button_type": "external",
                "job_id": job_id,
                "error_message": "",
            }

        # Step 3: attempt internal submit when a form step is present.
        if not _looks_like_applied(page):
            _attempt_internal_submit(page)
            try:
                page.wait_for_timeout(1500)
            except Exception:
                pass

        if _looks_like_applied(page):
            save_applied_job(user_id, job_title, company, location, experience, job_url)
            save_job_status(user_id, job_title, company, location, job_url, "applied")
            log_activity("Job Applied", job_title, user_id=user_id)
            return {
                "status": "applied",
                "apply_button_type": button_type,
                "job_id": job_id,
                "error_message": "",
            }

        if _looks_like_failure(page):
            screenshot = _capture_error_screenshot(page, user_id, job_title)
            save_job_status(user_id, job_title, company, location, job_url, "failed")
            log_activity("Apply Failed", f"{job_title} | UI error | {screenshot}", user_id=user_id, level="error")
            return {
                "status": "failed",
                "reason": "ui_failure",
                "screenshot": screenshot,
                "apply_button_type": button_type,
                "job_id": job_id,
                "error_message": "ui_failure",
            }

        screenshot = _capture_error_screenshot(page, user_id, job_title)
        save_job_status(user_id, job_title, company, location, job_url, "failed")
        log_activity("Apply Failed", f"{job_title} | unconfirmed result | {screenshot}", user_id=user_id, level="error")
        return {
            "status": "failed",
            "reason": "unconfirmed_result",
            "screenshot": screenshot,
            "apply_button_type": button_type,
            "job_id": job_id,
            "error_message": "unconfirmed_result",
        }

    except Exception as exc:
        screenshot = _capture_error_screenshot(page, user_id, job_title)
        save_job_status(user_id, job_title, company, location, job_url, "failed")
        log_activity(
            "Apply Failed",
            f"{job_title} | exception: {str(exc)} | {screenshot}",
            user_id=user_id,
            level="error",
        )
        return {
            "status": "failed",
            "reason": "exception",
            "error": str(exc),
            "screenshot": screenshot,
            "apply_button_type": "unknown",
            "job_id": job_id,
            "error_message": str(exc),
        }
    finally:
        try:
            context.close()
        except Exception:
            pass
