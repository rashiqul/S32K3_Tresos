---
name: "Tresos XDM Safety"
description: "Use for S32K358 Tresos AUTOSAR MCAL XDM configuration analysis and parameter recommendations. Enforces local-manual evidence and read-only handling."
applyTo: "config/**/*.xdm"
---

# Tresos XDM Safety

- Use the `mcal-reference-s32k358` skill for MCAL configuration questions.
- Treat files under `config/` as current project state, not vendor defaults or complete hardware intent.
- Analyze and recommend only. Do not modify XDM unless the user explicitly replaces the advisory-only policy.
- Never modify `output/**`; EPC files are generated artifacts.
- Preserve XML namespaces, hierarchy, references, variants, and `ENABLE` metadata when describing a parameter.
- Cite local RTD or hardware manuals for parameter meaning, supported values, register behavior, and limits.
- State cross-module effects involving clocks, pins, interrupts, DMA, partitions, and configuration variants.
- Require Tresos validation/generation and target-hardware testing in the verification guidance.
