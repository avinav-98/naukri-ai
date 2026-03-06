from backend.ai_engine.embedding_model import generate_embedding
from sklearn.metrics.pairwise import cosine_similarity


def calculate_match_score(resume_text, job_text):

    resume_vector = generate_embedding(resume_text)

    job_vector = generate_embedding(job_text)

    score = cosine_similarity(
        [resume_vector],
        [job_vector]
    )[0][0]

    return float(score)