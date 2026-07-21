# DX Assistant V0.12.0 Experimental Multi-Radio Beta

This Beta adds capability-gated OmniRig support so colleagues can evaluate
different radios without DX Assistant containing a Yaesu model-name check.
The core safety boundary is unchanged: DX Assistant never keys the transmitter
and never sets radio mode, split, power, or PTT.

## Start the dashboard

1. Configure WSJT-X UDP messages for `127.0.0.1:2237`.
2. Edit `config.json` and set the target callsign.
3. Double-click `Start-DXAssistant.cmd`, or run `python main.py`.
4. Select **Start monitoring**.

The portable Windows build starts with `DXAssistant.exe` and does not require a
separate Python installation. Alternatively, run the supplied Setup executable
to install DX Assistant for the current Windows user with Start Menu and optional
desktop shortcuts. Keep `config.json` beside the portable executable so the
locator, PSK distance, enabled antenna bands, operating frequencies, and
per-band drive reference can be saved. OmniRig 1.20
remains a separate prerequisite and must have Rig 1 configured correctly.

Once WSJT-X status is visible, choose a dwell time in the **Band search** panel
and select **Start band search**. This explicit second action enables receive-
frequency hopping through the session-enabled bands. The default dwell is 120
seconds.

To test another callsign, select **Stop**, then **Change target**, enter the
active callsign, and select **Start monitoring** again. The selected callsign is
saved immediately and becomes the target at the next launch.

## Diagnostics, alarms and audit history

Choose **Diagnostics** to see the current version, target, WSJT-X connection,
band-search and PSK Reporter state, configuration/log paths, and audit-log health.
The window can test the local alert sound and open the log folder.

**Mute 15 min** temporarily suppresses audible target bells. Visual target
alerts, band-search hold, retained target decodes and acknowledgement behaviour
continue normally. The mute ends automatically after 15 minutes.

Daily decode CSV files remain available. DX Assistant additionally writes append-only
UTC `events-YYYY-MM-DD.jsonl` files containing state changes, operator actions,
tuning attempts and results, target events, WSJT-X preparation and failures. If
the log folder is temporarily unavailable, up to 250 audit records are buffered
in memory and flushed after writing recovers; Diagnostics shows that condition.

The band frequencies shown in the left panel are the saved operating plan.
While stopped, select a band and choose **Edit frequency** to enter a
DXpedition's non-standard receive frequency. Choose **Enable / disable** to
match the connected antenna. Both choices persist across restarts. Disabled
bands are visually muted and excluded from band hopping; non-standard
frequencies are shown in red. Choose **Restore frequencies** to restore the
standard FT8 frequencies without changing the saved antenna band selection.
Frequencies use three decimal places in MHz (1 kHz resolution).

The row matching WSJT-X's current dial frequency is highlighted in green, with
a larger current-band indication beneath the list. If that band is disabled or
not present in the session plan, the indication changes to an amber warning.
The same panel shows WSJT-X's current Tx audio offset as a read-only value. The
offset is not added to VFO B: WSJT-X combines its audio offset with the dial
frequency and manages split-frequency translation when required.

**Edit max drive** stores a persistent 5-100 W safety-profile value for the
selected band. In this Beta the value is display/configuration only: it is
not sent to the radio. CAT access is restricted to verified VFO A/B
frequency alignment; the application has no PTT, mode, split, or power path.
The supplied profile uses maximums of 32 W on 40m; 35 W on 30m, 20m, and 17m;
25 W on 15m; and 22 W on 12m and 10m. A manually selected 22 W radio setting is
therefore within every configured ceiling. Because OmniRig does not expose the
actual power through the OmniRig API used here, the operator remains
responsible for confirming that setting on the radio.

## PSK Reporter band focus

While monitoring is active, DX Assistant retrieves recent FT8 reception reports
for the target from PSK Reporter once every five minutes. The **Area** controls
accept your current Maidenhead locator and a 500, 1,000, 1,500, 2,500, or 5,000
km distance. Select **Apply** after travelling or changing the area; the choice
is saved for future sessions and a fresh query is requested. The supplied
default is JO03 and 2,500 km.

Reports inside the selected area are counted once per receiving station on each
band, then ranked using receiver proximity and report recency. The display says,
for example, **20m: 337 receivers**. Frequencies identify only the amateur band;
reported dial or audio differences are ignored.

When enabled bands have suitable reports, the **PSK Reporter** panel shows them
in priority order with the number of nearby receivers. The search then dwells
only on those focused bands until a target is decoded or a later five-minute
update changes the evidence. A new focus takes effect at the next dwell boundary,
avoiding a mid-slot hop. With a single focused band, the dwell restarts without
repeatedly retuning the radio.

