# DX Assistant

DX Assistant is a receive-only Windows companion for WSJT-X that helps an
operator find and follow a target DX station more efficiently on FT8 using live
data from the operator's own radio and WSJT-X session. It watches local WSJT-X
decode traffic for a selected callsign, reads the current radio state through
OmniRig, uses PSK Reporter data as supporting evidence to narrow the search to
the most likely band activity, and applies guarded VFO frequency alignment
through the OmniRig API when the required safety checks pass.

The application is designed to improve search and tuning workflow without
automating transmission. It works from live receive-side operating data at your
station, not from a remote control or autonomous transmit path. It never keys
the radio, never initiates a reply, and never takes control of operating
decisions; the operator remains fully in control at all times.

The current release is **V0.14.0 Beta**. Radio support
is capability-gated rather than model-gated: an OmniRig profile must expose the
required dual-VFO frequency and safety-state features, and every new radio
still requires the controlled physical validation described in the colleague
guide.

## Installation

### Windows installer

1. Download `DXAssistant-v0.14.0-beta-Setup.exe` from the current release.
2. Close any earlier DX Assistant instance.
3. Run the installer. It is currently unsigned, so Windows may show an
   unknown-publisher warning; verify that the file came from this repository.
4. Keep the default per-user installation location unless you have a reason to
   change it.
5. Start **DX Assistant** from the Start Menu.

### Portable package

1. Download `DXAssistant-v0.14.0-beta-Windows-portable.zip` from the current
   release.
2. Select **Extract All**. Do not run the application inside the ZIP preview.
3. Keep `DXAssistant.exe`, `config.json`, and the complete `_internal` folder
   together.
4. Run `DXAssistant.exe`; a separate Python installation is not required.

### Prerequisites

- Windows 11 or another compatible 64-bit Windows installation.
- WSJT-X, configured to send UDP reports to `127.0.0.1:2237` and to accept UDP
  requests.
- OmniRig 1.20 with Rig 1 online and configured with the exact profile for the
  connected radio.
- A radio/profile combination exposing readable and writable VFO A and VFO B
  frequency plus readable VFO, split, receive, and transmit state.
- For optional phone notifications: the Pushover app on the phone, a Pushover
  User Key, and an application API Token.

## Quick start

1. Put the amplifier in standby for the initial compatibility test. Confirm the
   radio is receiving, split is on, receive is on VFO A, and transmit is on
   VFO B.
2. Start OmniRig and confirm Rig 1 can read the radio.
3. In WSJT-X, set the UDP server to `127.0.0.1`, port `2237`, select **Accept
   UDP requests**, and start monitoring.
4. Start DX Assistant and select **Check OmniRig compatibility**. This check is
   read-only. Do not continue with CAT band searching if it reports a missing
   capability.
5. While stopped, select **Change target** and enter the DX callsign.
6. Optionally select **Mobile alerts**, enter the Pushover credentials, enable
   the feature, and send a test notification.
7. Select **Start monitoring** and confirm the WSJT-X version, mode, and dial
   frequency appear.
8. Choose the dwell time and select **Start band search**.
9. When the target is decoded, inspect the retained decode and make all calling
   and transmit decisions yourself in WSJT-X.

Before testing an unvalidated radio, follow
[`source/COLLEAGUE_TEST_GUIDE.md`](source/COLLEAGUE_TEST_GUIDE.md) with the
amplifier in standby. The full operating guide is available in
[`documentation/DXAssistant-v0.14.0-beta-User-Manual.pdf`](documentation/DXAssistant-v0.14.0-beta-User-Manual.pdf).

## Project layout

- `source/` - active Python source, tests, configuration template, simulator,
  README, and release notes. All application changes are made here.
- `documentation/` - design specification, user manuals, development status,
  development log, and release checklist.
- `releases/` - packaged historical releases and distributable ZIP files.
- `build/` - PyInstaller output, document-rendering work, and reusable build
  scripts. Contents may contain historical absolute paths and are not the
  authoritative source.

## Current positions

- Latest packaged release: V0.14.0 Beta.
- Active development source: `source/` at version `0.14.0-beta`.
- OmniRig integration is capability-gated and contains no radio-model allow-list.
- Standard session plan: 160m through 6m, with 160m, 80m and 6m disabled by
  default pending antenna configuration.
- Optional notification-only Pushover mobile alerts; credentials remain local
  and are excluded from logs.
- Automated test baseline: 94 passing tests as of 23 July 2026.
- Canonical repository: `https://github.com/requirementXYZ/DXAssistant`.

See `documentation/PROJECT_STATUS.md` for the current product state and
`documentation/DEVELOPMENT_LOG.md` for the running history.

## Safety boundary

DX Assistant never initiates transmission. The production application has no
PTT, Enable Tx, Halt Tx, reply, radio-mode, split-setting, or power-setting
command path. The operator always remains in control. OmniRig access is limited
to guarded VFO A and VFO B frequency alignment after receive/split/routing
interlocks pass.
