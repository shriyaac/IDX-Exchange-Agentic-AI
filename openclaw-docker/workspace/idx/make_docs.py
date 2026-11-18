# Week 8: writes two text documents for the RAG index, straight from the database:
#   docs/schema_notes.txt            - every column in rets_property and california_sold
#                                      (the handbook's "schema reference" source)
#   docs/week5_market_summaries.txt  - Week 5 market summaries for several cities
#                                      (the handbook's "Week 5 market summaries" source)
#   python3 make_docs.py
import contextlib
import io
import os

import pandas as pd

from market_stats import engine, print_summary, TOP_CITIES_SQL, money

DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
CITIES = ["Irvine", "Pasadena", "Malibu", "Big Bear Lake", "Palm Springs", "San Diego", "Los Angeles"]


def schema_notes() -> str:
    cols = pd.read_sql(
        """SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE
           FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME IN ('rets_property', 'california_sold')
           ORDER BY TABLE_NAME, ORDINAL_POSITION""",
        engine,
    )
    parts = ["Schema notes for the IDX Exchange MLS database (database: idx_exchange).\n"]
    about = {
        "california_sold": "california_sold holds sold and closed residential transactions (the sold comps table). "
                           "Its column names follow the RESO / Trestle standard.",
        "rets_property": "rets_property holds active MLS listings (the live search table). Many search fields use "
                         "IDX legacy names: L_SystemPrice is the list price, L_Keyword2 is bedrooms, LM_Dec_3 is "
                         "bathrooms, LM_Int2_3 is square footage, L_City is the city, L_Type_ is the property type, "
                         "L_Remarks is the listing description. PoolPrivateYN and ViewYN store '1' for yes.",
    }
    for table, group in cols.groupby("TABLE_NAME"):
        names = ", ".join(group["COLUMN_NAME"])
        parts.append(f"{about.get(table, table)}\n"
                     f"The {table} table has {len(group)} columns: {names}.\n")
        for _, c in group.iterrows():
            parts.append(f"{table}.{c['COLUMN_NAME']} ({c['COLUMN_TYPE']})")
        parts.append("")
    parts.append("To join active listings to sold comps: CAST(rets_property.L_ListingID AS UNSIGNED) = "
                 "california_sold.ListingKey, or match on city and postal code for market-level analysis.")
    return "\n".join(parts)


def market_summaries() -> str:
    out = io.StringIO()
    out.write("Week 5 market summaries from california_sold (residential sales, last 12 months; "
              "the sold data covers March-September 2026).\n\n"
              "Definitions used: List-to-close ratio = ClosePrice / ListPrice, shown as a percent of asking "
              "price (also called the sale-to-list ratio); above 100% means homes sell over asking. "
              "Days on market (DOM) = days from listing to contract. Price per sqft = ClosePrice / LivingArea.\n\n")
    top = pd.read_sql(TOP_CITIES_SQL, engine)
    out.write("Top cities by number of sales:\n")
    for _, r in top.iterrows():
        out.write(f"{r['City']}: {r['sold_count']} sales, average price {money(r['avg_close_price'])}, "
                  f"{money(r['avg_price_per_sqft'])} per sqft, {r['avg_dom']} average days on market, "
                  f"list-to-close ratio {r['list_to_close_pct']}%.\n")
    for city in CITIES:
        out.write("\n")
        with contextlib.redirect_stdout(out):
            print_summary(city)
    return out.getvalue()


if __name__ == "__main__":
    os.makedirs(DOCS, exist_ok=True)
    for name, text in [("schema_notes.txt", schema_notes()),
                       ("week5_market_summaries.txt", market_summaries())]:
        with open(os.path.join(DOCS, name), "w") as f:
            f.write(text)
        print(f"Wrote docs/{name} ({len(text):,} characters)")
