# Week 5: Market Statistics Agent, built on california_sold (sold comps).
# Based on the handbook's "SQL: City Market Summary" and "Python Trend Analysis".
#
#   python3 market_stats.py summary 'Irvine'    -> median/avg price, $/sq ft, days on market,
#                                                  list-to-close ratio, active vs. sold inventory
#   python3 market_stats.py trend 'Irvine'      -> month-by-month prices and % change
#   python3 market_stats.py top                 -> the handbook's top-25 cities summary
#
# Changes from the handbook (because of the real data):
#   - connection details come from the environment, not a password typed into the code
#   - skips 4 typo rows dated in the future (CloseDate <= CURDATE())
#   - adds median price (the deliverable asks for it) and active-vs-sold inventory
import os
import sys
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine

engine = create_engine(
    "mysql+mysqlconnector://{user}:{pw}@{host}/{db}".format(
        user=os.environ["MYSQL_USER"],
        pw=quote_plus(os.environ["MYSQL_PASSWORD"]),
        host=os.environ.get("MYSQL_HOST", "mysql"),
        db=os.environ.get("MYSQL_DATABASE", "idx_exchange"),
    )
)

# Handbook: SQL City Market Summary (top 25 cities by number of sales)
TOP_CITIES_SQL = """
    SELECT
      City,
      COUNT(*)                                              AS sold_count,
      ROUND(AVG(ClosePrice), 0)                             AS avg_close_price,
      ROUND(AVG(ClosePrice / NULLIF(LivingArea,0)),0)       AS avg_price_per_sqft,
      ROUND(AVG(DaysOnMarket), 1)                           AS avg_dom,
      ROUND(AVG(ClosePrice / NULLIF(ListPrice,0)) * 100, 1) AS list_to_close_pct
    FROM california_sold
    WHERE PropertyType = 'Residential'
      AND CloseDate >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
      AND CloseDate <= CURDATE()
      AND LivingArea > 0
    GROUP BY City
    ORDER BY sold_count DESC
    LIMIT 25
"""


def get_city_sales(city: str, months: int = 12) -> pd.DataFrame:
    """All residential sales in one city over the last `months` months."""
    query = """
        SELECT ClosePrice, ListPrice, LivingArea, DaysOnMarket
        FROM california_sold
        WHERE City = %s
          AND PropertyType = 'Residential'
          AND CloseDate >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
          AND CloseDate <= CURDATE()
    """
    return pd.read_sql(query, engine, params=(city, months))


def get_market_summary(city: str, months: int = 12) -> dict:
    """Median/average price, $/sq ft, days on market and list-to-close ratio for a city."""
    df = get_city_sales(city, months)
    if df.empty:
        return {"city": city, "sold_count": 0}
    ppsf = df["ClosePrice"] / df["LivingArea"].where(df["LivingArea"] > 0)
    ratio = df["ClosePrice"] / df["ListPrice"].where(df["ListPrice"] > 0)
    active = pd.read_sql(
        "SELECT COUNT(*) AS n FROM rets_property WHERE L_City = %s AND L_Status = 'Active'",
        engine, params=(city,),
    )["n"].iloc[0]
    return {
        "city": city,
        "months": months,
        "sold_count": int(len(df)),
        "median_close_price": round(df["ClosePrice"].median()),
        "avg_close_price": round(df["ClosePrice"].mean()),
        "median_price_per_sqft": round(ppsf.median()),
        "avg_dom": round(df["DaysOnMarket"].mean(), 1),
        "median_dom": round(df["DaysOnMarket"].median()),
        "list_to_close_pct": round(ratio.mean() * 100, 1),
        "active_listings": int(active),
    }


# Handbook: Python Trend Analysis (monthly price trends for a city)
def get_price_trend(city: str, months: int = 24) -> pd.DataFrame:
    query = """
        SELECT
            DATE_FORMAT(CloseDate, "%Y-%m") AS month,
            COUNT(*)                          AS sales,
            ROUND(AVG(ClosePrice), 0)         AS avg_price,
            ROUND(AVG(DaysOnMarket), 1)       AS avg_dom
        FROM california_sold
        WHERE City = %s
          AND PropertyType = "Residential"
          AND CloseDate >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
          AND CloseDate <= CURDATE()
        GROUP BY DATE_FORMAT(CloseDate, "%Y-%m")
        ORDER BY month
    """
    df = pd.read_sql(query, engine, params=(city, months))
    df["price_change_pct"] = (df["avg_price"].pct_change() * 100).round(1)
    return df


def market_read(s: dict) -> str:
    """A plain-English read of the numbers (rule of thumb, not advice)."""
    ratio, dom = s["list_to_close_pct"], s["avg_dom"]
    if ratio >= 100 and dom <= 30:
        return "Seller's market: homes sell at or above asking, and quickly."
    if ratio < 98 or dom > 60:
        return "Buyer's market: homes sell below asking or sit longer, so buyers have room to negotiate."
    return "Balanced market: homes sell close to asking."


def money(n) -> str:
    return f"${n:,.0f}"


def print_summary(city: str) -> None:
    s = get_market_summary(city)
    if s["sold_count"] == 0:
        print(f"No sales found for '{city}' in the last 12 months. Check the spelling (e.g. 'Irvine').")
        return
    print(f"Market summary: {city} (residential sales, last 12 months)")
    print(f"  Homes sold:            {s['sold_count']:,}")
    print(f"  Median sold price:     {money(s['median_close_price'])}")
    print(f"  Average sold price:    {money(s['avg_close_price'])}")
    print(f"  Median price per sqft: {money(s['median_price_per_sqft'])}")
    print(f"  Days on market:        {s['avg_dom']} average, {s['median_dom']} median")
    print(f"  List-to-close ratio:   {s['list_to_close_pct']}% of asking price")
    print(f"  Active listings now:   {s['active_listings']:,}")
    print(f"  Read: {market_read(s)}")
    print("  Note: sold data covers March-September 2026.")


def print_trend(city: str) -> None:
    df = get_price_trend(city)
    if df.empty:
        print(f"No sales found for '{city}'. Check the spelling (e.g. 'Irvine').")
        return
    print(f"Monthly trend: {city} (residential sales)")
    print(df.to_string(index=False, formatters={"avg_price": money}))
    first, last = df["avg_price"].iloc[0], df["avg_price"].iloc[-1]
    change = (last - first) / first * 100
    print(f"\n{df['month'].iloc[0]} to {df['month'].iloc[-1]}: average price "
          f"{'up' if change >= 0 else 'down'} {abs(change):.1f}% ({money(first)} -> {money(last)})")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    city = " ".join(sys.argv[2:]).strip()
    try:
        if mode == "summary" and city:
            print_summary(city)
        elif mode == "trend" and city:
            print_trend(city)
        elif mode == "top":
            top = pd.read_sql(TOP_CITIES_SQL, engine)
            print("Top cities by number of sales, last 12 months")
            print(top.to_string(index=False, formatters={"avg_close_price": money, "avg_price_per_sqft": money}))
        else:
            print("Usage: python3 market_stats.py summary '<City>' | trend '<City>' | top")
    except Exception as err:
        print(f"Market stats failed: {err}")
        sys.exit(1)
