# DX Assistant V0.13.1 Beta - 22 July 2026

V0.13.1 removes the reference maximum-power display because DX Assistant cannot
set or verify the radio's RF power.

## Changed in V0.13.1

- Removed the **Max W** column and **Edit max drive** control from the dashboard.
- Removed maximum-power values from the supplied configuration and active
  application model. Legacy `power_watts` entries in an existing `config.json`
  are safely ignored.
- Clarified that safe RF power must be selected and confirmed directly by the
  operator at the radio.
- The receive-only boundary is unchanged; no power-setting command was added.

## Verification

- 86 automated tests pass, including a regression test confirming that legacy
  power values are ignored and no power column or control is presented.

## Included from V0.13.0

V0.13 expanded the operating band plan and improved the main dashboard workflow
without changing the receive-only radio-control boundary.

## Changed in V0.13.0

- Added 160m at 1.840 MHz, 80m at 3.573 MHz and 6m at 50.313 MHz.
- The three new bands are disabled by default and have no assumed maximum-drive
  power setting; older saved configurations gain them without losing existing
  frequencies or antenna selections.
- Added `MHz` to the top monitoring-status frequency value.
- **Change target** is green whenever it is available while stopped.
- **Recent WSJT-X activity** now scrolls upward in chronological order, with the
  latest decode at the bottom and automatically kept visible.
- **Monitor selected band now** clears both the blue row selection and keyboard
  focus after use while preserving the independent green current-band marker.

### V0.13.0 verification

- 87 automated tests pass, including band-plan migration, chronological rolling
  activity, action-state colours, selection/focus cleanup and unchanged static
  transmission-safety checks.

## Included from V0.12.0

DX Assistant V0.12.0 introduced experimental multi-radio capability gating.

## Changed in V0.12.0

V0.12 removes the FTDX101D model-name gate and uses documented OmniRig
capabilities to decide whether configured Rig 1 can participate in the existing
dual-VFO split-safe search workflow.

## Changed in V0.12.0

- No manufacturer-specific CAT commands or radio-model allowlist is present.
- Before every alignment, the bridge requires OmniRig to advertise readable and
  writable VFO A/B frequencies plus readable RX, split and RX-A/TX-B routing.
- Online, RX, Split On and RX-A/TX-B interlocks remain mandatory.
- VFO B is aligned and verified first, followed by VFO A and final receive-
  frequency verification; rollback remains RX-gated.
- **Check OmniRig compatibility** performs a read-only capability check and
  reports the exact RigType and missing capabilities without tuning.
- Diagnostics includes the latest compatibility result.
- Maximum-drive wording is radio-neutral and remains display/reference only.
- A dedicated colleague test guide is included in both distributions.

This is an experimental compatibility release. An OmniRig definition advertising
the required functions is a test candidate, not proof that its physical radio
implements those functions correctly.

## Verification

- 85 automated tests pass, including model-independent capability parsing,
  incomplete-profile reporting, UI diagnostics and unchanged static safety
  boundaries.

## Included from V0.11.0

This release closes the applicable conversation-to-development gaps while
retaining the established receive-only safety boundary.

## Changed in V0.11.0

- The last callsign selected with **Change target** is saved and restored on the
  next launch.
- A new append-only UTC JSON Lines audit log records application state changes,
  operator actions, WSJT-X preparation, target events, tuning requests/results,
  PSK Reporter failures, and errors alongside the existing decode CSV files.
- Audit writes fail safely: up to 250 records are retained in memory and flushed
  when the log directory becomes writable again.
- **Diagnostics** shows the application, connection, search, PSK Reporter,
  configuration and logging state, and provides alarm-test and open-log actions.
- **Mute 15 min** suppresses audible bells temporarily without hiding visual
  target alerts.
- An unsigned per-user Windows installer is supplied in addition to the portable
  ZIP. It creates Start Menu and optional desktop shortcuts, does not require
  administrator rights, and preserves `config.json` during upgrade/uninstall.
- PSK Reporter is the sole approved external evidence source. Cluster integration
  is formally outside the V0.11/V1 scope.
- FTDX101D remains the sole approved CAT profile. Other radio profiles are
  formally outside the current scope pending a future product decision and
  safety validation.

## Verification

- 81 automated tests pass, including audit-log buffering/flush, dashboard audit
  integration, muted-alarm visual behaviour, persistent target selection, and
  the unchanged transmission-safety boundary.

## Included from V0.10.0

