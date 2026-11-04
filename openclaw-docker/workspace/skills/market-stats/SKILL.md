---
name: market-stats
description: Answers California housing market questions for a city (prices, price per sq ft, days on market, list-to-close ratio, monthly trend) from sold-home data.
---

# Market Stats (Week 5)

Use this skill for market questions about a city, for example "Is now a good time to buy in
San Diego?", "What's the average price per sq ft in Pasadena?", or "Are Irvine prices rising?".

1. Use the `exec` tool to run both commands for the city (exact city name, single quotes):

   ```bash
   cd /home/node/projects/idx && python3 market_stats.py summary '<City>'
   cd /home/node/projects/idx && python3 market_stats.py trend '<City>'
   ```

   For "which cities are busiest", run `python3 market_stats.py top` instead.

2. Answer the question in 2-4 sentences using only these numbers, then show the key figures:
   median price, days on market, list-to-close ratio, and the trend.
   Mention that the sold data covers March-September 2026.
   Do not invent numbers. This is market data, not financial advice.
