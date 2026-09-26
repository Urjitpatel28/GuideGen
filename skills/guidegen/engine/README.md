# guidegen-engine

The mechanics half of the GuideGen skill. Run it with uv from the repo that contains the skill:

```
uv run --project skills/guidegen/engine guidegen doctor --json
```

See `../SKILL.md` for how the agent orchestrates it and `../references/` for details.

Development:

```
cd skills/guidegen/engine
uv run pytest            # unit tests
uv run pytest -m e2e     # needs example apps + Playwright Chromium
```
