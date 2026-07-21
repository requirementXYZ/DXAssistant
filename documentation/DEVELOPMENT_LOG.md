# DX Assistant development log

This is the chronological record of product decisions, implementation, tests,
packaging, and operator validation. Add new entries at the top.

## 21 July 2026 - GitHub repository established and synchronized

- Established `https://github.com/requirementXYZ/DXAssistant` as the canonical
  repository on the `main` branch.
- Published the V0.12.0 Beta authoritative source, tests, project guidance and
  documentation in commit `9b217f9`.
- Added a permanent project rule requiring repository synchronization and
  pushed-commit verification for every future release.
- Added repository exclusions for build output, generated distributables,
  Python caches, logs, credentials and editor metadata.

## 20 July 2026 - V0.12.0 experimental multi-radio Beta release

User need:

- Produce a colleague-testable release that uses the OmniRig API rather than a
  radio-model allow-list, while preserving the receive-only safety boundary.

Implementation:

- Removed the FTDX101D identity gate from the PowerShell bridge. No direct CAT
  protocol or Yaesu command was added; all radio interaction remains through
  OmniRig COM.
- Added discovery through `IsParamReadable` and `IsParamWriteable`. A profile
  must expose read/write VFO A and B frequency plus readable VFO, split,
  receive and transmit state before any tune is attempted.
- Added a read-only **Check OmniRig compatibility** dashboard action and clear
  missing-capability diagnostics. Alignment remains VFO B first, then VFO A,
  with read-back verification and the existing receive/split/routing guards.
- Added regression coverage, model-neutral operator wording, a controlled
  colleague test guide, release notes and an updated 11-page user manual.
- Produced an unsigned per-user installer and complete portable ZIP.

Verification:

- 85 automated tests passed from `source/`.
- PowerShell bridge parser and Python byte-compilation checks passed.
- Portable no-radio smoke test passed; the packaged dashboard remained running
  during a four-second hidden startup test.
- The 957-entry ZIP contains the executable, bundled bridge/runtime,
  configuration, release notes, README, colleague test guide, and DOCX/PDF
  manuals without an unwanted enclosing folder.
- Silent installer install, installed no-radio smoke test and uninstall passed;
  `config.json` remained after uninstall.
- The DOCX was exported through Microsoft Word, rendered to 11 PDF page images
  and visually inspected.

Packages:

- `releases/DXAssistant-v0.12.0-beta-Windows-portable.zip`
  - SHA-256: `ED544B1E08FA9DEB6417295BD3A0D9FE6025596BCBEC990C918A12590B24A053`
- `releases/DXAssistant-v0.12.0-beta-Setup.exe`
  - SHA-256: `4E67EE128FFF5D6A9C01A390FE3D3199B45903E42E0D84E7250247A4D64E9C3B`

Remaining live test:

- Automated testing did not connect to or alter a radio. The FTDX101D and each
  additional OmniRig profile remain operator checkpoints. A positive capability
  result means candidate-compatible only; colleagues must follow
  `COLLEAGUE_TEST_GUIDE.md` with the amplifier in standby.

## 20 July 2026 - OmniRig multi-radio compatibility investigation

User need:

- Determine how DX Assistant could safely operate with radios supported by
  OmniRig rather than relying permanently on an FTDX101D name check.

Investigation:

- Reviewed the current bridge, official OmniRig COM interface, rig-description
  format, tester guide, supported-radio list and current official INI package.
- Confirmed DX Assistant sends no direct Yaesu CAT commands, but its identity,
  split/routing expectations and frequency-write sequence are currently approved
  only for the FTDX101D.
- Statically inspected 171 official INI definitions. Fifty-five advertise the
  broad parameter shape of the current dual-VFO workflow; this is a candidate
  pool, not hardware compatibility evidence.
- Produced `documentation/OMNIRIG_COMPATIBILITY_STUDY.md` recommending capability
  discovery, explicit tuning strategies, an approved-profile registry and a
  receive-only operator validation wizard.

Verification:

- Research and documentation only; no source, package or live-radio behaviour
  changed, so the V0.11.0 test/package baseline remains unchanged.

## 20 July 2026 - V0.11.0 gap-closure release

User need and scope decisions:

- Complete the applicable conversation-to-development gaps and deliver a fully
  tested build for operator testing.
- Use PSK Reporter as the sole external evidence source, support the FTDX101D
  only, and provide an unsigned per-user installer alongside the portable ZIP.

Implementation:

- Packaged persistent last-target behaviour.
- Added append-only UTC JSON Lines event logging for state, operator, target,
  WSJT-X preparation, PSK Reporter, tuning and failure events.
- Added bounded 250-record in-memory buffering and recovery flush after log-write
  failure.
- Added Diagnostics with log health, alarm test and open-log actions, plus a
  15-minute audible mute that preserves visual alerts.
- Added and compiled an Inno Setup per-user installer with Start Menu, optional
  desktop shortcut, uninstall support and configuration preservation.
- Formally reconciled the old blueprint: cluster and non-FTDX101D radio profiles
  are outside the approved current scope.
- Updated README, release notes, gap/status records, product scope, acceptance
  test, and the visually checked 11-page DOCX/PDF user manual.

Verification and packaging:

