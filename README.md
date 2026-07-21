# DX Assistant

DX Assistant is a receive-only Windows companion for WSJT-X that watches for a
selected DX callsign, uses PSK Reporter evidence to focus an FT8 band search,
and performs guarded VFO frequency alignment through the OmniRig API. It never
initiates transmission; the operator always remains in control.

The current release is **V0.12.0 Experimental Multi-Radio Beta**. Radio support
is capability-gated rather than model-gated: an OmniRig profile must expose the
required dual-VFO frequency and safety-state features, and every new radio still
requires the controlled physical validation described in the colleague guide.

## Installation

### Windows installer

1. Download `DXAssistant-v0.12.0-beta-Setup.exe` from the current release.
2. Close any earlier DX Assistant instance.
3. Run the installer. It is currently unsigned, so Windows may show an
   unknown-publisher warning; verify that the file came from this repository.
4. Keep the default per-user installation location unless you have a reason to
   change it.
5. Start **DX Assistant** from the Start Menu.

### Portable package

1. Download `DXAssistant-v0.12.0-beta-Windows-portable.zip` from the current
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
6. Select **Start monitoring** and confirm the WSJT-X version, mode, and dial
   frequency appear.
7. Choose the dwell time and select **Start band search**.
8. When the target is decoded, inspect the retained decode and make all calling
   and transmit decisions yourself in WSJT-X.

Before testing an unvalidated radio, follow
[`source/COLLEAGUE_TEST_GUIDE.md`](source/COLLEAGUE_TEST_GUIDE.md) with the
amplifier in standby. The full operating guide is available in
[`documentation/DXAssistant-v0.12.0-beta-User-Manual.pdf`](documentation/DXAssistant-v0.12.0-beta-User-Manual.pdf).

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

- Latest packaged release: V0.12.0 Experimental Multi-Radio Beta.
- Active development source: `source/` at version `0.12.0-beta`.
- OmniRig integration is capability-gated and contains no radio-model allow-list.
- Automated test baseline: 85 passing tests as of 20 July 2026.
- Canonical repository: `https://github.com/requirementXYZ/DXAssistant`.

See `documentation/PROJECT_STATUS.md` for the current product state and
`documentation/DEVELOPMENT_LOG.md` for the running history.

## Safety boundary

DX Assistant never initiates transmission. The production application has no
PTT, Enable Tx, Halt Tx, reply, radio-mode, split-setting, or power-setting
command path. The operator always remains in control. OmniRig access is limited
to guarded VFO A and VFO B frequency alignment after receive/split/routing
interlocks pass.
