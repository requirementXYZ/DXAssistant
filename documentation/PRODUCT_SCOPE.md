# DX Assistant product scope

Decision date: 20 July 2026

## Supported product

- External propagation evidence: **PSK Reporter only**.
- Radio/CAT profile: **experimental capability-compatible OmniRig Rig 1
  profiles**. DX Assistant contains no radio-model allow-list.
- Distribution: portable Windows ZIP and unsigned per-user Windows installer.
- WSJT-X outbound control: approved Configure request only.
- OmniRig writes: verified VFO A and VFO B frequency alignment only.

## Formally closed blueprint branches

The older Version 1.0 design blueprint described possible DX Cluster input and
multi-source confidence. These remain outside the approved product scope.
Additional radios may now enter controlled Beta testing only when OmniRig
advertises all required dual-VFO and safety-state capabilities. Capability
discovery is not hardware validation; each profile requires the documented
operator-controlled live safety test.

The following remain explicitly prohibited: PTT, Enable Tx, Halt Tx, Reply,
radio-mode, split-setting and power-setting commands. DX Assistant never
initiates transmission and the operator always remains in control.