- 81 automated tests passed after development.
- PyInstaller 6.21.0 / Python 3.14.6 one-directory build succeeded.
- Packaged no-radio smoke test returned exit code 0.
- Hidden packaged dashboard remained running until deliberately closed.
- Portable ZIP contains 956 entries with no duplicated nested release folder.
- Inno Setup 6.7.3 compile succeeded.
- Silent installer install, installed no-radio smoke, and uninstall returned exit
  code 0; `config.json` remained preserved.
- Portable ZIP SHA-256:
  `46B945AD28CC3BADDE5EE99C5B2AE10FD71870AC7D0599EBBAA2FC21C6E1175D`.
- Installer SHA-256:
  `734717202A410A56412BC85A0000D0B016E752E381BCF1F9CE93AA41AF092AEE`.

Remaining live test:

- The operator acceptance, interruption recovery and eight-hour endurance checks
  in `documentation/OPERATOR_ACCEPTANCE_TEST.md` require the operator's live
  FTDX101D/WSJT-X environment. No automated test transmitted or altered a live
  radio.

## 20 July 2026 - Conversation-to-development gap analysis

User need:

- Consolidate the DX Assistant discussions and identify what was discussed but
  has not been developed in the maintained project.

Work completed:

- Compared the historical DX Assistant task and Version 1.0 design blueprint
  with `source/`, tests, project records, and V0.10.0 release evidence.
- Added `documentation/GAP_ANALYSIS.md`, separating released work, development-
  only work, genuine open gaps, acceptance-evidence gaps, and deliberately
  excluded safety behaviour.
- Identified the leading open items as packaging the persistent target, event/
  audit logging, structured recovery evidence, radio-profile validation,
  installer decisions, and reconciliation of the older cluster/multi-source
  blueprint.

Verification:

- The complete source suite passed: 77 tests on 20 July 2026.
- This was a documentation analysis only; no application behaviour or release
  package changed, so no packaged smoke test or new checksum was required.

## 20 July 2026 - Permanent project workspace and persistent target

User needs:

- Move the project out of the dated Codex workspace into a stable folder.
- Maintain development documentation as the project progresses.
- Retain the last target callsign between application runs.

Work completed:

- Established `C:\Users\g8ajm\Documents\Codex\DX_Assistant` as the permanent
  project root.
- Moved active source to `source/`, packaged history to `releases/`, design/user
  documents to `documentation/`, and build history to `build/`.
- Added root working instructions and enduring status/log/checklist documents.
- Added `save_target_call()` with validation, normalization, atomic JSON update,
  and dashboard error handling.
- Updated the source-path packaging test for the new `source/` directory.

Verification:

- 77 automated tests passed after the persistent-target change.
- The existing V0.10.0 packaged executable passed its no-radio smoke test from
  the new permanent path, and the release ZIP checksum remained unchanged.
- No executable was packaged; this behaviour remains development-only until the
  next release.

## 19 July 2026 - V0.10.0 Beta and user documentation

Released improvements:

- Persistent band enablement and edited DXpedition frequencies.
- Red indication for non-standard band frequencies.
- Standard-frequency restoration without changing antenna enablement.
- Clear green/amber/grey action-state colours.
- Persistent OmniRig interlock error detail.
- Renamed manual WSJT-X action to **Re-send target to WSJT-X**.
- Target alerts preserve snapped/maximized window layout and raise only once per
  unacknowledged alarm.

Verification and packaging:

- 76 automated tests passed.
- PyInstaller 6.21.0 / Python 3.14.6 portable build succeeded.
- Packaged no-radio smoke test returned exit code 0.
- Hidden dashboard startup succeeded.
- Duplicate nested release folder was removed and ZIP contents reverified.
- Final V0.10.0 ZIP SHA-256:
  `B3BB17D4D886804F77ED18C33D2CAE8E1BBC65347C873EDDB7DD2B2FBA432697`.
- Produced and visually verified an 11-page DOCX/PDF user manual.

## 17 July 2026 - V0.9.0 first portable Beta

- Produced the first self-contained Windows executable release.
- Added travel-aware PSK Reporter locator/radius controls and band focus.
- Added Configure-only WSJT-X DX Call/Grid preparation.
- Confirmed the app does not send PTT, Enable Tx, Halt Tx, mode, split, or power
  commands.
- Diagnosed a live **Search error** as a guarded OmniRig interlock failure while
  WSJT-X UDP decoding remained healthy.
- Proved the PyInstaller package must include `omnirig_bridge.ps1` using an
  absolute source path.

## 14-16 July 2026 - Band hopping and operator workflow

- Added separate compact recent-decode and retained target-decode panels.
- Added band labels, three-decimal MHz display, non-standard session frequencies,
  antenna band enablement, per-band reference power, and current-band highlight.
- Added guarded VFO A/B alignment through OmniRig.
- Established 120 seconds as the practical default dwell with selectable values.
- Added target hold, explicit acknowledgement, explicit resume, and operator
  ownership whenever WSJT-X Enable Tx is active.
- Added immediate selected-band monitoring and removed stale blue selection
  highlighting after band changes.

## 13 July 2026 - Recovery and design baseline

- Recovered the previous FTDX101D assistant materials and working intent.
- Created the DX Assistant design specification and receive-only safety boundary.
- Established the state machine, WSJT-X UDP receiver, target parsing, CSV logging,
  dashboard, simulator, and automated safety tests.
- Preserved two non-negotiable principles: the assistant never initiates
  transmission, and the operator always remains in control.
