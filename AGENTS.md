# DX Assistant working instructions

These instructions apply to all future work in this project folder.

## Authoritative locations

- Make application changes only in `source/`.
- Put distributable builds in `releases/`.
- Use `build/` for temporary build and render output.
- Put enduring design, operating, and development records in `documentation/`.

Do not resume development in the old dated Codex workspace. Do not treat a
historical release folder or PyInstaller build tree as source.

## Required documentation updates

For every completed feature or correction:

1. Update `documentation/PROJECT_STATUS.md` if current behaviour, compatibility,
   risks, or planned work changed.
2. Add a dated entry to `documentation/DEVELOPMENT_LOG.md` describing the user
   need, implementation, verification, and any remaining live test.
3. Update `source/README.md` and `source/RELEASE_NOTES.md` when preparing a
   package.
4. Record the new package, test count, smoke-test result, and checksum in the
   development log.

## Repository synchronization

- Canonical repository: `https://github.com/requirementXYZ/DXAssistant`.
- For every completed release, commit and push the authoritative `source/`,
  `documentation/`, root project guidance, and release metadata after all tests
  and packaging checks pass.
- Confirm the pushed commit is present on the repository's default branch and
  record its commit identifier in `documentation/DEVELOPMENT_LOG.md`.
- Do not commit temporary `build/` output, local logs, caches, credentials, or
  expanded portable-package directories.
- Repository synchronization is part of release completion; if authentication
  or network access blocks it, report the release as locally complete but not
  repository-synchronized.

## Safety requirements

- Preserve: "DX Assistant never initiates transmission."
- Preserve: "The operator always remains in control."
- Do not add PTT, Enable Tx, Halt Tx, reply, radio-mode, split-setting, or
  power-setting commands without an explicit new product decision and safety
  review.
- Keep WSJT-X outbound control limited to the approved Configure request unless
  explicitly redesigned.
- Keep OmniRig writes limited to verified VFO frequency alignment.
- Treat live-radio testing as an operator checkpoint; automated tests must not
  transmit or alter a live radio.

## Verification

- Run the complete test suite from `source/` after source changes.
- Add regression tests for every behaviour change.
- For releases, run the packaged no-radio smoke test and verify ZIP contents.
- Preserve unrelated operator configuration and existing releases.
