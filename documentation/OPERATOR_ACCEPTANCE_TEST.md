# DX Assistant V0.11.0 Beta operator acceptance test

These are the remaining live checks. Automated tests and packaging checks do not
transmit or alter a live radio. Perform the radio portions only when convenient,
with WSJT-X Enable Tx off and the amplifier in standby.

## Installation and startup

- Close every older DX Assistant instance.
- Run `DXAssistant-v0.11.0-beta-Setup.exe` and accept or decline the optional
  desktop shortcut.
- Confirm the application opens from the Start Menu and reports V0.11.0 Beta.
- Confirm the previous portable release remains untouched.
- If Windows SmartScreen appears, confirm the file name before choosing to run
  the unsigned private Beta.

## Safe monitoring workflow

- Confirm OmniRig Rig 1 reports exactly `FTDX101D`.
- Confirm radio RX, split on, receive VFO A and transmit VFO B.
- Start monitoring, then start a short two-band search.
- Confirm both VFOs align and WSJT-X remains receive-only.
- Change target while stopped, close and reopen DX Assistant, and confirm the
  selected target persists.

## Alarm and diagnostics

- Open Diagnostics; confirm version, paths, WSJT-X, search and PSK Reporter state.
- Select Test alarm.
- Select Mute 15 min and use the simulator or a real target opportunity; confirm
  the visual alert/hold still occurs without a bell.
- Open the log folder and confirm a daily decode CSV and
  `events-YYYY-MM-DD.jsonl` appear during operation.

## Recovery rehearsal

- While monitoring but not transmitting, close WSJT-X. Confirm DX Assistant
  enters Degraded state and does not tune. Restart WSJT-X and confirm recovery.
- Pause or disconnect internet access for one PSK Reporter poll. Confirm the
  display reports unavailable and band search falls back to the full enabled
  sweep; restore internet and confirm a later poll recovers.
- With Enable Tx off, deliberately remove split or RX-A/TX-B routing, request a
  hop, and confirm the exact OmniRig error remains visible and no tune occurs.
  Restore the safe state and resume explicitly.

## Endurance evidence

- Run monitoring for at least eight hours.
- Record start/end time and target.
- Confirm the dashboard remains responsive, decode CSV rows are intact, event
  log JSON lines are readable, and Diagnostics reports no buffered log events.
- Send a screenshot and approximate time for any unexpected state or message.
