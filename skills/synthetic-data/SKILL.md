---
name: synthetic-data
description: Interactively generate realistic synthetic test queries for an LLM product. Works with the user to find failure-driven dimensions, hand-write tuples, scale them up, and turn them into natural-language queries ready to run through the real system. Includes an optional browser review app.
---

# Synthetic Data Skill

You are running an interactive session to generate synthetic test queries for an LLM application (a chatbot, an agent, a RAG system, a writing assistant, and so on). The queries will be run through the real system so the user can review the traces with error analysis (see the `error-discovery` skill).

This skill is meant for interactive sessions only. Never invent the dimensions on your own and run ahead: the user knows the product, you structure the work.

The method follows Hamel Husain and Shreya Shankar's guide, "What is the best approach for generating synthetic data?":
https://hamel.dev/blog/posts/evals-faq/what-is-the-best-approach-for-generating-synthetic-data.html

## Core ideas to explain to the user (in plain words, once, at the start)

- A **dimension** is one way user requests differ from each other, chosen because you suspect the system may fail along it. Example for a support bot: Issue Type, Customer Mood, Prior Context.
- A **tuple** is one combination with one value per dimension, e.g. `(refund, angry, second contact)`. It is the recipe for one test query, not the query itself.
- We generate tuples first (for coverage), then turn each tuple into a natural-language query in a separate step (for realism). Asking an LLM directly for "test queries" gives generic, repetitive, easy questions that find nothing.

## Who does what

- **Chat** is for thinking: hypotheses, dimensions, deciding methods. Discuss these with the user in conversation.
- **The review app** (optional, in `app/`) is for bulk review: approving tuples, checking coverage, judging whether queries sound real. Offer it at the start of Phase 3: "Want to review tuples and queries in the browser? It's easier than typing approvals." If the user declines, do the same reviews in chat.

## Progress updates

Before each phase, say in one line what you are about to do and why. After each phase, say what was produced and what comes next. Never go silent for long stretches.

## Data files

Everything lives in a `synthetic_data/` folder in the user's project. Use JSON (the review app reads these files directly):

- `dimensions.json`
  ```json
  {"product": "Support agent for an online store",
   "hypotheses": [{"id": "H1", "text": "Gives wrong policy answers for out-of-policy requests"}],
   "dimensions": [{"name": "mood", "tests": ["H2"], "values": ["calm", "confused", "angry"]}]}
  ```
- `tuples.json`: a list of
  `{"id": "t01", "values": {"mood": "angry", ...}, "note": "why it's interesting", "hypotheses": ["H1"], "source": "agent|human|cross-product", "status": "pending|approved|rejected"}`
- `queries.json`: a list of
  `{"id": "q001", "tuple_id": "t01", "query": "...", "status": "real|fake" (set by the reviewer), "note": "reviewer note"}`
