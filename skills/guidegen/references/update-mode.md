# /guidegen --update

Re-uses `guidegen-out/manual.yaml`, keeps every developer edit, and re-captures only what changed.

1. Skip phase 0: never ask the brief question in update mode. Read `guidegen-out/brief.md` if it exists and keep
   following it. Phases 1-3 as usual (doctor, config exists, app start). Answers saved earlier mean no questions.
2. `guidegen changed --json` gives `screens` (source changed, never captured, or unreachable), `tasks` (use a
   changed screen or are not captured) and `only` (all their ids).
3. **Re-inventory** with the recipes: add screens that are new in the code (new ids only). Screens whose files were
   deleted: set nothing yourself. Report them in the summary and let the developer `exclude` or remove them.
4. **Re-explore** only new screens and the screens in `changed.screens`, then verify the tasks in `changed.tasks` live. Merge.
5. `guidegen capture --only <id> ...` for everything in `only` plus new ids. If nothing changed, skip capture.
6. **Re-write** text only for new or changed items. Leave `override`, `exclude` and `locked` untouched (merge enforces this).
7. Render and report as usual.

`--only <id>` from the developer narrows steps 4-5 to those ids. An interrupted run resumes the same way,
because statuses and images already in `guidegen-out/` are reused.