This release concentrates on operating clarity, durable band-plan settings,
and preserving the operator's desktop layout when a target is found.

## Changed in V0.10.0

- Enabled/disabled antenna bands now persist in `config.json` across restarts.
- Edited DXpedition frequencies now persist across restarts and are displayed
  in red whenever they differ from the standard FT8 frequency.
- **Restore frequencies** restores only the standard FT8 frequencies and keeps
  the saved antenna band selection unchanged.
- Primary controls use consistent action colours: green for start/resume, amber
  for stop/pause/acknowledge and available stopped-only configuration, and grey
  when unavailable. Labels and enabled states remain explicit.
- **Prepare DX in WSJT-X** is renamed **Re-send target to WSJT-X** because the
  selected target is already sent automatically at the start of monitoring.
- OmniRig interlock failures remain visible in the Band search panel instead of
  being overwritten by the next WSJT-X heartbeat.
- A target alert no longer changes a visible snapped or maximized window into a
  restored floating window. The window is restored only if minimized.
- Repeated target decodes accumulate without repeatedly ringing or raising the
  window until the current alert is acknowledged.

## Included from V0.9.0

- First portable Windows executable build; Python is bundled and is not a user
  prerequisite.
- Editable `config.json` remains beside the executable, while the frequency-only
  OmniRig PowerShell bridge is bundled as an internal application resource.
- Packaged `--smoke-test` verifies configuration and bridge availability without
  opening the dashboard, binding UDP, or accessing the radio.

- Windows desktop dashboard built with the Python standard library.
- Explicit Stopped, Starting, Monitoring, Target Decoded, Degraded, and Error
  states.
- Start, Stop, Acknowledge target alert, and Clear displays controls.
- WSJT-X connection, frequency, mode, decode count, and target count displays.
- Enabled-band and configured-frequency display.
- Live decode table with target highlighting.
- Heartbeat timeout and automatic recovery.
- Safe localhost WSJT-X simulator for bench testing.
- FT8 sender-role parsing, so a target merely being called is not reported as
  locally heard.
- Session target selection from the dashboard while monitoring is stopped.
- Compact rolling view limited to the latest 12 general decodes.
- Separate target-decode panel that retains target messages for the session.
- Band label on every displayed and logged decode, derived from the live WSJT-X
  dial frequency in preparation for band hopping.
- Per-band persistent frequency overrides for non-standard DXpedition operating
  frequencies, with amateur-band validation and one-click default restoration.
- Individual persistent band enable/disable controls to represent the connected
  antenna's capabilities, with disabled bands visually muted.
- Simplified three-decimal MHz frequency entry and display, rounded to 1 kHz.
- Three-decimal frequency in the top monitoring status.
- Persistent per-band FTDX101D maximum-drive safety profile (5-100 W), clearly
  configuration-only with no radio power command path in this release.
- Operator-supplied amplifier-safe maximum-drive profile: 40m 32 W; 30m, 20m,
  and 17m 35 W; 15m 25 W; 12m and 10m 22 W.
- OmniRig operating note: leaving the radio manually set to 22 W is within
  every configured band ceiling. DX Assistant neither sets nor verifies the
  radio's actual power in this release.
- Live WSJT-X status now highlights the current row in the session band plan
  and shows a larger current-band indicator beneath the list.
- A current band that is disabled or absent from the session plan is shown as
  an amber warning rather than as an enabled band.
- Renamed the alarm button to **Acknowledge target alert** to make clear that
  it resets the local notification while monitoring and decode retention continue.
- Deliberately separate **Start band search** control; ordinary WSJT-X monitoring
  remains available without CAT frequency changes.
- OmniRig Rig 1 frequency-only bridge proven with the installed FTDX101D profile.
- Split-safe hop sequence aligns inactive VFO B first and receiving VFO A second,
  then verifies both VFOs and the receive frequency.
- Hard interlocks require FTDX101D online, radio RX, split on, and RX-A/TX-B
  routing before every frequency alignment.
- Selectable 60, 90, 120, 180, 240, or 300 second dwell, defaulting to 120
  seconds, with a live countdown.
- Round-robin hopping includes only session-enabled antenna bands and uses each
  band's session frequency override.
- Target detection immediately enters **Target hold** and stops future hops.
- WSJT-X Enable Tx or transmitting status immediately hands VFO ownership to
  the operator; search resumes only after TX is inactive, the target alert is
  acknowledged, and **Resume search** is explicitly selected.
- Resume realigns both VFOs to the current band's configured base frequency
  before restarting the dwell timer.
