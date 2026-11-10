# Prompt: generate synthetic data with the `synthetic-data` skill

Copy the prompt below into Claude Code or Claude.ai in any project, fill in the parts in [brackets], and send it.

**Which review mode?** The review app runs on `localhost`, so it only opens in your browser when the agent runs on your own computer.
- **Claude Code on your machine** → keep the "app" line.
- **Claude.ai in the browser** (cloud session) → keep the "chat-only" line instead.

---

```
I want to generate synthetic test queries for my AI product using the
"synthetic-data" skill from https://github.com/mohcinemadkour/YouAIEvals
(folder skills/synthetic-data). It implements the method in
https://hamel.dev/blog/posts/evals-faq/what-is-the-best-approach-for-generating-synthetic-data.html

1. Get the skill: clone the repo (or run
   npx skills add https://github.com/mohcinemadkour/YouAIEvals --skill synthetic-data)
   and read skills/synthetic-data/SKILL.md before doing anything else.

2. Follow SKILL.md exactly, phase by phase, matching the guide's steps:
   - Define dimensions from failure hypotheses about my product.
   - Write about 20 tuples by hand, with me.
   - Fix obvious problems in my prompt first, instead of testing them.
   - Generate more tuples at scale (cross product then filter, or direct generation).
   - Turn each tuple into a natural-language query, in a separate prompt.
   - Hand off the queries to be run through my real system.
   It is interactive: stop and wait for my approval after the product
   summary, after the dimensions, and after each batch of tuples and queries.
   Never invent dimensions and run ahead without me.

3. Review mode (keep ONE line):
   - App: start skills/synthetic-data/app/server.py on my data folder
     and give me the URL to open.
   - Chat-only: do all the reviews in this conversation; don't start the app.

4. Save everything in a synthetic_data/ folder, and at the end give me
   queries.jsonl as a file I can download.

About my product:
- What it does: [e.g. customer support agent for an online store]
- Who uses it: [e.g. shoppers asking about orders, refunds, accounts]
- What worries me most: [e.g. wrong refund-policy answers, bad tone with angry customers]
- System prompt / tools / docs: [paste them, or attach the files]
- Real conversations, if any: [attach a few, or say "none yet"]

Target: about [100] queries.
[Optional: My system runs on [AWS Bedrock / an API at ...]. After export,
write a script that sends each query to it and saves the full traces,
so I can review them with the error-discovery skill.]
```

---

**Tips**
- The more context you give under "About my product", the better the dimensions in Phase 2. The system prompt matters most.
- Next step after this skill: run the queries through your real system, then review the traces with the `error-discovery` skill in this repo.
