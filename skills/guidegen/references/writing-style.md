# Writing style (phase 8)

Readers are the product's **end users**: non-technical, busy, looking something up in the middle of a job.

If `guidegen-out/brief.md` exists, it comes first: its audience, tone, chapter order, preferred terms and banned words
override the defaults below. The rules against code, internal names and real data always apply.

## Rules

- Second person, imperative, present tense: "Click **Save**." / "Type the customer's name."
- **One action per step.** Start the step with the verb. Add the result when it helps: "Click **Save**. The order opens."
- UI labels in **bold**, spelled **exactly** as on screen (check the screenshot): **New order**, not "new order button".
- No code, no internal names, no file paths, no ids, no HTTP words, no "component", "modal", "route",
  "endpoint" or "view model". Say "window", "page", "tab", "box", "list", "button", "menu".
- Short sentences (aim for under 20 words). Plain words: "choose" not "select from the dropdown", "type" not "input".
- Name the place before the action when needed: "On the **Customers** tab, click **New customer**."
- Explain *why* only when it prevents a mistake: "Customers must exist before you can create orders for them."
- Warnings for irreversible actions: "This cannot be undone."
- Never include real personal data, secrets, or the values you typed during capture (the screenshot shows them already, redacted where needed).

## Fields to write

- `meta.title` ("<Product> User Manual"), `meta.intro` (1-2 sentences on what the product is for) and `meta.audience`
  (who reads it, for example "warehouse staff"; leave the default "end users" when you do not know).
- `chapters`: order and any custom text chapters from the brief (glossary, about this manual). Same writing rules.
- `gettingStarted`: `requirements` (bullets), `launch`, `signIn`, `tour`, `tourScreen`.
- Each screen: `text.summary` (what it is for, 1-2 sentences) and `elements` (the fields, buttons and columns a user needs; `description` says what each one does and any rules such as required, range or format).
- Each task: `goal` and step `text`.
- `troubleshooting`: see `troubleshooting-collection.md`.

Never write into `override`. That is the developer's field.
