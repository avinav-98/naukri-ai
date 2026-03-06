from pathlib import Path


ROLE_HINTS = [
    ("python developer", ["python developer", "python", "flask", "django"]),
    ("java developer", ["java developer", "spring boot", "java"]),
    ("qa engineer", ["qa engineer", "automation testing", "selenium", "test cases"]),
    ("project manager", ["project manager", "agile", "scrum", "stakeholder management"]),
    ("data scientist", ["data scientist", "nlp", "machine learning", "deep learning"]),
    ("machine learning engineer", ["machine learning engineer", "mlops", "tensorflow", "pytorch"]),
    ("data engineer", ["data engineer", "airflow", "spark", "etl", "data pipeline"]),
    ("business analyst", ["business analyst", "stakeholder", "requirement gathering"]),
    ("data analyst", ["data analyst", "sql", "power bi", "tableau", "excel"]),
    ("backend developer", ["backend developer", "fastapi", "django", "flask", "api development"]),
    ("frontend developer", ["frontend developer", "react", "javascript", "css", "html"]),
    ("full stack developer", ["full stack", "frontend", "backend", "node.js", "react"]),
    ("devops engineer", ["devops", "kubernetes", "docker", "terraform", "ci/cd"]),
    ("software engineer", ["software engineer", "software developer", "python", "java", "c++"]),
]


def load_resume_text(file_path: str):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError("Resume file not found")
    return path.read_text(encoding="utf-8")


def infer_search_query(resume_text: str) -> str:
    text = resume_text.lower()
    best_role = "data analyst"
    best_score = 0

    for role, hints in ROLE_HINTS:
        score = 0
        for hint in hints:
            if hint in text:
                score += 1
        if score > best_score:
            best_score = score
            best_role = role

    return best_role
