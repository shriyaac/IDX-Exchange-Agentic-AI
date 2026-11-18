---
name: rag
description: Answer real-estate knowledge questions (terms like DOM or list-to-close ratio, what a database column means, which columns a table has, Week 5 market summary facts) from the indexed IDX documents. Not for searching listings or computing new stats.
---

# RAG knowledge answers (Week 8)

Use this when the user asks what something means or how the data works, for example:
"What does DOM mean?", "What columns are in california_sold?", "What is a list-to-close ratio?",
"Which field holds bedrooms in rets_property?"

Do NOT use it for finding homes (use property-search), market numbers for a city
(use market-stats) or "homes like this" (use recommendations).

## How to run

    cd /home/node/projects/idx && python3 rag.py ask '<the user question>'

It prints an answer, then a "Sources:" line.

## How to reply

- Give the answer in plain words, then add "Source: <document names>".
- If the output says it doesn't know, or shows only passages, say the documents
  don't cover it clearly and give the most relevant passage briefly. Do not make up an answer.
- The documents are indexed already. Only if it says "The index is empty", run
  "python3 rag.py index" first (it takes a few minutes).
