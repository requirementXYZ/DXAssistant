# DX Assistant release checklist

## Source and documentation

- [ ] Version number updated in `source/dxassistant/__init__.py`.
- [ ] Source README matches packaged behaviour.
- [ ] Release notes contain only completed changes.
- [ ] Project status and development log updated.
- [ ] User manual updated if controls or workflow changed.

## Verification

- [ ] Full automated test suite passes.
- [ ] Safety/static tests pass.
- [ ] No-radio source smoke test passes.
- [ ] Relevant live receive-only checks completed by the operator.

## Package

- [ ] Fresh versioned PyInstaller build directory used.
- [ ] Absolute OmniRig bridge `--add-data` source path used.
- [ ] Portable folder contains `DXAssistant.exe`, `_internal`,
  `config.template.json`,
  README, release notes, and current manual.
- [ ] First packaged launch creates `config.json` without modifying the template.
- [ ] No duplicated nested portable folder exists.
- [ ] Packaged `--smoke-test` returns exit code 0.
- [ ] Dashboard opens from the packaged folder without starting monitoring.
- [ ] ZIP contents explicitly inspected.
- [ ] ZIP SHA-256 recorded in the development log.

## Handover

- [ ] Operator told to close the previous version before starting the new one.
- [ ] Operator told to extract the complete ZIP and keep all files together.
- [ ] Compatibility and known limitations stated clearly.
- [ ] Any required live operator test described precisely.
