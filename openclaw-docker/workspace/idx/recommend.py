# Week 7: recommendation engine (handbook: "Hybrid Scoring Model" + "Comp Validation").
#   python3 recommend.py <MLS#>        e.g. python3 recommend.py 1176489384
# Given a listing the user likes, scores every other active listing in the same city
# (60% structured similarity + 40% semantic similarity from the Week 6 embeddings),
# shows the top 5, and checks each one's price against recent sold comps.
#
# Changes from the handbook:
#   - skips points for missing values (some listings have no beds or sq ft) instead of crashing
#   - comp check skips typo future dates and handles cities/sizes with no comps (no divide-by-zero)
#   - no Gemini requests: the embeddings are already saved from Week 6
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from embed_listings import engine, store_path

LISTING_COLUMNS = """L_ListingID, L_DisplayId, L_Address, L_City, L_Zip, L_SystemPrice,
                     L_Keyword2, LM_Dec_3, LM_Int2_3, L_Type_, PhotoCount"""


def present(x) -> bool:
    return x is not None and not pd.isna(x)


# Handbook: calculate_similarity_score()
def calculate_similarity_score(target, candidate, target_emb, candidate_emb):
    score = 0.0

    # Structured similarity (60% of total score)
    if present(target["L_SystemPrice"]) and present(candidate["L_SystemPrice"]):
        price_diff = abs(target["L_SystemPrice"] - candidate["L_SystemPrice"])
        if price_diff < 50_000:    score += 20
        elif price_diff < 150_000: score += 12
        elif price_diff < 300_000: score += 5

    if present(target["L_Keyword2"]) and target["L_Keyword2"] == candidate["L_Keyword2"]: score += 15
    if target["L_City"] == candidate["L_City"]:                                          score += 15

    if present(target["LM_Int2_3"]) and present(candidate["LM_Int2_3"]):
        sqft_diff = abs(target["LM_Int2_3"] - candidate["LM_Int2_3"])
        if sqft_diff < 300:   score += 10
        elif sqft_diff < 700: score += 5

    structured = score

    # Semantic similarity (40% of total score)
    sem_sim = cosine_similarity(
        np.array(target_emb).reshape(1, -1),
        np.array(candidate_emb).reshape(1, -1)
    )[0][0]
    score += sem_sim * 40

    return round(score, 2), structured, round(float(sem_sim) * 40, 2)


# Handbook: validate_with_comps()
def validate_with_comps(city, sqft, price):
    """Is this list price supported by recent sales of similar-size homes in the same city?"""
    if not (present(sqft) and sqft > 0 and present(price)):
        return None
    sql = """
        SELECT
          AVG(ClosePrice / NULLIF(LivingArea,0)) AS avg_ppsf,
          COUNT(*) AS comp_count
        FROM california_sold
        WHERE City = %s AND PropertyType = 'Residential'
          AND LivingArea BETWEEN %s AND %s
          AND CloseDate >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
          AND CloseDate <= CURDATE()
    """
    result = pd.read_sql(sql, engine, params=(city, float(sqft) * 0.8, float(sqft) * 1.2)).iloc[0]
    if not result["comp_count"] or not present(result["avg_ppsf"]):
        return {"comp_count": 0}
    comp_price = float(result["avg_ppsf"]) * float(sqft)
    return {
        "comp_price": round(comp_price),
        "list_price": int(price),
        "comp_count": int(result["comp_count"]),
        "delta_pct": round((float(price) - comp_price) / comp_price * 100, 1),
    }


def num(x) -> str:
    if not present(x):
        return "?"
    return f"{x:,.0f}" if float(x).is_integer() else f"{x:g}"


def card(l) -> str:
    address = l["L_Address"] if present(l["L_Address"]) else "(address not listed)"
    price = f"${l['L_SystemPrice']:,.0f}" if present(l["L_SystemPrice"]) else "?"
    return (f"{address}, {l['L_City']} {l['L_Zip'] if present(l['L_Zip']) else ''}".rstrip() + "\n"
            f"   {price} | {num(l['L_Keyword2'])} bd / {num(l['LM_Dec_3'])} ba | {num(l['LM_Int2_3'])} sq ft | "
            f"{num(l['PhotoCount'])} photos | MLS# {l['L_DisplayId']}")


def comp_line(c) -> str:
    if c is None:
        return "   Price check: not enough details (missing sq ft or price)"
    if c["comp_count"] == 0:
        return "   Price check: no similar-size sales in the last 6 months"
    word = "above" if c["delta_pct"] > 0 else "below"
    verdict = ("in line with comps" if abs(c["delta_pct"]) <= 5
               else f"priced {abs(c['delta_pct'])}% {word} comps")
    return (f"   Price check: {c['comp_count']} similar-size sales (last 6 months) suggest "
            f"${c['comp_price']:,} -> {verdict}")


def main(listing: str) -> None:
    target_rows = pd.read_sql(
        f"SELECT {LISTING_COLUMNS} FROM rets_property WHERE L_DisplayId = %s OR L_ListingID = %s LIMIT 1",
        engine, params=(listing, listing),
    )
    if target_rows.empty:
        print(f"No listing found with MLS# {listing}.")
        return
    target = target_rows.iloc[0]
    city = target["L_City"]

    path = store_path(city)
    if not os.path.exists(path):
        print(f"No embeddings for {city} yet, so recommendations aren't available there. "
              f"Run: python3 embed_listings.py '{city}'")
        return
    saved = np.load(path)
    embeddings = dict(zip(saved["ids"], saved["vectors"]))
    target_id = str(target["L_ListingID"])
    if target_id not in embeddings:
        print(f"MLS# {listing} has no embedding yet. Run: python3 embed_listings.py '{city}'")
        return

    candidates = pd.read_sql(
        f"SELECT {LISTING_COLUMNS} FROM rets_property WHERE L_City = %s AND L_Status = 'Active'",
        engine, params=(city,),
    ).drop_duplicates("L_ListingID")
    candidates = candidates[candidates["L_ListingID"].astype(str) != target_id]

    scored = []
    for _, cand in candidates.iterrows():
        cid = str(cand["L_ListingID"])
        if cid not in embeddings:
            continue
        total, structured, semantic = calculate_similarity_score(
            target, cand, embeddings[target_id], embeddings[cid])
        scored.append((total, structured, semantic, cand))
    scored.sort(key=lambda x: x[0], reverse=True)

    print("You liked:")
    print("   " + card(target))
    print(comp_line(validate_with_comps(city, target["LM_Int2_3"], target["L_SystemPrice"])))
    print(f"\nTop 5 similar listings ({len(scored)} compared; score out of 100 = "
          f"structured out of 60 + semantic out of 40):\n")
    for rank, (total, structured, semantic, cand) in enumerate(scored[:5], 1):
        print(f"{rank}. {card(cand)}")
        print(f"   Score {total:.1f} (structured {structured:.0f}/60 + semantic {semantic:.1f}/40)")
        print(comp_line(validate_with_comps(city, cand["LM_Int2_3"], cand["L_SystemPrice"])) + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 recommend.py <MLS#>")
        sys.exit(1)
    main(sys.argv[1].strip())
