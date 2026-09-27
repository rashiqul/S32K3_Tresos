# Source and Citation Policy

## Precedence by Claim

1. Current configured state: `config/*.xdm` and `.prefs/pref_general.xdm`.
2. Tresos parameter meaning and allowed configuration: matching RTD user manual.
3. Driver integration and dependencies: matching RTD integration manual.
4. Peripheral register behavior and programming sequence: S32K3 reference manual.
5. Electrical, package, and frequency limits: S32K3 datasheet.
6. Board routing and fitted components: EVB hardware user manual.
7. Example implementation: application note.

These sources answer different questions. Do not use a current XDM value as a documented default, an application note as a device limit, or a family-level statement as proof of exact S32K358 support.

Apply [target-context](./target-context.md) before combining these sources. A project name, graph
device entity, default Resource value, or board-manual filename is not a project-to-device binding.

## Citation Requirements

- Cite the workspace-relative document path and physical PDF page.
- Include the printed page label or section title when extraction provides it.
- Cite XDM evidence with file and full parameter/container path.
- Quote only short relevant text. Mark summaries and calculations as interpretation.
- If extracted text and the visible PDF disagree, trust the visible source and report the extraction issue.
- If manuals conflict, report revision identifiers and the conflict rather than choosing silently.
- Never infer a page or section number from nearby search results.

## Missing Evidence

When local sources do not establish a required fact:

1. State exactly what is missing.
2. Explain why the recommendation depends on it.
3. Ask the user for the application requirement or permission to search official external sources.
4. Do not fill the gap with a plausible register value or generic AUTOSAR behavior.
