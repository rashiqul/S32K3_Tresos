# Target and Board Context

## Current Evidence

The intended target is established, while the exact physical-board population and MCU FXOSC
assembly still require confirmation.

- The project declares S32K3X8EVB-Q289 board 54870 revision C with S32K358 MAPBGA289 as its
  reference platform.
- `config/Resource.xdm` records
  `Resource/ResourceGeneral/ResourceSubderivative = s32k358_mapbga289`, consistent with that intent.
- `docs/S32K3X8EVB-Q289HWUM.pdf` physical page 5 documents U80 as S32K358 V1.01 with marking
  `P32K358GGT0VJBST`; physical page 42 identifies board 54870 revision C.
- The board manual does not prove that the connected board has the documented revision or
  population. Confirm the PCB label and U80 marking before final hardware-dependent values.
- `config/Mcu.xdm` records `McuCrystalFrequencyHz = 1.6E7`. Its importer metadata includes `@DEF`
  and `@CALC`; the value is not confirmation of the oscillator fitted to the actual board.
- The board manual's explicit 50 MHz oscillator is the Ethernet SABRE TXCLK source on physical
  page 40, not the MCU FXOSC. Obtain the board schematic/BOM or inspect the MCU oscillator component
  marking before accepting 16 MHz as the FXOSC input.
- `McuClockSettingConfig` is an empty map. No saved PLL, divider, core, bus, or peripheral-clock
  configuration exists to reuse or validate.
- A graph `Device(S32K358)` entity or an S32K358 datasheet citation establishes source
  applicability only. It does not assert that this project is configured for, or physically uses,
  that derivative.

## Mandatory Hardware-Identity Gate

Before giving final values for any hardware-dependent configuration, confirm all applicable items:

1. Exact MCU derivative and package fitted to the board.
2. Board name, revision, and assembly/population variant.
3. Actual oscillator, crystal, clock-source, transceiver, memory, PHY, or external-device part and
   fitted options relevant to the request.
4. Required operating frequencies, voltages, modes, wakeup behavior, and failure response.
5. Peripheral instances and board routes, including jumpers, straps, connectors, and mux conflicts.

If these facts are unavailable, provide only conditional guidance and a list of evidence needed to
resolve it. Do not produce final PLL/divider values, timing parameters, pin assignments, external
device settings, memory geometry, or electrical limits.

## Affected Areas

This gate is not MCU-only. Apply it whenever advice depends on physical derivative, package, board
assembly, or an external component, including:

- MCU clock tree, power modes, clock monitoring, and flash/RAM wait states.
- FlexCAN timing and CAN transceiver type, supply, standby/wakeup pins, termination, and routing.
- LIN transceiver routing and wakeup behavior.
- Port/Dio package pins, muxing, board nets, jumpers, and fitted components.
- NVM/Fee/Mem drivers, flash geometry, sectors, partitions, endurance, and external memory parts.
- Ethernet PHY/interface mode and reference clocks.
- ADC references, analog routing, package channels, and board population.
- GPT, PWM, ICU, SPI, I2C, UART, SENT, watchdog, DMA, interrupts, and any derivative-specific
  peripheral instance or clock source.

## Source Roles

- Use XDM only for current saved state.
- Use the EVB manual only for the board/revision/assembly it explicitly documents.
- Use the reference manual for architecture and register behavior after derivative applicability is
  established.
- Use the exact-device datasheet for package, electrical, timing, memory, and frequency limits.
- Use component datasheets or board BOM/schematic evidence for external transceivers, memories,
  oscillators, and PHYs.