---
name: semantic-search
description: Finds the 5 active listings whose descriptions best match a free-text description of a home's style or feel (e.g. "charming craftsman with mountain views"). Currently covers Irvine.
---

# Semantic Search (Week 6)

Use this skill when the user describes the style, feel or features of a home in their own words,
for example "charming craftsman with mountain views and character" or "modern home with a pool
for entertaining", rather than exact filters like beds and price.

1. Use the `exec` tool to run, with the city and the user's description in single quotes:

   ```bash
   cd /home/node/projects/idx && python3 semantic_search.py '<City>' '<the user description>'
   ```

   Embeddings currently exist for Irvine only. If the user names another city and the script
   says there are no embeddings for it, tell them semantic search is only set up for Irvine so far.
   If no city is given, use 'Irvine'. Replace any single quote (') in the description with a space.

2. Show the 5 results exactly as printed (address, price, beds/baths, sq ft, photos, match score
   and description snippet). Do not invent or change listings.
