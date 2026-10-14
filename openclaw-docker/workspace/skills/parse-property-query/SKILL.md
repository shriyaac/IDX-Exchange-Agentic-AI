---
name: parse-property-query
description: Turns a free-text home search (city, price, beds, baths, sq ft, type, pool, view) into a structured filter object for rets_property.
---

# Parse Property Query (Week 2)

Use this skill when the user describes homes they want to find, for example
"3-bedroom condos in Irvine under $1.5M with a pool".

1. Use the `exec` tool to run the parser with the user's exact words in single quotes:

```bash
   node /home/node/projects/idx/parse-query.mjs '<the user query>'
```

   If the query itself contains a single quote ('), replace it with a space first.

2. The script prints a JSON filter object. Reply with that JSON exactly as printed,
   followed by one short sentence listing the filters that were found.
   Do not add, guess or change any filter values yourself.

Filter fields: city, maxPrice, beds (minimum), baths (minimum), sqft (minimum),
type (Condominium, Townhouse or SingleFamilyResidence), pool ("1" = has a pool),
hasView ("1" = has a view). A null value means the user did not ask for it.
