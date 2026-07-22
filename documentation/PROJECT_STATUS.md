# DX Assistant project status

Last updated: 22 July 2026

## Current release

The current release is **DX Assistant V0.13.1 Beta**.

- Portable ZIP: `releases/DXAssistant-v0.13.1-beta-Windows-portable.zip`
- Portable folder: `releases/DXAssistant-v0.13.1-beta-Windows-portable/`
- Per-user installer: `releases/DXAssistant-v0.13.1-beta-Setup.exe`
- User manual: `documentation/DXAssistant-v0.13.1-beta-User-Manual.docx`
- PDF manual: `documentation/DXAssistant-v0.13.1-beta-User-Manual.pdf`
- Colleague test guide: `source/COLLEAGUE_TEST_GUIDE.md`
- Portable ZIP SHA-256:
  `563C53629B5FDFD0A6171D52728F72EDF3C3A5F4DC8F564D7A891EE4A4A1CC3A`
- Installer SHA-256:
  `AD7F2D9801A61BE3BEB74137F0B745CDC97D70D11E3898F3D646141A39BDBBB0`

V0.13.1 passed 86 automated tests, source, portable and installed no-radio smoke tests,
a hidden dashboard startup test, 956-entry archive verification, and a silent
install/smoke/uninstall test that confirmed `config.json` is preserved.

## Active development

The authoritative development tree is `source/`. It currently reports version
`0.13.1-beta` and matches the packaged release.

Implemented for V0.13.1:

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

Verification baseline: **86 automated tests passing** on 22 July 2026.

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
