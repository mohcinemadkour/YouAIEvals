# YouAIEvals

Course materials for practical AI evaluation by Mohcine Madkour (EvalTrust).

## Skills

| Skill | What it does |
|---|---|
| [`synthetic-data`](skills/synthetic-data/SKILL.md) | Interactively generates realistic synthetic test queries: finds failure-driven dimensions with you, hand-writes ~20 tuples, scales them up, and turns each into a natural-language query ready to run through your real system. Includes a browser review app (`app/`, Python standard library only) for approving tuples, checking coverage and judging queries. |
| [`error-discovery`](skills/error-discovery/SKILL.md) | Runs an interactive error-analysis session on a dataset of LLM outputs or traces: studies the data, builds a review app, picks diverse samples, and organizes failure modes with you in the loop. |

Ready-to-paste prompt for starting a synthetic-data session in any project: [`skills/synthetic-data/PROMPT.md`](skills/synthetic-data/PROMPT.md).

Use them in that order when you have no real users yet: generate queries with `synthetic-data`, run them through your system, then review the traces with `error-discovery`.

### Install

```bash
npx skills add https://github.com/mohcinemadkour/YouAIEvals --skill synthetic-data
npx skills add https://github.com/mohcinemadkour/YouAIEvals --skill error-discovery
```

Or copy the skill folders from `skills/` into your project's `.claude/skills/` folder.
