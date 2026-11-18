# Week 8: Retrieval-Augmented Generation (handbook: "RAG Pipeline").
#   python3 rag.py index                        -> chunk + embed every file in docs/ (PDF or .txt)
#   python3 rag.py ask 'What does DOM mean?'    -> retrieve the 4 best chunks, answer from them only
#
# Same four steps as the handbook: chunk_text, index_documents, retrieve, rag_answer.
# Changes from the handbook:
#   - Gemini instead of OpenAI (same `openai` library, Gemini's OpenAI-compatible endpoint)
#   - reads PDFs as well as text files; the index is saved to a file and resumes like Week 6
#   - the answer lists which documents it came from, and says so when the context doesn't cover it
import hashlib
import json
import logging
import os
import re
import sys

import numpy as np
from openai import InternalServerError, RateLimitError
from pypdf import PdfReader
from sklearn.metrics.pairwise import cosine_similarity

from embed_listings import client, get_embeddings

logging.getLogger("pypdf").setLevel(logging.ERROR)   # hide harmless PDF-format warnings

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "docs")
INDEX = os.path.join(HERE, "embeddings", "rag_index")      # .npz (vectors) + .json (chunks)
CHAT_MODELS = ["gemini-3.8-flash", "gemini-3.6-flash"]     # main model, then backup


def load_documents() -> list[dict]:
    docs = []
    for name in sorted(os.listdir(DOCS)):
        path = os.path.join(DOCS, name)
        if name.lower().endswith(".pdf"):
            text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
        elif name.lower().endswith((".txt", ".md")):
            text = open(path, encoding="utf-8", errors="replace").read()
        else:
            continue
        text = re.sub(r"[ \t]+", " ", text)            # PDFs often put tabs between words
        text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
        docs.append({"title": name, "content": text})
    return docs


# 1. Chunk documents (handbook)
def chunk_text(text: str, chunk_size=600, overlap=100) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


# 2. Index chunks (handbook), in batches of 20 and saved as it goes
def index_documents(docs: list[dict]) -> None:
    wanted = [{"source": d["title"], "chunk": c} for d in docs for c in chunk_text(d["content"])]
    key = lambda item: hashlib.sha1((item["source"] + item["chunk"]).encode()).hexdigest()
    saved_items, saved_vecs = load_index()
    have = {key(it): v for it, v in zip(saved_items, saved_vecs)}
    items = [it for it in wanted if key(it) in have]           # keep only chunks that still exist
    vecs = [have[key(it)] for it in items]
    todo = [it for it in wanted if key(it) not in have]
    print(f"{len(docs)} documents, {len(wanted)} chunks: {len(items)} already indexed, {len(todo)} to go")
    os.makedirs(os.path.dirname(INDEX), exist_ok=True)
    for start in range(0, len(todo), 20):
        batch = todo[start:start + 20]
        embeddings = get_embeddings([it["chunk"] for it in batch])
        items += batch
        vecs += [np.array(e, dtype=np.float32) for e in embeddings]
        save_index(items, vecs)
        print(f"  indexed {len(items)}/{len(wanted)}")
    save_index(items, vecs)
    print("Done. Sources: " + ", ".join(d["title"] for d in docs))


def save_index(items, vecs) -> None:
    np.savez(INDEX + ".npz", vectors=np.vstack(vecs) if vecs else np.zeros((0, 1)))
    with open(INDEX + ".json", "w") as f:
        json.dump(items, f)


def load_index():
    if not os.path.exists(INDEX + ".json"):
        return [], []
    items = json.load(open(INDEX + ".json"))
    vecs = list(np.load(INDEX + ".npz")["vectors"]) if items else []
    return items, vecs


# 3. Retrieve relevant chunks for a query (handbook)
def retrieve(query: str, index: list[dict], top_k=4) -> list[dict]:
    q_emb = np.array(get_embeddings([query])[0]).reshape(1, -1)
    scored = [
        (doc, cosine_similarity(q_emb, np.array(doc["embedding"]).reshape(1, -1))[0][0])
        for doc in index
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in scored[:top_k]]


# 4. Generate grounded answer (handbook)
def rag_answer(query: str, index: list[dict]) -> tuple[str, list[dict]]:
    chunks = retrieve(query, index)
    context = "\n\n".join(f"[{c['source']}]\n{c['chunk']}" for c in chunks)
    prompt = (f"Answer using only the context below. If the context does not contain the answer, "
              f"say you don't know.\n\n{context}\n\nQuestion: {query}")
    for model in CHAT_MODELS:
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.choices[0].message.content, chunks
        except (RateLimitError, InternalServerError):
            print(f"  ({model} is busy or rate-limited, trying the next model)")
    return "(No chat model is free right now, so here are the best-matching passages from your documents:)\n\n" + context, chunks


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "index":
        index_documents(load_documents())
    elif mode == "ask" and len(sys.argv) > 2:
        items, vecs = load_index()
        if not items:
            print("The index is empty. Run: python3 rag.py index")
            sys.exit(1)
        index = [{**it, "embedding": v} for it, v in zip(items, vecs)]
        answer, used = rag_answer(" ".join(sys.argv[2:]), index)
        print(answer.strip())
        print("\nSources: " + ", ".join(sorted({c["source"] for c in used})))
    else:
        print("Usage: python3 rag.py index | python3 rag.py ask '<question>'")
