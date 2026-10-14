---
name: current-time
description: Tells the user the current date and time (Pacific time). Use when asked what time or day it is.
---

# Current Time

Week 1 practice skill (the handbook's `getCurrentTime` example, written the OpenClaw way).

When the user asks for the current time or date:

1. Use the `exec` tool to run:

   ```bash
   TZ=America/Los_Angeles date "+%A, %B %d, %Y at %I:%M %p %Z"
   ```

2. Reply with one short sentence containing that result. Do not guess the time yourself.
