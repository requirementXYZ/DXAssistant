# DX Assistant V0.14.0 Beta operator acceptance test

These are the remaining live checks. Automated tests and packaging checks do not
transmit or alter a live radio. Perform the radio portions only when convenient,
with WSJT-X Enable Tx off and the amplifier in standby.

## Installation and startup

- Close every older DX Assistant instance.
- Run `DXAssistant-v0.14.0-beta-Setup.exe` and accept or decline the optional
  desktop shortcut.
- Confirm the application opens from the Start Menu and reports V0.14.0 Beta.
- Confirm the previous portable release remains untouched.
- If Windows SmartScreen appears, confirm the file name before choosing to run
  the unsigned private Beta.

## Safe monitoring workflow

- For the proven FTDX101D environment, confirm OmniRig Rig 1 reports
  `FTDX101D`. For another radio, complete the colleague compatibility guide
  before relying on search tuning.
- Confirm radio RX, split on, receive VFO A and transmit VFO B.
- Start monitoring, then start a short two-band search.
- Confirm both VFOs align and WSJT-X remains receive-only.
- Change target while stopped, close and reopen DX Assistant, and confirm the
  selected target persists.

## Dashboard and band-plan checks

- Confirm the session plan shows 160m at 1.840 MHz, 80m at 3.573 MHz and 6m at
  50.313 MHz, initially disabled.
- Confirm there is no **Max W** column or **Edit max drive** button.
- Confirm the top dial-frequency value ends in `MHz`.
- While stopped, confirm **Change target** is green; after monitoring starts,
  confirm it becomes grey and unavailable.
- Allow more than 12 general decodes. Confirm older rows move upward and the
  newest decode remains visible at the bottom.
- Select an enabled band and choose **Monitor selected band now**. Confirm the
  blue selection disappears while the tuned/current band remains green.
- Do not enable 160m, 80m or 6m until antenna coverage has been confirmed.
- Confirm the radio's safe RF power manually; DX Assistant neither sets nor
  verifies it.

## Alarm and diagnostics

- Open Diagnostics; confirm version, paths, WSJT-X, search and PSK Reporter state.
- Select Test alarm.
- Select Mute 15 min and use the simulator or a real target opportunity; confirm
  the visual alert/hold still occurs without a bell.
- Open the log folder and confirm a daily decode CSV and
  `events-YYYY-MM-DD.jsonl` appear during operation.

## Pushover mobile-alert checks

- Install and configure the Pushover app on the phone. Create a personal
  Pushover application/API token; keep the User Key and API Token private.
- With monitoring stopped, select **Mobile alerts**. Confirm the dialog clearly
  says that the Pushover app is required on the phone.
- Enter the two 30-character keys. Confirm both fields are masked, enable mobile
  alerts, and select **Send test notification**.
- Confirm the test arrives on the intended phone, then save the settings.
- Use the simulator or a suitable live target opportunity. Confirm a newly
  raised target alert produces one phone notification containing the target,
  band/frequency, mode, UTC time and SNR.
- Allow further target decodes while the same alert remains active and confirm
  the phone is not repeatedly notified.
- Temporarily use an invalid token or disconnect internet access. Confirm the
  local target alert, retained decode and monitoring still work. Restore the
  correct setting afterwards.
- Open Diagnostics and the event log. Confirm they show only generic mobile
  status and contain neither key.

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
