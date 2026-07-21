# DX Assistant development guide

## Starting point

Always work from:

`C:\Users\g8ajm\Documents\Codex\DX_Assistant\source`

The active source is no longer stored in a folder named after an old preview
release. Historical release folders are read-only references, not development
trees.

## Normal change workflow

1. Confirm the requested behaviour and any live-radio checkpoint.
2. Inspect the active source and preserve the receive-only safety boundary.
3. Implement the smallest complete change in `source/`.
4. Add or update regression tests.
5. Run the full automated suite.
6. Update `PROJECT_STATUS.md` and add a dated `DEVELOPMENT_LOG.md` entry.
7. Update source README/release notes when preparing a package.
8. Build into a fresh versioned directory; never overwrite an older release.
9. Run the packaged no-radio smoke test and verify the archive contents.
10. Record the final test count, package status, and SHA-256 checksum.

## Test command

From `source/`:

```powershell
& 'C:\Users\g8ajm\AppData\Local\Python\pythoncore-3.14-64\python.exe' -m unittest discover -s tests -v
```

Tests must remain safe without a connected radio. A simulator may send synthetic
localhost WSJT-X UDP packets, but automated tests must never key or reconfigure a
live transmitter.

## Packaging notes

- Use a new build directory such as `build/pyinstaller-vX.Y.Z`.
- Build from `source/`.
- Supply an absolute `--add-data` path for
  `source/dxassistant/omnirig_bridge.ps1;dxassistant` because PyInstaller resolves
  data paths relative to the spec-file directory.
- Copy the complete one-directory PyInstaller result into a versioned folder in
  `releases/`.
- Keep `config.json`, README, release notes, manuals, `_internal`, and
  `DXAssistant.exe` together.
- Verify `DXAssistant.exe --smoke-test` before zipping.

## Documentation rules

- `PROJECT_STATUS.md` describes the product as it stands now.
- `DEVELOPMENT_LOG.md` records what changed and why, including verification.
- `source/RELEASE_NOTES.md` describes a specific distributable version.
- User manuals describe only packaged behaviour; do not document an unreleased
  feature as already available.
- Preserve final DOCX and PDF manuals in `documentation/` and include the chosen
  release copy in the portable package.

## Safety review questions

Before accepting any radio-control change, answer:

- Can it initiate or prolong transmission?
- Can it set mode, split, RF power, PTT, Enable Tx, Halt Tx, or a reply action?
- What live state must be verified before any VFO write?
- What happens if WSJT-X and OmniRig disagree?
- Does the operator retain an explicit stop, acknowledgement, and resume choice?
- Can the behaviour be tested without transmitting?
