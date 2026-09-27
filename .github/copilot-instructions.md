# Project Guidelines

## Status Documentation

- Treat `README.md` as the project status and implementation record.
- Whenever a change contextually or functionally alters capabilities, supported scope, workflow behavior, setup requirements, known limitations, improvement priorities, validation results, or milestone status, update the `Project Status` section of `README.md` in the same change.
- Set `Last updated` to the actual change date and add or revise the appropriate milestone-history entry.
- Keep status entries factual and verified. Do not update the status ledger for read-only investigations or changes with no contextual or functional project impact.

## MCAL Safety

- Keep the S32K358 MCAL skill advisory-only unless the user explicitly changes that policy.
- Do not edit `config/**/*.xdm`, `.prefs/**/*.xdm`, or generated `output/**` as part of advisory configuration work.
- Prefer local manuals under `docs/` and cite evidence for hardware or configuration claims.