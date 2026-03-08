import re
from typing import Optional, Tuple


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _extract_numbers(text: str) -> list[float]:
    return [float(n) for n in re.findall(r"\d+(?:\.\d+)?", text or "")]


def parse_years_range(text: str) -> Optional[Tuple[float, float]]:
    nums = _extract_numbers(text)
    if not nums:
        return None
    if len(nums) == 1:
        return nums[0], nums[0]
    lo, hi = sorted(nums[:2])
    return lo, hi


def parse_salary_range_lpa(text: str) -> Optional[Tuple[float, float]]:
    raw = (text or "").lower()
    nums = _extract_numbers(raw)
    if not nums:
        return None

    # Rough normalization: Cr -> 100 LPA; otherwise assume LPA-like values.
    if "cr" in raw:
        nums = [n * 100 for n in nums]

    if len(nums) == 1:
        return nums[0], nums[0]
    lo, hi = sorted(nums[:2])
    return lo, hi


def _overlaps(a: Tuple[float, float], b: Tuple[float, float]) -> bool:
    return max(a[0], b[0]) <= min(a[1], b[1])


def matches_job_role(job_title: str, desired_role: str) -> bool:
    role = _normalize(desired_role)
    if not role:
        return True
    title = _normalize(job_title)
    if role in title:
        return True

    role_tokens = [t for t in role.split() if len(t) > 2]
    if not role_tokens:
        return True
    return all(tok in title for tok in role_tokens)


def matches_location(job_location: str, preferred_location: str) -> bool:
    preferred = _normalize(preferred_location)
    if not preferred:
        return True

    location = _normalize(job_location)
    if not location:
        return False

    alias = {
        "bangalore": "bengaluru",
        "bengaluru": "bengaluru",
        "gurgaon": "gurugram",
        "gurugram": "gurugram",
        "bombay": "mumbai",
        "new delhi": "delhi",
    }

    preferred_parts = [p.strip() for p in re.split(r"[,/|]", preferred) if p.strip()]
    if not preferred_parts:
        preferred_parts = [preferred]

    normalized_location = location
    for src, dst in alias.items():
        normalized_location = normalized_location.replace(src, dst)

    for part in preferred_parts:
        norm_part = part
        for src, dst in alias.items():
            norm_part = norm_part.replace(src, dst)
        if norm_part in normalized_location:
            return True
    return False


def matches_experience(job_experience: str, user_experience: str) -> bool:
    user_exp = _normalize(user_experience)
    if not user_exp:
        return True

    user_range = parse_years_range(user_exp)
    job_range = parse_years_range(job_experience or "")
    if user_range is None:
        return True
    if job_range is None:
        # Naukri often omits experience in card snippets; don't drop solely for missing value.
        return True

    if user_range[0] == user_range[1]:
        years = user_range[0]
        return job_range[0] <= years <= job_range[1]
    return _overlaps(user_range, job_range)


def matches_salary(job_salary: str, salary_expectation: str) -> bool:
    expected = _normalize(salary_expectation)
    if not expected:
        return True

    expected_range = parse_salary_range_lpa(expected)
    job_range = parse_salary_range_lpa(job_salary or "")
    if expected_range is None:
        return True
    if job_range is None:
        # Salary is frequently "Not disclosed"; allow instead of dropping all jobs.
        return True
    return _overlaps(job_range, expected_range)


def matches_salary_strict(job_salary: str, salary_expectation: str) -> bool:
    expected = _normalize(salary_expectation)
    if not expected:
        return True
    expected_range = parse_salary_range_lpa(expected)
    job_range = parse_salary_range_lpa(job_salary or "")
    if expected_range is None:
        return True
    if job_range is None:
        return False
    return _overlaps(job_range, expected_range)


def evaluate_job_filters(job: dict, settings: dict) -> Tuple[bool, str]:
    scan_mode = (settings.get("scan_mode", "basic") or "basic").strip().lower()
    if scan_mode not in {"basic", "advance", "extreme"}:
        scan_mode = "basic"

    if not matches_job_role(job.get("title", ""), settings.get("job_role", "")):
        return False, "role_mismatch"
    if not matches_experience(job.get("experience", ""), settings.get("experience", "")):
        return False, "experience_mismatch"

    if scan_mode in {"basic", "extreme"} and not matches_location(job.get("location", ""), settings.get("preferred_location", "")):
        return False, "location_mismatch"
    salary_ok = matches_salary(job.get("salary", ""), settings.get("salary", ""))
    if scan_mode == "extreme":
        salary_ok = matches_salary_strict(job.get("salary", ""), settings.get("salary", ""))
    if scan_mode in {"basic", "advance", "extreme"} and not salary_ok:
        return False, "salary_mismatch"

    # Resume analyzer gating for advanced modes.
    if scan_mode in {"advance", "extreme"}:
        score = float(job.get("resume_match_score", 0) or 0)
        threshold = float(settings.get("resume_match_threshold", 5) or 5)
        if scan_mode == "advance":
            threshold = max(threshold, 10.0)
        if scan_mode == "extreme":
            threshold = max(threshold, 20.0)
        if score < threshold:
            return False, "resume_score_low"

    return True, "ok"