- `queries.jsonl`: final export, one approved query per line (written by the app's Export button, or by you).
- `fix_first.md`: prompt problems to fix before testing (if any).

**Rule when you update `tuples.json` or `queries.json`:** read the current file first and keep every existing item's `status`, `note`, `values` and `source` as the reviewer left them. Only add new items, or replace items the reviewer rejected or marked fake. Never reset the reviewer's decisions.

## Running the review app

```bash
python <this-skill-folder>/app/server.py --data synthetic_data --port 8765
```

Then tell the user to open http://localhost:8765. The app has four tabs: Dimensions (read-only view of the hypotheses and dimensions), Tuples (approve, reject, change values, with a coverage chart per dimension), Queries (sounds real / sounds fake + a note), and Export. It needs only the Python standard library. It polls the files, so anything you write shows up in the page within a few seconds.

Run it in the background. When the user says they're done reviewing, read the JSON files to see their decisions. If the session can't keep a server running, give the user the command to run it themselves.

## Phase 1: Understand the product

Goal: enough context to form failure hypotheses.

1. Ask the user for whatever exists, and read it: the system prompt, tool definitions, product docs or policies, a few real conversations or traces if any, and known complaints or bugs.
2. Ask, briefly (at most 3 questions at a time):
   - Who are the users, and what do they come to do?
   - What would be a costly or embarrassing failure?
   - Is anything already known to go wrong?
3. Summarize back in 5 lines or fewer: what the product does, who uses it, and the top worries. Ask the user to correct it.

If the user has no intuition yet, suggest they (or a colleague) use the application for 10 minutes and come back with notes. Do not skip this.

## Phase 2: Propose dimensions from failure hypotheses

1. Write a short list of **failure hypotheses**, each one sentence. Aim for 4 to 8.
2. Derive **3 to 4 dimensions** from them. For each: its name, 3 to 6 values, and the hypotheses it tests.
3. Show them as a table in chat and ask the user to accept, edit, merge, add or remove. Iterate until the user approves.

Rules:
- Every dimension must trace back to a hypothesis. Drop dimensions that are only "nice variety".
- Keep values concrete and mutually distinct. "Angry" and "frustrated" are the same value; merge them.
- Prefer few dimensions with meaningful values. 3 to 4 is usually right.

Save `dimensions.json`. If the app is running, the Dimensions tab now shows them.

## Phase 3: Hand-write about 20 tuples together

This phase teaches the user the problem space. Do not generate all 20 at once.

1. Propose 5 tuples, each with a one-line note on why it is interesting (which hypothesis it stresses). Write them to `tuples.json` with `status: "pending"` and ask the user to approve, reject or edit each one (in the app's Tuples tab or in chat).
2. Ask the user to write at least 2 tuples themselves (in chat; you add them with `source: "human"`).
3. Repeat until about 20 approved tuples exist. Use the coverage chart (or count yourself) so that every value of every dimension appears at least once. Include a few deliberately hard or edge combinations.

## Phase 4: Fix obvious problems first

Review the approved tuples against the system prompt and docs. If a tuple will obviously fail because the prompt never covers that situation (for example, the prompt never mentions the refund policy), tell the user: fix the prompt instead of generating more test queries for it. Save these to `fix_first.md` and let the user decide.

## Phase 5: Scale up the tuples

Explain the two methods and recommend one:

- **Cross product then filter.** Generate every combination, then filter out invalid or nonsensical ones with an LLM pass (show the user what was removed). Guarantees coverage, including edge cases. Best when most combinations are valid:
  ```bash
  python <this-skill-folder>/scripts/cross_product.py synthetic_data/dimensions.json synthetic_data/tuples_generated.json --sample 100
  ```
  Then filter, and merge the survivors into `tuples.json` (keep existing items and their reviews).
- **Direct LLM generation.** Ask the LLM for new tuples, giving the dimensions and the approved seed tuples as examples. More realistic combinations, but drifts toward generic ones and misses rare scenarios. Use when many combinations are invalid.

Ask how many queries the user wants. Default target: about 100, a good pool for error analysis. Ask the user to skim the new tuples (Tuples tab, filter "pending") and reject any that make no sense.

## Phase 6: Turn tuples into natural-language queries

Use a **separate prompt** from tuple generation, one tuple at a time or in small batches. In that prompt:

- Give the product context and the tuple.
- Ask for a message a real user would actually send: their vocabulary, typos and length, not a polished test question.
- Vary phrasing; do not reuse openings ("Hi, I would like to...").
- For multi-turn products, you may produce a short opening turn plus one follow-up.

Example: the tuple `(Vegan, Italian, Multi-step)` becomes "I need a dairy-free lasagna recipe that I can prep the day before."

Skip rejected tuples. Write `queries.json`. Ask the user to review them (Queries tab: sounds real / sounds fake, with an optional note). Then regenerate every query marked fake, using the reviewer's note, and replace it in place (same `id`, cleared `status`). Repeat until the user is satisfied.

## Phase 7: Hand off

1. Export: the user clicks Export in the app, or you write `queries.jsonl` yourself (approved queries only, one JSON object per line with `id`, `tuple`, `query`, `hypotheses`).
2. Explain how to run `queries.jsonl` through the **real system** (not a mock) and capture full traces. If you have access to the system or an API endpoint, offer to write the runner script; otherwise give clear instructions.
3. Point to the next step: review the traces with the `error-discovery` skill. Annotate at least 30 traces yourself before trusting agent suggestions.
4. End with these honest limits, in your own words:
   - Synthetic data cannot show how common a failure is in production. Only real traffic can.
   - It can miss details that matter in specialized domains, low-resource languages, high-stakes settings and underrepresented user groups.
   - Compare synthetic examples with real data as soon as real data is available, and replace them over time.

If the session ends early (a non-interactive run), save whatever exists, stop any server you started, say which phase was reached, and never claim later phases ran.
