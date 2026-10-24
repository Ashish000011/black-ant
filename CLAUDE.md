# Instructions for Claude Code

1. **Read `CONTEXT.md` before anything else.** It holds what the project is, what is done, what is in progress,
   the decisions made and the important past prompts. Use it instead of relying on earlier chat history.
2. **Update `CONTEXT.md` for notable changes only** (a feature, a result, a decision, an important prompt), in the
   same PR as the change: the sections it touches and one dated line in its Log. Small fixes do not need an entry,
   so PRs do not all collide on this file. Keep machine-specific setup (local paths, accounts) out of it.
3. Follow the team's rules in `README.md` ("How we work"): numbers live in `config.yaml`, numbers on slides come
   from `results/`, nobody pushes to `main`.
4. The enablers (E1 to E3) are frozen: anything new must fit inside their stated bounds.
