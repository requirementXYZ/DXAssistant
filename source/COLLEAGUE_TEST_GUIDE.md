# DX Assistant V0.12.0 Experimental Multi-Radio Beta

This package is for controlled compatibility testing with radios configured in
OmniRig 1.20. It uses only the OmniRig API and contains no manufacturer CAT
commands. A radio appearing in OmniRig's list does not guarantee that its rig
definition provides every function DX Assistant requires.

## Safety boundary

- DX Assistant never initiates transmission.
- It never writes PTT, Tx, mode, split, routing or power.
- Its only radio writes are VFO A and VFO B frequencies.
- It blocks every tune unless OmniRig reports the radio online, in RX, Split On,
  RX-A/TX-B, with readable and writable A/B frequencies.
- The operator always remains in control.

For the first test, put any amplifier in standby and leave WSJT-X **Enable Tx**
off. Do not test a new radio unattended.

## Before starting

Record the radio model/firmware, exact OmniRig Rig 1 type, OmniRig version,
rig-definition source/date, COM port and baud rate. Configure Rig 1 for the
actual radio profile—do not pretend another model is connected.

Configure WSJT-X UDP reporting to `127.0.0.1:2237`, with **Accept UDP requests**
enabled.

## Read-only compatibility check

1. Start DX Assistant but do not start band searching.
2. Select **Check OmniRig compatibility**.
3. The check reads capabilities and current state only; it performs no tuning.
4. If it reports missing capabilities, stop. Send the exact message and a
   screenshot. WSJT-X monitoring may still be used, but band search is not
   supported by that profile.
5. If it reports a compatible capability set, continue with the controlled live
   check. This result means only that OmniRig advertises the required functions.

## Controlled frequency test

1. Confirm amplifier standby, WSJT-X Enable Tx off, radio RX, Split On and
   receive-A/transmit-B routing.
2. Choose two enabled bands that are safe for the connected antenna.
3. Start monitoring.
4. Select the first band and choose **Monitor selected band now**.
5. Watch the physical radio. Confirm VFO B moves first, then VFO A, both settle
   on the displayed base frequency, and the radio never enters TX.
6. Repeat once for the second band.
7. Start a short two-band search and observe at least two complete hops.
8. Select **Pause search** and confirm no further changes occur.
9. Turn Split off, select Resume, and confirm the tune is blocked with a visible
   Split error. Restore Split manually and resume explicitly.

Stop immediately if the radio transmits, changes mode, changes split/routing,
selects an unexpected VFO, or reports a frequency different from the display.

## Return the evidence

Please return the radio/OmniRig details, compatibility result, B-then-A result,
Split-off interlock result, approximate time, any exact error text, and the
matching `events-YYYY-MM-DD.jsonl` file from **Diagnostics > Open log folder**.
Do not send the general decode CSV unless needed; it may contain unrelated calls.
