from sentence_transformers import SentenceTransformer

model = None


def get_model():

    global model

    if model is None:
        model = SentenceTransformer("all-MiniLM-L6-v2")

    return model


def generate_embedding(text):

    model = get_model()

    embedding = model.encode(text)

    return embedding