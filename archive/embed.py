from sentence_transformers import SentenceTransformer

_model = None

def embed(texts):
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model.encode(texts, normalize_embeddings=True).astype("float32")