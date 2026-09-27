# Project Profile

## Verified Metadata

- Eclipse project: `S32K358_EVB`.
- Eclipse natures: `dreisoft.tresos.launcher2.plugin.ecucnature` and `dreisoft.tresos.launcher2.plugin.launchernature`.
- Tresos target: `CORTEXM`.
- Tresos derivative: `S32K3XX`.
- Configuration path: `config`.
- Generation path: `output`.
- Configuration format: XDM.
- RTD package: `SW32K3_S32M27x_RTD_R23-11_7.0.1`.
- RTD software version recorded by the enabled modules: `7.0.1 D2602`.
- The package name and AUTOSAR release are corroborated by the RTD UM/IM title and revision
	pages; the project-specific build discriminator `D2602` is recorded in
	`.prefs/pref_general.xdm`.
- AUTOSAR release fields in module published information: `4.9.0`.

The declared reference platform is S32K3X8EVB-Q289 board 54870 revision C with an S32K358 in
MAPBGA289. `ResourceSubderivative` records `s32k358_mapbga289`, consistent with that intent. This
declaration does not prove the revision or population of the physical board connected to the
developer workstation. Apply the mandatory gate in [target-context](./target-context.md) before
hardware-dependent recommendations.

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
