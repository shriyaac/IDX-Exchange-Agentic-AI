# Week 6: build embeddings for active listings (handbook: "Embedding Generation").
#   python3 embed_listings.py 'Irvine'          -> embeds every active Irvine listing
#   python3 embed_listings.py 'Irvine' 50       -> only the first 50 (quick test)
#
# Same approach as the handbook, with these changes:
#   - Gemini instead of OpenAI, through Gemini's OpenAI-compatible endpoint, so the
#     handbook's `from openai import OpenAI` code stays the same
#   - one city at a time and small batches, to stay inside the free-tier rate limits
#   - waits and retries automatically when rate-limited, and can resume where it stopped
#   - saved to embeddings/<city>.npz because the database login is read-only
import os
import re
import sys
import time

import numpy as np
import pandas as pd
from openai import OpenAI, RateLimitError
from sqlalchemy import create_engine
from urllib.parse import quote_plus

MODEL = "gemini-embedding-2"
BATCH = 20                       # listings per request

client = OpenAI(
    api_key=os.environ["GEMINI_API_KEY"],
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
engine = create_engine(
    "mysql+mysqlconnector://{user}:{pw}@{host}/{db}".format(
        user=os.environ["MYSQL_USER"], pw=quote_plus(os.environ["MYSQL_PASSWORD"]),
        host=os.environ.get("MYSQL_HOST", "mysql"), db=os.environ.get("MYSQL_DATABASE", "idx_exchange"),
    )
)
EMBED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "embeddings")


def store_path(city: str) -> str:
    return os.path.join(EMBED_DIR, re.sub(r"[^a-z0-9]+", "-", city.lower()).strip("-") + ".npz")


def get_embeddings(texts: list[str], model: str = MODEL) -> list[list[float]]:
    """Handbook's get_embedding(), but for a batch of texts in one request."""
    texts = [t.replace("\n", " ").strip()[:8000] for t in texts]   # max token safety
    for attempt in range(6):
        try:
            response = client.embeddings.create(model=model, input=texts)
            return [d.embedding for d in response.data]
        except RateLimitError:
            wait = 30 * (attempt + 1)
            print(f"  rate-limited, waiting {wait}s...")
            time.sleep(wait)
    raise RuntimeError("still rate-limited after several retries; run the same command again later")


def val(x, default="unknown"):
    """Missing database values (NULL) become 'unknown'; 3.0 becomes 3."""
    if x is None or pd.isna(x):
        return default
    return int(x) if isinstance(x, float) and x.is_integer() else x


def build_listing_text(row: dict) -> str:
    """Handbook's build_listing_embedding(): combine key fields into one description."""
    price = f"${val(row['L_SystemPrice'], 0):,}"
    return f"""
        {val(row["L_Type_"], "Home")} in {row["L_City"]}, CA.
        {val(row["L_Keyword2"])} beds, {val(row["LM_Dec_3"])} baths.
        {val(row["LM_Int2_3"])} sq ft. Built {val(row["YearBuilt"])}.
        Price: {price}.
        {val(row["L_Remarks"], "")}
    """.strip()


def main(city: str, limit: int | None = None) -> None:
    sql = """
        SELECT L_ListingID, L_Type_, L_City, L_Keyword2, LM_Dec_3, LM_Int2_3,
               YearBuilt, L_SystemPrice, L_Remarks
        FROM rets_property
        WHERE L_Status = 'Active' AND L_City = %s
        ORDER BY L_ListingID
    """
    rows = pd.read_sql(sql, engine, params=(city,)).drop_duplicates("L_ListingID")
    if limit:
        rows = rows.head(limit)
    if rows.empty:
        print(f"No active listings found for '{city}'. Check the spelling (e.g. 'Irvine').")
        return

    path = store_path(city)
    ids, vecs = [], []
    if os.path.exists(path):                       # resume: keep what's already embedded
        saved = np.load(path)
        ids, vecs = list(saved["ids"]), list(saved["vectors"])
    done = set(ids)
    todo = rows[~rows["L_ListingID"].astype(str).isin(done)]
    print(f"{city}: {len(rows)} listings, {len(done)} already embedded, {len(todo)} to go")

    os.makedirs(EMBED_DIR, exist_ok=True)
    records = todo.to_dict("records")
    for start in range(0, len(records), BATCH):
        batch = records[start:start + BATCH]
        embeddings = get_embeddings([build_listing_text(r) for r in batch])
        ids += [str(r["L_ListingID"]) for r in batch]
        vecs += [np.array(e, dtype=np.float32) for e in embeddings]
        np.savez(path, ids=np.array(ids), vectors=np.vstack(vecs))   # save after every batch
        print(f"  embedded {len(ids)}/{len(rows)}")
        time.sleep(2)                                                 # be gentle with free-tier limits
    print(f"Done: {len(ids)} listings saved to embeddings/{os.path.basename(path)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 embed_listings.py '<City>' [limit]")
        sys.exit(1)
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)
