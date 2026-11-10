---
name: synthetic-data
description: Interactively generate realistic synthetic test queries for an LLM product. Works with the user to find failure-driven dimensions, hand-write tuples, scale them up, and turn them into natural-language queries ready to run through the real system.
---

# Synthetic Data Skill

You are running an interactive session to generate synthetic test queries for an LLM application (a chatbot, an agent, a RAG system, a writing assistant, and so on). The queries will be run through the real system so the user can review the traces with error analysis (see the `error-discovery` skill).

This skill is meant for interactive sessions only. You never invent the dimensions on your own and run ahead: the user knows the product, you structure the work.

The method follows Hamel Husain and Shreya Shankar's guide, "What is the best approach for generating synthetic data?":
https://hamel.dev/blog/posts/evals-faq/what-is-the-best-approach-for-generating-synthetic-data.html

## Core ideas to explain to the user (in plain words, once, at the start)

- A **dimension** is one way user requests differ from each other, chosen because you suspect the system may fail along it. Example for a support bot: Issue Type, Customer Mood, Prior Context.
- A **tuple** is one combination with one value per dimension, e.g. `(refund, angry, second contact)`. It is the recipe for one test query, not the query itself.
- We generate tuples first (for coverage), then turn each tuple into a natural-language query in a separate step (for realism). Asking an LLM directly for "test queries" gives generic, repetitive, easy questions that find nothing.

## Progress updates

Before each phase, say in one line what you are about to do and why. After each phase, say what was produced and what comes next. Never go silent for long stretches.

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

1. Write a short list of **failure hypotheses**, each one sentence: "The bot may give wrong policy answers when the request is out of policy." Aim for 4 to 8.
2. Derive **3 to 4 dimensions** from them. For each dimension give:
   - its name,
   - 3 to 6 values,
   - the hypothesis it tests.
3. Show them as a table and ask the user to accept, edit, merge, add or remove. Iterate until the user approves.

Rules:
- Every dimension must trace back to a hypothesis. Drop dimensions that are only "nice variety".
- Keep values concrete and mutually distinct. "Angry" and "frustrated" are the same value; merge them.
- Prefer few dimensions with meaningful values over many dimensions. 3 to 4 is usually right.

Save to `synthetic_data/dimensions.yaml`:

```yaml
product: <one line>
hypotheses:
  - id: H1
    text: <one sentence>
dimensions:
  - name: customer_mood
    tests: [H2]
    values: [calm, confused, angry]
```

## Phase 3: Hand-write about 20 tuples together

This phase teaches the user the problem space. Do not generate all 20 at once.

1. Propose 5 tuples, each with a one-line note on why it is interesting (which hypothesis it stresses). Ask the user to approve, edit or reject each one.
2. Ask the user to write at least 2 tuples themselves.
3. Repeat until about 20 approved tuples exist. Make sure every value of every dimension appears at least once, and include a few deliberately hard or edge combinations.

Save to `synthetic_data/tuples_seed.csv` with one column per dimension plus `note` and `source` (`human` or `agent-approved`).

## Phase 4: Fix obvious problems first

Before scaling, review the tuples against the system prompt and docs. If a tuple will obviously fail because the prompt never covers that situation (for example, the prompt never mentions the refund policy), tell the user: fix the prompt instead of generating more test queries for it. List these as "fix first" items and let the user decide.

## Phase 5: Scale up the tuples

Explain the two methods and recommend one:

- **Cross product then filter.** Generate every combination of values, then filter out invalid or nonsensical ones with an LLM pass (show the user the rejected ones). Guarantees coverage, including edge cases. Best when most combinations are valid. Use `scripts/cross_product.py` for the product step.
- **Direct LLM generation.** Ask the LLM for new tuples, giving the dimensions and the seed tuples as examples. More realistic combinations, but drifts toward generic ones and misses rare scenarios. Use when many combinations are invalid.

Ask how many queries the user wants. Default target: about 100, which is a good pool for error analysis. If the cross product is much larger, sample it, stratified so every value is represented.

Show the user 10 random generated tuples for a sanity check before continuing.

Save to `synthetic_data/tuples.csv`.

## Phase 6: Turn tuples into natural-language queries

Use a **separate prompt** from tuple generation, one tuple at a time or in small batches. In that prompt:

- Give the product context and the tuple.
- Ask for a message a real user would actually send: their vocabulary, typos and length, not a polished test question.
- Vary phrasing; do not reuse openings ("Hi, I would like to...").
- For multi-turn products, you may produce a short opening turn plus one follow-up.

Example: the tuple `(Vegan, Italian, Multi-step)` becomes "I need a dairy-free lasagna recipe that I can prep the day before."

Show the user 10 generated queries next to their tuples. Ask whether they sound like real users. Adjust the prompt and regenerate if not.

Save to `synthetic_data/queries.jsonl`, one object per line:

```json
{"id": "q001", "tuple": {"customer_mood": "angry", "...": "..."}, "query": "...", "hypotheses": ["H2"]}
```

## Phase 7: Hand off

1. Explain how to run `queries.jsonl` through the **real system** (not a mock) and capture full traces. If you have access to the system or an API endpoint, offer to write the runner script; otherwise give clear instructions.
2. Point to the next step: review the traces with the `error-discovery` skill. Annotate at least 30 traces yourself before trusting agent suggestions.
3. End with these honest limits, in your own words:
   - Synthetic data cannot show how common a failure is in production. Only real traffic can.
   - It can miss details that matter in specialized domains, low-resource languages, high-stakes settings and underrepresented user groups.
   - Compare synthetic examples with real data as soon as real data is available, and replace them over time.

## Outputs

All files go in `synthetic_data/`:

- `dimensions.yaml`: hypotheses and dimensions
- `tuples_seed.csv`: about 20 hand-approved tuples
- `tuples.csv`: scaled tuples
- `queries.jsonl`: natural-language queries ready to run
- `fix_first.md`: problems to fix in the prompt before testing (if any)

If the session ends early (a non-interactive run), save whatever exists, say which phase was reached, and never claim later phases ran.
