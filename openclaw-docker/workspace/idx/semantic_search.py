# Week 6: semantic property search (handbook: "Cosine Similarity Search").
#   python3 semantic_search.py 'Irvine' 'charming craftsman with mountain views'
# Turns the description into an embedding, compares it with every saved listing
# embedding for that city (cosine similarity), and prints the 5 closest listings.
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from embed_listings import engine, get_embeddings, store_path


def get_embedding(text: str) -> list[float]:
    return get_embeddings([text])[0]


def find_similar_listings(query, listing_embeddings, top_k=5):
    """Handbook's find_similar_listings(): return the top_k (listing_id, score) pairs."""
    query_vec = np.array(get_embedding(query)).reshape(1, -1)
    scores = []
    for listing_id, emb in listing_embeddings:
        sim = cosine_similarity(query_vec, np.array(emb).reshape(1, -1))[0][0]
        scores.append((listing_id, float(sim)))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]


def num(x) -> str:
    """Show 3.0 as 3, 2.5 as 2.5, and missing values as ?."""
    if pd.isna(x):
        return "?"
    return f"{x:,.0f}" if float(x).is_integer() else f"{x:g}"


def main(city: str, query: str) -> None:
    path = store_path(city)
    if not os.path.exists(path):
        print(f"No embeddings for '{city}' yet. Run: python3 embed_listings.py '{city}'")
        return
    saved = np.load(path)
    listing_embeddings = list(zip(saved["ids"], saved["vectors"]))
    top = find_similar_listings(query, listing_embeddings, top_k=5)

    ids = [lid for lid, _ in top]
    placeholders = ", ".join(["%s"] * len(ids))
    details = pd.read_sql(
        f"""SELECT L_ListingID, L_DisplayId, L_Address, L_City, L_Zip, L_SystemPrice,
                   L_Keyword2, LM_Dec_3, LM_Int2_3, L_Type_, PhotoCount, L_Remarks
            FROM rets_property WHERE L_ListingID IN ({placeholders})""",
        engine, params=tuple(ids),
    ).drop_duplicates("L_ListingID").set_index("L_ListingID")

    print(f"Top {len(top)} matches in {city} for: \"{query}\" ({len(listing_embeddings)} listings searched)\n")
    for rank, (lid, score) in enumerate(top, 1):
        if lid not in details.index:
            continue
        d = details.loc[lid]
        remarks = d["L_Remarks"].replace("\r", " ").replace("\n", " ") if pd.notna(d["L_Remarks"]) else ""
        snippet = remarks[:160] + ("..." if len(remarks) > 160 else "")
        price = f"${d['L_SystemPrice']:,.0f}" if pd.notna(d["L_SystemPrice"]) else "?"
        address = d["L_Address"] if pd.notna(d["L_Address"]) else "(address not listed)"
        zip_code = d["L_Zip"] if pd.notna(d["L_Zip"]) else ""
        print(f"{rank}. {address}, {d['L_City']} {zip_code}".rstrip())
        print(f"   {price} | {num(d['L_Keyword2'])} bd / {num(d['LM_Dec_3'])} ba | {num(d['LM_Int2_3'])} sq ft | "
              f"{num(d['PhotoCount'])} photos | MLS# {d['L_DisplayId']} | match {score:.2f}")
        print(f"   \"{snippet}\"\n" if snippet else "   (no description)\n")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 semantic_search.py '<City>' '<description>'")
        sys.exit(1)
    main(sys.argv[1], " ".join(sys.argv[2:]))
