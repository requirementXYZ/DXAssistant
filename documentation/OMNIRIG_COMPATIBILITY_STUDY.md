# OmniRig compatibility study

Date: 20 July 2026

## Conclusion

DX Assistant can be redesigned to support more radios without containing direct
manufacturer CAT commands. It should not, however, claim compatibility with
every radio merely because an OmniRig definition exists.

The sound design is **capability-gated and validation-approved**:

1. ask OmniRig whether each required parameter is readable or writable;
2. select only a tuning strategy whose complete safety contract is available;
3. run a read-only preflight on every startup and before every tune;
4. permit a new RigType only after an operator-controlled bench validation;
5. retain a small approved-profile record for sequence, settling time, tolerance
   and validation evidence.

This removes the hard-coded FTDX101D identity without weakening fail-closed
behaviour. It does not imply universal compatibility.

## What OmniRig provides

OmniRig 1.20 is a COM radio-control engine. Radio-specific CAT commands reside in
external INI definition files, and a new radio can be added by creating another
definition. The official interface exposes:

- `RigType`, online status and Rig 1/Rig 2 selection;
- generic `Freq`, `FreqA`, `FreqB`, `Vfo`, `Split`, `Tx` and `Mode` properties;
- `GetRxFrequency()` and `GetTxFrequency()`;
- `ReadableParams`, `WriteableParams`, `IsParamReadable()` and
  `IsParamWriteable()` capability discovery.

The INI format recognises generic parameters including operating frequency,
independent VFO frequencies, four receive/transmit VFO routes, split on/off and
RX/TX state. The documentation explicitly states that most radios support only a
subset.

Primary references:

