# DX Assistant project status

Last updated: 23 July 2026

## Current release

The current release is **DX Assistant V0.14.1 Beta**.

- Portable ZIP: `releases/DXAssistant-v0.14.1-beta-Windows-portable.zip`
- Portable folder: `releases/DXAssistant-v0.14.1-beta-Windows-portable/`
- Per-user installer: `releases/DXAssistant-v0.14.1-beta-Setup.exe`
- User manual: `documentation/DXAssistant-v0.14.1-beta-User-Manual.docx`
- PDF manual: `documentation/DXAssistant-v0.14.1-beta-User-Manual.pdf`
- Colleague test guide: `source/COLLEAGUE_TEST_GUIDE.md`
- Portable ZIP SHA-256:
  `05F3A8BDF3C23E564088EF837752D1DD0EB53B73C21B2BD112D1B3213D3702DB`
- Installer SHA-256:
  `FB266EBD555DE059D00B81B59A10D5CCA101C108ADD3D13CC0F411FD08B67E3A`

V0.14.1 passed 111 automated tests, source, portable and installed no-radio
smoke tests, a hidden dashboard startup test, 956-entry archive verification,
and a silent install/smoke/uninstall test that confirmed the private
`config.json` is created from the template and preserved. Repository
synchronization is pending the final release commit.

## Active development

The authoritative development tree is `source/`. It currently reports version
`0.14.1-beta`.

Implemented for V0.14.1:

- Replaced the tracked mutable configuration with a credential-free template;
  first launch creates the ignored, operator-owned `config.json`.
- Periodic callbacks always reschedule after unexpected errors, and stale
  receiver events after rapid Start/Stop are safely discarded.
- Unexpected background-worker and malformed OmniRig responses now return
  controlled results so tuning, polling and notification controls recover.
- Decode-log failures no longer interrupt monitoring.
- Receiver bind, socket ownership and rapid restart handling are hardened.
- Configuration read errors use the normal visible error path.
- Target Pushover alerts use bounded response reads and up to three delivery
  attempts; malformed UDP warnings are ignored or rate-limited.
- Application HTTP version identifiers share the authoritative application
  version.

Implemented for V0.14.0:

- Added optional Pushover phone notifications for newly raised target alerts.
- Added a stopped-only **Mobile alerts** dialog with masked User Key and API
  Token fields, enable control, local save and test-notification action.
- The GUI states that the Pushover app is required on the phone.
- Each newly raised alert can produce one normal-priority phone notification
  containing target, band/frequency, mode, UTC decode time and SNR. Repeated
  target decodes during the same active alert do not repeatedly notify.
- Pushover delivery runs in the background and fails quietly: local visual and
  audible alerts, retained decodes and monitoring remain unaffected.
- Credentials remain local in `config.json`, are absent from the supplied
  configuration template, and are never included in diagnostics or event logs.
- Pushover is notification-only and adds no radio or transmit control.

Retained from V0.13.1:

- Removed the Max W column, Edit max drive control, active maximum-power model,
  and supplied configuration values because DX Assistant cannot set or verify
  RF power. Legacy `power_watts` values are ignored for compatibility.
- Operator guidance now requires safe RF power to be selected and confirmed at
  the radio.

Retained from V0.13.0:

- Added standard 160m (1.840 MHz), 80m (3.573 MHz), and 6m (50.313 MHz)
  entries. They default to disabled pending antenna confirmation.
- Older saved band plans gain the new rows without overwriting existing
  antenna selections or frequencies.
- Added the MHz unit to the top dial-frequency value and green availability
  styling to **Change target**.
- Recent activity now runs oldest-to-newest with the latest decode visible at
  the bottom.
- Immediate selected-band monitoring clears blue selection and keyboard focus
  while retaining the green current-band marker.

Retained from V0.12.0:

- The selected target callsign is saved immediately to `config.json` when
  **Change target** succeeds.
- The next launch reopens with the last selected callsign instead of reverting
  to T22TT.
- A failed configuration write leaves the current target unchanged and reports
  an error.
- Append-only UTC event/audit logging with bounded in-memory failure buffering.
- Diagnostics, alarm test/open-log actions, and 15-minute audible mute while
  preserving visual target alerts.
- Unsigned per-user Windows installer, Start Menu integration, optional desktop
  shortcut and preserved configuration.
- OmniRig capability discovery with a read-only dashboard compatibility check.
- Removal of the FTDX101D model-name gate; tuning uses only OmniRig COM
  properties and capability methods.
- Fail-closed rejection before writes when a profile lacks any required
  dual-VFO or safety-state capability.
- A controlled colleague test guide for experimental radio validation.

Verification baseline: **111 automated tests passing** on 23 July 2026.

## Proven operating environment (previous release)

- Windows 11
- WSJT-X 3.0.1
- OmniRig 1.20, Rig 1
- Yaesu FTDX101D
- Split operation with receive on VFO A and transmit on VFO B
- WSJT-X UDP server `127.0.0.1:2237`

## Current capabilities

- Local WSJT-X Heartbeat, Status, and Decode reception.
- Sender-role target detection and retained target-decode history.
- Alert acknowledgement separated from explicit search resume.
- Guarded enabled-band round-robin hopping with selectable dwell.
- Operator-selected immediate-band monitoring.
- Persistent antenna band enablement, non-standard frequencies, station locator,
  PSK Reporter radius, and target callsign.
- Standard 160m through 6m plan with upgrade-safe addition of missing bands.
- PSK Reporter band focus with automatic full-sweep fallback.
- Optional one-per-alert Pushover phone notification with a stopped-only test
  and configuration dialog.
- Configure-only preparation of DX Call/Grid in WSJT-X.
- Portable Windows executable with bundled Python runtime.

## Compatibility and known limits

- CAT band searching has no model-name allow-list. It requires OmniRig Rig 1 to
  advertise readable/writable VFO A and B frequency plus readable VFO, split,
  receive and transmit state.
- A positive compatibility check is a candidate result, not proof of correct
  hardware/profile behaviour. Each radio needs the controlled live test in
  `COLLEAGUE_TEST_GUIDE.md` before operational reliance.
- DX Assistant has no RF-power display or setting control. Safe power must be
  selected and confirmed directly by the operator at the radio.
- The installer is unsigned, so Windows may display an unknown-publisher warning.
- Pushover mobile delivery requires its phone app, a Pushover account, an
  application/API token, and internet access. DX Assistant cannot guarantee
  delivery and never substitutes it for the local alert.
- PSK Reporter is the sole external evidence source. Cluster integration and any
  transmit automation are outside the current scope.

## Candidate next-release scope

- Incorporate findings from the V0.11 operator acceptance and endurance test.
- Collect colleague results and document profiles that pass physical validation.
- Consider a future explicitly designed strategy for radios that do not expose
  the required dual-VFO state; V0.13 fails closed for those profiles.
- Consider code signing only if distribution expands beyond private Beta use.

The consolidated conversation-to-development comparison is maintained in
`documentation/GAP_ANALYSIS.md`. It distinguishes open work from development-
only changes and deliberately excluded transmit-related behaviour.

## Next operator input

- Complete `documentation/OPERATOR_ACCEPTANCE_TEST.md` with the FTDX101D and use
  `source/COLLEAGUE_TEST_GUIDE.md` for each additional candidate radio.
- Configure personal Pushover credentials locally, send a test notification,
  and confirm one phone notification is received for a newly raised target
  alert. Do not send the credentials to the developer or commit them.
