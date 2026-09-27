# Target Hardware Platform

Last reviewed: 2026-09-27

## Declared Target

| Item | Declared value | Evidence |
|---|---|---|
| Project | `S32K358_EVB` | Eclipse/workspace project identity |
| RTD package | `SW32K3_S32M27x_RTD_R23-11_7.0.1` | RTD UM/IM title and revision pages |
| RTD project build | `7.0.1 D2602` | `.prefs/pref_general.xdm` `SoftwareVersion` |
| Reference board | `S32K3X8EVB-Q289`, board 54870 revision C | `docs/S32K3X8EVB-Q289HWUM.pdf`, physical pages 41-42 |
| MCU | S32K358, MAPBGA289, U80 | Board manual, physical pages 4-5 |
| Tresos subderivative | `s32k358_mapbga289` | `config/Resource.xdm` |

This table declares project intent. Before hardware-dependent release decisions, confirm the PCB
revision and U80 marking on the physical board.

## Board Interfaces

| Interface | Board implementation | Primary route | Evidence |
|---|---|---|---|
| CAN FD 0 | TJA1153, connector J54 | PTA6/CAN0_RX, PTA7/CAN0_TX, PTC21/EN, PTC20/STB | Board manual, physical pages 25-26 |
| LIN 1 | TJA1021T/20/C, connector J675 | PTB9/LPUART9_RX, PTB10/LPUART9_TX | Board manual, physical pages 23-24 |
| USB UART | MCP2221A | PTC27/LPUART13_RX, PTC26/LPUART13_TX by default | Board manual, physical pages 21-22 |

The board manual has naming inconsistencies that must be resolved against the schematic and SIUL2
tables: physical page 6 calls the second LIN route LPUART5, while page 24 calls it LPUART12; the
second CAN physical interface is labeled CAN1 but its RX/TX route is described as CAN4 on page 26.

## Oscillator Status

The MCU FXOSC component and frequency are not identified by the board-manual text. The saved
`McuCrystalFrequencyHz` value is 16 MHz with `@DEF` and `@CALC` provenance, so it is not sufficient
hardware evidence.

The 50 MHz oscillator documented on physical page 40 is dedicated to Ethernet RGMII TXCLK at the
SABRE connector. It must not be used as evidence for MCU FXOSC.

Required closure evidence is one of:

- Q289 revision C schematic/BOM identifying the MCU crystal or oscillator reference and value.
- A readable component marking cross-checked against its datasheet.
- Frequency measurement at the relevant oscillator or clock-output test point.

## Graph Representation

The hardware extractor profile creates a `HardwarePlatform` node and cited `HardwareComponent`,
`Connector`, `Signal`, and `ClockSource` nodes. Assertions preserve the distinction between board
manual facts, declared project intent, current XDM state, and physical-board confirmation.

Run the following after hardware-profile or XDM changes:

```powershell
python -m poetry run python .github/skills/mcal-hardware-pdf-extractor/scripts/hardware_extract.py --json
just graph-stage
just graph-activate
```