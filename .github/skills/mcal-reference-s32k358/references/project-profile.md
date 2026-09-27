# Project Profile

## Verified Metadata

- Eclipse project: `S32K358_EVB`.
- Eclipse natures: `dreisoft.tresos.launcher2.plugin.ecucnature` and `dreisoft.tresos.launcher2.plugin.launchernature`.
- Tresos target: `CORTEXM`.
- Tresos derivative: `S32K3XX`.
- Configuration path: `config`.
- Generation path: `output`.
- Configuration format: XDM.
- RTD software version recorded by the enabled modules: `7.0.1 D2602`.
- AUTOSAR release fields in module published information: `4.9.0`.

The project name suggests S32K358 EVB intent, but neither the name nor the supplied Q289 board
manual proves the fitted derivative, package, board revision, or assembly. `ResourceSubderivative`
currently records `s32k389_mapbga437` with `@DEF` provenance and is not confirmed application
intent. Apply the mandatory gate in [target-context](./target-context.md) before hardware-dependent
recommendations.

## Configured Modules

The project contains 11 module XDM files:

- `BaseNXP`
- `Can_43_FLEXCAN`
- `Dio`
- `EcuC`
- `Gpt`
- `Lin_43_LPUART_FLEXIO`
- `Mcl`
- `Mcu`
- `Platform`
- `Port`
- `Resource`

`SystemModel2.tdb` is project model data, not another MCAL module XDM file.

## Interpretation Rules

- Values in `config/*.xdm` describe the current saved configuration.
- Empty maps may mean no instances are configured; do not infer unsupported hardware.
- `IMPORTER_INFO` values such as `@DEF` or `@CALC` describe provenance, not necessarily a safe application default.
- `IMPLEMENTATION_CONFIG_VARIANT` and `POST_BUILD_VARIANT_USED` must be evaluated per module rather than globally normalized.
- Disabled elements remain relevant when explaining why a visible Tresos option is unavailable.
- Never reconcile conflicting project-name, XDM, board-manual, and physical-board identities by
	silently choosing one source.
