from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

sentences = [
    "How do peers share files without a central server?",
    "BitTorrent is a peer-to-peer file sharing protocol.",
    "The recipe calls for two cups of flour.",
]
vecs = model.encode(sentences, normalize_embeddings=True)
print("vector shape:", vecs.shape)

# cosine similarity (vectors are normalized, so a dot product is enough)
print("query vs BitTorrent:", float(vecs[0] @ vecs[1]))
print("query vs flour:     ", float(vecs[0] @ vecs[2]))