- [Official OmniRig product and supported-radio page](https://dxatlas.com/omnirig/)
- [Official COM interface source](https://github.com/VE3NEA/OmniRig/blob/master/OmniRig.ridl)
- [Official rig-description structure](https://dxatlas.com/omnirig/IniStru.txt)
- [Official OmniRig tester guide](https://dxatlas.com/omnirig/BetaTest.txt)
- [Official current INI download](https://dxatlas.com/OmniRig/Files/RigIni.zip)

## Current DX Assistant constraint

The bridge uses only OmniRig properties; it contains no direct Yaesu CAT command
strings. It nevertheless imposes an FTDX101D-specific policy:

- RigType must equal `FTDX101D`;
- OmniRig must report online, RX, split on and RX-A/TX-B;
- both `FreqB` and `FreqA` must be writable and readable;
- the bridge writes B first, then A, waits fixed intervals, and verifies both plus
  `GetRxFrequency()`;
- rollback restores B then A only while the rig still reports RX.

The enum values used for RX, split and VFO routing are OmniRig constants, not
Yaesu constants. The radio-specific assumptions are that a definition implements
those properties correctly and that the B-then-A sequence is safe for that rig.

## Static survey of current definitions

The official INI package dated 25 February 2026 was downloaded and its 171
definition files were inspected without executing any CAT commands.

Static candidate counts:

- 55 definitions contain setters for `pmFreqA` and `pmFreqB` and status parsing
  for both frequencies, `pmVfoAB`, `pmSplitOn` and `pmRx`—the broad shape required
  by the current dual-VFO workflow.
- 89 definitions contain a `pmFreq` setter plus status parsing for `pmFreq` and
  `pmRx`—a possible simpler receive-frequency strategy.
- 99 definitions match at least one of those two static shapes.

Examples in the strict static candidate set include FTDX101D, Elecraft K3,
IC-7300, TS-590 and FT-991 definitions. This does **not** establish operational
compatibility. Static presence cannot prove correct CAT replies, correct VFO
semantics, safe write order, adequate settling time or reliable state reporting.
The official tester guide specifically calls for checking every readable and
writable parameter against the physical radio and notes that definition errors
are likely outside the author's original test radio.

## Recommended architecture

### 1. Capability snapshot

Replace the model-name gate with a read-only snapshot containing:

- OmniRig interface/software version, rig number, RigType and status;
- readable/writable bitmasks;
- explicit booleans for `Freq`, `FreqA`, `FreqB`, `VfoAB`, `SplitOn`,
  `SplitOff`, `Rx` and `Tx`;
- current frequency, VFO routing, split and RX/TX values only when readable.

Never infer support from a non-zero property value. Use OmniRig's capability
methods first, then read the property.

### 2. Tuning strategies

Implement strategies behind one frequency-alignment interface.

**Dual-VFO split strategy**

- Requires readable/writable A and B frequencies.
- Requires readable RX state, split state and explicit VFO routing.
- Requires RX, split on and an approved receive/transmit route.
- Uses an approved write order, per-profile settling times, verification tolerance
  and rollback order.
- Closest to current behaviour and the first recommended generalisation target.

**Active receive-frequency strategy**

- Requires readable/writable generic `Freq` and readable RX state.
- Never changes VFO routing, split, mode or power.
- May be suitable for receiver-only monitoring or rigs where WSJT-X owns split.
- Must remain separately opt-in because writing the active frequency may also
  alter the future transmit frequency. It should not be enabled until its
  handover consequences are deliberately approved.

Do not silently fall back from the dual-VFO strategy to the active-frequency
strategy. The operator must see which contract is active.

### 3. Approved-profile registry

Capability discovery proves only that operations are advertised. Maintain a
small data file keyed by exact RigType with:

- approved strategy;
- required capability bitmasks;
- allowed routing values;
- write and rollback order;
- settling delays and frequency tolerance;
- tested OmniRig/INI version or definition checksum;
- radio/firmware tested and date;
- validation status: experimental, bench-validated or operator-validated.

An unknown RigType may display WSJT-X data and a read-only capability report, but
automatic tuning remains blocked until the operator completes validation and a
profile is approved.

### 4. Compatibility wizard

Provide an explicit, receive-only wizard:

1. Confirm WSJT-X Enable Tx is off and the radio reports RX.
2. Display RigType, OmniRig version and advertised capabilities.
3. Perform read-only consistency checks while the operator changes A/B, split
   and routing at the front panel.
4. With amplifier in standby, ask the operator to approve two harmless test
   frequencies on one band.
5. Exercise the proposed write order and verify every intermediate state.
6. Deliberately test an unsafe condition such as split off and prove tuning is
   blocked.
7. Restore the original state and produce a validation report.

The wizard must never write PTT, Tx, mode, split, routing or power. It may write
only frequencies after explicit operator approval.

### 5. Runtime safety rules

- Re-evaluate capabilities when RigType or OmniRig status changes.
- Re-run all interlocks immediately before each frequency write and after each
  intermediate write.
- Treat unreadable, unknown, stale or contradictory values as blocking.
- Keep WSJT-X transmit status as an additional interlock, not a substitute for
  the radio's RX state.
- Record advertised capabilities, chosen strategy, each write, verification,
  rollback and failure in the event audit log.
- Stop search after any failure; resumption remains an explicit operator action.
- Never add setters for PTT/Tx, mode, split, routing or power.

## Recommended compatibility wording

During initial development:

> DX Assistant uses the OmniRig API and contains no manufacturer CAT commands.
> Automatic band searching is enabled only for radio profiles whose required
> OmniRig capabilities and safety behaviour have been validated by the DX
> Assistant project.

After several profiles are validated:

> Supports validated OmniRig radio profiles that provide the frequency, RX-state,
> split and VFO-routing capabilities required by the selected DX Assistant tuning
> strategy. An OmniRig definition alone does not guarantee compatibility.

Avoid “supports any transceiver supported by OmniRig.” OmniRig itself documents
that radios implement different parameter subsets, and its tester guide requires
hardware verification of each definition.

## Suggested implementation sequence

1. Add capability discovery and a read-only compatibility report, leaving the
   existing FTDX101D gate in force.
2. Refactor the current algorithm into a `dual_vfo_split` strategy with an
   FTDX101D profile and unchanged tests.
3. Add simulated capability-matrix tests for missing, partial, contradictory and
   changing capabilities.
4. Add the receive-only compatibility wizard and validation-report export.
5. Validate one contrasting radio—ideally Elecraft K3, IC-7300, TS-590 or FT-991—
   with its owner before approving that profile.
6. Consider the active-frequency strategy only as a separate later product
   decision.

This staged design broadens the architecture immediately while keeping actual
radio writes limited to evidence-backed profiles.