- Acknowledging a target alert now suppresses repeat bells and holds from the
  same target on that held band, while continuing to retain every target decode.
- **Resume search** now moves directly to the next enabled band instead of
  repeating a full dwell on the band that just produced the target alert.
- Read-only **WSJT-X Tx offset** display, decoded from the official Status
  message. This does not alter VFO B or attempt to control WSJT-X's Tx audio.
- **Monitor selected band now** moves immediately to any selected enabled band
  while monitoring in receive, starts a fresh dwell, and then continues the
  normal round-robin search.
- Band-plan selection is cleared after enable/disable so the blue selection
  highlight no longer remains on the last changed row.
- PSK Reporter retrieval for the target callsign, limited to FT8 reports from
  the most recent 30 minutes and polled no more often than once every five minutes.
- JO03-aware ranking retains reports from receivers within 2,500 km, deduplicates
  repeated reports from each receiver on a band, and scores bands by proximity
  and recency.
- Reported frequencies are classified by amateur band only; exact dial and audio
  offsets do not influence the search frequency.
- Search focus follows the ranked, session-enabled reported bands. A new focus
  begins at the next dwell boundary so a decode interval is never cut short.
- Automatic full enabled-band sweep whenever there are no suitable reports or
  PSK Reporter is unavailable.
- Dedicated PSK Reporter status panel shows focused bands and nearby receiver
  counts without exposing any radio controls to the network component.
- Compact two-column band-plan controls and a verified default-window layout keep
  all controls visible with the new status panel.
- Editable station locator and selectable 500, 1,000, 1,500, 2,500, or 5,000 km
  PSK Reporter search distance, persisted for operation from other locations.
- Applying a new PSK search area clears stale priorities and requests a fresh
  poll; results arriving for an older area are discarded.
- Clear PSK status wording identifies counts as distinct receiving stations.
- WSJT-X preparation uses only the official Configure message. It populates DX
  Call and asks WSJT-X to generate standard messages; preparing again after a
  decode also includes the decoded grid when available.
- The preparation request mirrors current WSJT-X mode/timing parameters and is
  returned only to the exact live WSJT-X UDP endpoint that supplied Status.
- Even/odd selection deliberately remains under operator control; the retained
  target-decode panel provides the current evidence before Enable Tx is chosen.
- A newly selected target is now prepared automatically on the first live,
  receive-only WSJT-X Status packet after monitoring starts, so WSJT-X no longer
  continues to display the previous target while the search begins.
- Target preparation no longer requires a local decode. The manual button is
  available whenever WSJT-X Status is live and transmit is inactive.
- Automatic preparation remains pending while WSJT-X reports Enable Tx or an
  active transmission, and is sent only after WSJT-X returns to receive.

## Safety

The production package contains no PTT, EnableTx, HaltTx, Reply, radio-mode,
split, or power-setting code. Its only outbound WSJT-X message is Configure(15),
used to prepare DX Call/Grid and generate messages without enabling transmit.
Its OmniRig bridge can write only VFO A and VFO B frequencies, and blocks all
tuning unless the radio reports RX with the expected split routing. The
simulator remains isolated under `tools` and sends synthetic localhost packets
only when the operator starts it manually.

## Verification

- 76 automated tests pass, including persistent band-plan settings,
  non-standard-frequency indication, action-state colours, persistent OmniRig
  error detail, visible-window geometry protection, repeated-alert suppression,
  frozen-path and no-radio packaged smoke
  checks, pre-decode target preparation, transmit-
  state deferral, Configure-only packet construction and a
  real localhost request/response test, travel-area validation and persistence,
  target-grid extraction, PSK Reporter XML/gzip parsing, Maidenhead
  distance calculation, nearby-receiver deduplication and ranking, band-only
  frequency classification, service-failure fallback, search-focus ordering,
  network-module confinement, default-window layout,
  Tx-offset protocol/display compatibility,
  immediate selected-band monitoring, selection-highlight cleanup,
  repeated-target acknowledgement suppression,
  next-band resume, hopping state/round-robin timing, target
  hold, Enable-Tx ownership handover, OmniRig result/error handling, the
  frequency-only bridge boundary, sender-role parsing, current-band highlighting,
  disabled-current-band warnings, band derivation, antenna band-plan controls,
  drive-profile persistence, session-frequency validation, dashboard construction,
  target selection, and target-alarm acknowledgement.
- A real localhost UDP receive-path test passes.
- Python byte-compilation passes.
