# DX Assistant project status

Last updated: 20 July 2026

## Current release

The release being packaged is **DX Assistant V0.12.0 Experimental Multi-Radio Beta**.

- Portable ZIP: `releases/DXAssistant-v0.12.0-beta-Windows-portable.zip`
- Portable folder: `releases/DXAssistant-v0.12.0-beta-Windows-portable/`
- Per-user installer: `releases/DXAssistant-v0.12.0-beta-Setup.exe`
- User manual: `documentation/DXAssistant-v0.12.0-beta-User-Manual.docx`
- PDF manual: `documentation/DXAssistant-v0.12.0-beta-User-Manual.pdf`
- Colleague test guide: `source/COLLEAGUE_TEST_GUIDE.md`
- Portable ZIP SHA-256:
  `ED544B1E08FA9DEB6417295BD3A0D9FE6025596BCBEC990C918A12590B24A053`
- Installer SHA-256:
  `4E67EE128FFF5D6A9C01A390FE3D3199B45903E42E0D84E7250247A4D64E9C3B`

V0.12.0 passed 85 automated tests, portable and installed no-radio smoke tests,
a hidden dashboard startup test, 957-entry archive verification, and a silent
install/smoke/uninstall test that confirmed `config.json` is preserved.

## Active development

The authoritative development tree is `source/`. It currently reports version
`0.12.0-beta` and matches the packaged release.

Implemented for V0.12.0:

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

Verification baseline: **85 automated tests passing** on 20 July 2026.

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
- Persistent antenna band enablement, non-standard frequencies, drive reference,
  station locator, PSK Reporter radius, and next-release target callsign.
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
- The maximum-drive values are reference/display values only. DX Assistant does
  not set or verify RF power.
- The installer is unsigned, so Windows may display an unknown-publisher warning.
- PSK Reporter is the sole external evidence source. Cluster integration and any
  transmit automation are outside the current scope.

## Candidate next-release scope

- Incorporate findings from the V0.11 operator acceptance and endurance test.
- Collect colleague results and document profiles that pass physical validation.
- Consider a future explicitly designed strategy for radios that do not expose
  the required dual-VFO state; V0.12 fails closed for those profiles.
- Consider code signing only if distribution expands beyond private Beta use.

The consolidated conversation-to-development comparison is maintained in
`documentation/GAP_ANALYSIS.md`. It distinguishes open work from development-
only changes and deliberately excluded transmit-related behaviour.

## Next operator input

- Complete `documentation/OPERATOR_ACCEPTANCE_TEST.md` with the FTDX101D and use
  `source/COLLEAGUE_TEST_GUIDE.md` for each additional candidate radio.
