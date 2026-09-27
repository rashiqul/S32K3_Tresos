# Document Map

All paths are relative to the workspace root. The PDFs are canonical and must not be copied into the skill.

## Hardware Sources

| Document | Use |
|---|---|
| `docs/S32K3XXRM.pdf` | Peripheral architecture, registers, fields, reset values, clocking, interrupts, and operating sequences |
| `docs/S32K3xx_Datasheet.pdf` | Device variants, electrical limits, timing limits, package information, and maximum frequencies |
| `docs/S32K3X8EVB-Q289HWUM.pdf` | S32K3X8EVB-Q289 connectors, jumpers, transceivers, clocks, and board-level signal routing |
| `docs/AN13435.pdf` | Application guidance and examples; informative rather than authoritative over RM/datasheet requirements |

## RTD Module Sources

| Module | User manual | Integration manual |
|---|---|---|
| BaseNXP | `docs/RTD_BASENXP_UM.pdf` | `docs/RTD_BASENXP_IM.pdf` |
| Can_43_FLEXCAN | `docs/RTD_CAN_43_FLEXCAN_UM.pdf` | `docs/RTD_CAN_43_FLEXCAN_IM.pdf` |
| Dio | `docs/RTD_DIO_UM.pdf` | `docs/RTD_DIO_IM.pdf` |
| Gpt | `docs/RTD_GPT_UM.pdf` | `docs/RTD_GPT_IM.pdf` |
| Lin_43_LPUART_FLEXIO | `docs/RTD_LIN_43_LPUART_FLEXIO_UM.pdf` | `docs/RTD_LIN_43_LPUART_FLEXIO_IM.pdf` |
| Mcl | `docs/RTD_MCL_UM.pdf` | `docs/RTD_MCL_IM.pdf` |
| Mcu | `docs/RTD_MCU_UM.pdf` | `docs/RTD_MCU_IM.pdf` |
| Platform | `docs/RTD_PLATFORM_UM.pdf` | `docs/RTD_PLATFORM_IM.pdf` |
| Port | `docs/RTD_PORT_UM.pdf` | `docs/RTD_PORT_IM.pdf` |
| Resource | `docs/RTD_RESOURCE_UM.pdf` | `docs/RTD_RESOURCE_IM.pdf` |

No dedicated EcuC manual is present. For EcuC, use `config/EcuC.xdm`, `.prefs/pref_general.xdm`, relevant integration manuals, and clearly report the documentation gap.

## Supplementary RTD Sources

The corpus also contains manuals for modules that are not currently represented by `config/*.xdm`, including ADC, AE, CAN transceiver, CRC, DPGA, Ethernet, Fee, GDU, I2C, I2S, ICU, LIN transceiver, memory drivers, messaging, OCOTP, OCU, PWM, RM, SENT, SPI, UART, watchdog, and Zipwire. It also contains RTD configuration/non-AUTOSAR guides and a Port compiler migration guide.

Search these documents when they explain a dependency or when the user is planning to add a module. Do not describe an unconfigured module as enabled or present in the current Tresos configuration.

The separate `mcal-pdf-json-extractor` skill discovers 36 complete RTD UM/IM pairs from filenames.
It uses shared RTD conventions by default, with module profile overrides under
`.github/skills/mcal-pdf-json-extractor/profiles/`. Generated JSON is local cache data under
`.cache/mcal-pdf-json-extractor/structured/` and is not a replacement for page-level manual
verification.

## Routing

- Configuration parameter semantics and constraints: module UM first.
- Driver integration, dependencies, generated artifacts, and APIs: module IM first.
- Register-level explanation: reference manual, checked against device applicability.
- Frequency, voltage, package, or timing limit: datasheet.
- Header, jumper, transceiver, or board pin: EVB hardware manual.
- Current configured value or enabled state: the corresponding XDM.
