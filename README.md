# DX Assistant

This folder is the permanent working home for the DX Assistant project.

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
