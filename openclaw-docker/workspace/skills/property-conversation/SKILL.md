---
name: property-conversation
description: Multi-turn home search. Use for every message about finding homes for sale, including short follow-up answers like a city, a budget, "condo", "more" or "start over".
---

# Property Conversation (Week 4)

Use this skill for finding homes for sale, and for every follow-up message in that search
(answers like "Irvine", "under $1.2M", "single family with 3 beds", "with a pool", "more",
"start over"). Prefer it over `property-search` for finding listings; use `property-search`
only for sold comps.

1. Use the `exec` tool to run, with the user's exact message in single quotes:

```bash
   cd /home/node/projects/idx && node converse.mjs main '<the user message>'
```

   Always use the session name `main`. If the message contains a single quote ('), replace
   it with a space first.

2. Reply with the script's output: the text after "Agent:" and any property cards, exactly as
   printed. Do not answer the question yourself, invent listings, or skip the follow-up
   question the script asks.
