---
name: recommendations
description: Recommends the 5 active listings most similar to a listing the user likes (by MLS number), with a price check against recent sold comps. Covers Irvine, Pasadena, Malibu, Big Bear Lake and Palm Springs.
---

# Recommendations (Week 7)

Use this skill when the user likes a specific listing and wants similar homes, for example
"show me homes like MLS# 1176489384", "more like the first one", or "what else is similar?".

1. Find the listing's MLS number. If the user refers to a listing from an earlier result
   ("the first one", "95 Duet"), use the MLS# shown in that result.

2. Use the `exec` tool to run:

   ```bash
   cd /home/node/projects/idx && python3 recommend.py <MLS#>
   ```

3. Show the output exactly as printed: the liked listing, the top 5 similar listings with
   their scores, and each price check. Do not invent listings, scores or prices.
   Price checks compare against recent similar-size sales in the same city; they are
   estimates, not appraisals.

Recommendations work for listings in Irvine, Pasadena, Malibu, Big Bear Lake and Palm Springs (the cities with saved embeddings).
If the script says there are no embeddings for a city, tell the user that.
