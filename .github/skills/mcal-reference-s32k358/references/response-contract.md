# Response Contract

Use this structure for configuration guidance.

## Request and Assumptions

State the requested behavior, known hardware, and every unresolved input. Do not hide assumptions inside calculations.

## Current Configuration

Report relevant XDM values using the file and full container/parameter path. Note disabled containers and empty maps.

## Manual Evidence

For each decisive fact, provide the local PDF path, physical PDF page, printed page label or section when available, and a concise interpretation.

## Recommendation

List the exact Tresos module, container path, parameter, and proposed value. Explain why it follows from the evidence. Do not modify the XDM.

## Calculations

Show equations, source values, units, rounding, achieved result, and error or margin. Reject combinations that violate a cited limit.

## Cross-Module Impact

Cover affected clocks, pins, interrupts, DMA, partitions, callbacks, variants, and initialization ordering.

## Verification

Include Tresos validation and generation, generated-code compilation, and relevant target measurements or communication tests. Static guidance is not hardware validation or safety certification.

## Unresolved Items

List missing requirements, absent documents, revision conflicts, extraction failures, and any external research that would require permission.