---
name: property-search
description: Searches active California MLS listings from a plain-English request, or shows recent sold comps for a city. Returns formatted property cards.
---

# Property Search (Week 3)

Use this skill when the user wants to find homes for sale, or asks what homes sold for in a city.

## Find active listings
Use the `exec` tool to run, with the user's request in single quotes:

```bash
cd /home/node/projects/idx && node search.mjs listings '<the user request>' <page>
```

- `<page>` is 1 for a new search. If the user asks for "more" or "next", run the same request with the next page number.
- If the request contains a single quote ('), replace it with a space first.

## Show sold comps
```bash
cd /home/node/projects/idx && node search.mjs comps '<City>' <months>
```
- Use the city name exactly (for example 'Irvine', 'Newport Beach'). `<months>` defaults to 12.

## How to reply
- Show the property cards exactly as printed. Do not invent, change or add listings, prices or details.
- If the output says no listings match, say so and suggest loosening one filter (price, beds or type).
- Never run any other database command. This skill is read-only.
