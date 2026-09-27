# Module Workflows

Use only the sections relevant to the request, then inspect all named dependencies.

## Mandatory Target Context

- Apply [target-context](./target-context.md) before every workflow whose result depends on the MCU
	derivative, package, board revision, oscillator, external component, memory geometry, or board
	routing.
- Until those facts are reconciled, provide conditional options and required evidence rather than
	final register values, timings, pin assignments, memory sectors, or external-device settings.

## Resource, EcuC, and BaseNXP

- Confirm derivative, architecture, RTD release, and active configuration variant.
- Check partition references and whether the referenced OS/EcuC entities exist.
- For BaseNXP, establish OSIF counter source, units, multicore behavior, and user-mode support.
- Do not assume variant settings must match across modules; explain each module's generation model.

## MCU

- Establish oscillator frequencies, PLL inputs/outputs, dividers, system/core/bus clocks, and allowable limits.
- Check clock-monitor, reset, power-mode, RAM, flash wait-state, and timeout behavior.
- Trace every affected peripheral clock into GPT, CAN, LIN, Platform, and MCL.
- Show clock equations and units; account for integer divider constraints and tolerance.

## Port and Dio

- Resolve the exact package pin, SIUL2 instance, PCR/MSCR/IMCR mapping, mux mode, direction, pull, drive, and initial level.
- Check EVB routing, jumpers, transceivers, and conflicts with debug/JTAG or other functions.
- Detect duplicate pin/PCR ownership and reconcile Dio channel/port definitions with Port configuration.
- Separate pad configuration, input selection, GPIO direction, and peripheral ownership.

## Platform

- Identify interrupt source, vector, core, priority, routing, and enablement.
- Check MCM, MPU, VTOR, multicore, privilege, and partition assumptions when relevant.
- Verify the associated peripheral and clock configuration before recommending interrupt settings.

## MCL

- Identify DMA/eDMA instance, channel, request source, transfer shape, arbitration, callback, and cache implications.
- Check trigger mux, LCU, eMIOS, or shared-service configuration only when used by a consumer.
- Verify ownership conflicts and dependencies from CAN, LIN, GPT, or other drivers.

## GPT

- Establish timer IP/instance/channel, source clock, requested period, resolution, mode, notification, and wakeup behavior.
- Calculate prescaler and tick counts, including rounding error and maximum count.
- Check MCU clock availability and Platform interrupt routing.

## Can_43_FLEXCAN

- Establish FlexCAN instance, classic CAN versus CAN FD, nominal/data bit rates, sample points, oscillator tolerance, and payload requirements.
- Calculate prescaler and timing segments from the confirmed source clock; report achieved rates and errors.
- Check controller, hardware object, mailbox/FIFO, interrupt, wakeup, and transceiver configuration.
- Verify MCU clock, Port mux, Platform interrupt, and EVB transceiver routing dependencies.
- Confirm the fitted CAN transceiver part, supply/interface voltage, termination, standby/wakeup
	wiring, board revision, and selected FlexCAN instance before final timing or wakeup guidance.

## Lin_43_LPUART_FLEXIO

- Establish LPUART versus FLEXIO implementation, role, baud rate, frame timing, checksum model, wakeup, timeout, interrupt, and DMA requirements.
- Calculate baud divisors from the confirmed source clock and report error.
- Verify MCU clock, Port mux, Platform interrupt, MCL DMA, and EVB transceiver routing dependencies.
- Confirm the fitted LIN transceiver, board route, supply, enable/wakeup wiring, and population
	options before final electrical or wakeup guidance.

## NVM, Fee, Mem, and OCOTP

- Confirm the exact derivative and its internal flash/data-flash geometry before selecting sectors,
	erase units, partitions, or Fee layout.
- For external memory, confirm the fitted device, bus interface, density, page/sector geometry,
	voltage, timing, and board route.
- Treat supplementary module manuals as capability documentation only when no corresponding XDM
	module is configured; do not describe those drivers as enabled.
- Check endurance, retention, alignment, ECC, reserved areas, boot/header regions, and generated
	linker/memory-map dependencies against exact-device evidence.

## Common Completion Checks

- Confirm units and allowed ranges from the module manual.
- Confirm referenced containers exist and enabled conditions are satisfied.
- Identify impacts on generated code, memory, interrupts, and initialization order.
- Provide Tresos validation, generation, compile, and target-test steps appropriate to the change.