If there are no suitable reports, PSK Reporter is unavailable, or the feature is
disabled in `config.json`, DX Assistant automatically retains the full enabled-
band round-robin sweep. PSK Reporter cannot control the radio; HTTP access is
confined to its dedicated read-only retrieval module. The public service is never
queried more frequently than its requested five-minute interval.

When a target is first decoded, DX Assistant rings the local bell, raises its
window without changing its snapped/maximized layout, and enters **Target
decoded** state. Further decodes accumulate without repeatedly moving the
window until the alert has been acknowledged. **Acknowledge target alert** clears that
notification and returns the state to **Monitoring**. It does not delete the
decode, reset counts, stop monitoring, or control the radio; a later target
decode raises a new alert.

## Prepare the detected DX in WSJT-X

In WSJT-X, first enable **Settings > Reporting > Accept UDP requests**. You may
also select **Accepted UDP request restores window** if that is convenient.
When monitoring receives its first safe WSJT-X Status packet, DX Assistant sends
one official Configure request to the exact WSJT-X instance supplying those
packets. This immediately replaces the previous **DX Call** with the selected
target and asks WSJT-X to generate standard messages; it does not wait for the
target to be decoded. If WSJT-X reports Enable Tx or an active transmission, the
request remains pending until WSJT-X returns to receive.

**Re-send target to WSJT-X** remains available while a live receive-only Status is
present. After a target decode, selecting it again includes the grid when that
grid was present in the decode. If no grid was decoded, the request leaves
WSJT-X's existing DX grid unchanged.

This button does not select Enable Tx, reply to a decode, set even/odd periods,
or transmit. Check the latest retained target decode to confirm the DX period,
then make the final Enable Tx decision in WSJT-X yourself. DX Assistant has no
EnableTx, HaltTx, PTT, mode, split, or power command path.

## Band-search handover

Each hop requires OmniRig Rig 1 to be online and its selected profile to expose
read/write VFO A and VFO B frequencies plus readable VFO, split, receive and
transmit state. The radio must be in RX, split on, and receive-A/transmit-B
routing. DX Assistant moves VFO B first, then VFO A, and verifies both at the
configured base frequency. It cannot key the transmitter. Use **Check OmniRig
compatibility** before starting a search; this is a read-only check.

A target decode pauses hopping. If WSJT-X Enable Tx is selected, DX Assistant
relinquishes VFO ownership for the whole operating period, including receive
slots between transmissions. Releasing Enable Tx does not restart hopping.
After operating, acknowledge any target alert and select **Resume search**;
both VFOs are then aligned to the next enabled band's base frequency and the
search continues immediately. Repeated target decodes on the acknowledged held
band remain in the target panel but do not keep raising new alerts.

To move immediately to a particular enabled band, select its row and choose
**Monitor selected band now**. This is available while WSJT-X is in receive and
monitoring is active. It safely aligns both VFOs, starts a fresh dwell period on
the selected band, and then continues the normal round-robin search. It can be
used when the search is stopped, paused, or already running.

## Test without the radio

Start the dashboard, select **Start monitoring**, then double-click
`Run-Simulator.cmd`. Alternatively, in a second terminal run:

```powershell
python tools\simulate_wsjtx.py
```

The simulator sends only synthetic UDP test packets to localhost. It waits up to
12 seconds for the automatic Configure-only response and reports whether it was
received. The manual **Re-send target to WSJT-X** button may also be selected during
that period. It does not connect to or control the radio.

## Current boundary

Implemented: dashboard, state machine, heartbeat/status/decode reception,
target alarm, compact rolling activity display, persistent session target-decode
display, band-labelled decode history, daily CSV log, connection timeout, band
display, simulator, guarded OmniRig VFO alignment, selectable dwell, enabled-band
round-robin search, immediate selected-band monitoring, WSJT-X Tx-offset display,
travel-aware PSK Reporter band focus with full-sweep fallback, target hold,
Configure-only WSJT-X DX preparation, and explicit operator-control
handover/resume.

Experimental scope: any radio/profile combination whose OmniRig API advertises
the complete required capability set. A positive check is a candidate result,
not proof of correct rig-profile behaviour; follow `COLLEAGUE_TEST_GUIDE.md`
with the amplifier in standby before relying on band searching. Single-VFO or
active-frequency-only strategies, cluster integration, and transmission remain
outside scope. V0.12 is available as both a portable executable Beta and an
unsigned per-user Windows installer.
