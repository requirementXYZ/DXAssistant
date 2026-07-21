# DX Assistant conversation-to-development gap analysis

Date: 20 July 2026

Resolution update: V0.12.0 Experimental Multi-Radio Beta implements the
capability-gated OmniRig branch requested after V0.11.0.
Operator decisions selected PSK Reporter as the sole evidence source and the
FTDX101D was initially selected as the sole radio profile; V0.12 supersedes that
radio-name restriction with a strict OmniRig capability gate. Cluster branches remain
formally closed in `documentation/PRODUCT_SCOPE.md`, not left as unfinished work.

## Purpose and evidence base

This analysis compares the product intent and operator decisions recorded in the
historical **FTDX101D DX Assistant** Codex task and the Version 1.0 design
specification with the maintained project in `source/`, its automated tests,
project records, and packaged releases.

The conversation record available to Codex is principally one long historical
task containing the successive DX Assistant discussions. The separate WSJT-X /
Log4OM discussion was excluded because it concerns a different logging path and
product. Current implementation claims were checked against source and tests,
not inferred only from conversational statements.

Status terms used below:

- **Released** - present in the V0.10.0 portable package.
- **Development only** - present in `source/` but not in a packaged release.
- **Open gap** - discussed or specified, but not implemented.
- **Deliberately excluded** - considered and intentionally kept outside the
  product boundary; this is not unfinished work.
- **Needs evidence** - code exists, but the stated acceptance evidence is not
  yet recorded.

## Executive conclusion

DX Assistant has delivered the central operating workflow discussed with the
operator: safe WSJT-X monitoring, local target detection, guarded band hopping,
PSK Reporter-assisted focus, clear operator handover, persistent band planning,
Configure-only WSJT-X preparation, and a portable Windows release. The most
important conversation-derived usability corrections through V0.10.0 are also
complete.

V0.11 closes the applicable development gaps: the persistent target is packaged,
an unsigned per-user installer is available, audit logging and diagnostics are
implemented, audible alarms can be tested and temporarily muted, and the older
cluster/multi-radio blueprint branches are formally outside scope. The remaining
work is operator acceptance evidence: the live FTDX101D interruption rehearsal
and recorded eight-hour endurance run.

Transmit automation is intentionally absent and must remain absent. It is a
safety boundary, not a product gap.

## What discussion has already become working product

| Discussed need or decision | Current evidence | Status |
|---|---|---|
| Receive WSJT-X Heartbeat, Status and Decode traffic and match the target only in sender role | Protocol, receiver and engine modules with regression coverage | Released |
| Audible/visible target alert, retained target evidence, acknowledgement separate from search resume | Dashboard state and alert workflow; operator explanation reflected in the manual | Released |
| Operator-enabled band plan, non-standard DXpedition frequencies and immediate selected-band monitoring | Band/config/dashboard modules; persistent settings and regression tests | Released |
| Guarded FTDX101D hopping with RX, split and RX-A/TX-B interlocks | Frequency-only OmniRig bridge; VFO B then VFO A verification | Released |
| Explicit dwell/search control and operator ownership while WSJT-X Enable Tx is active | Hopping state and dashboard handover/resume logic | Released |
| PSK Reporter nearby-receiver focus with safe full-sweep fallback | Dedicated read-only network module and fallback tests | Released |
| Prepare the selected target automatically in WSJT-X, with a manual recovery action | Configure-only UDP path and **Re-send target to WSJT-X** control | Released |
| Meaningful green/amber/grey action cues | Dashboard action styles and regression tests | Released |
| Keep OmniRig failure detail visible | Persistent band-search error state and regression test | Released |
| Preserve snapped/maximized layout and avoid repeated raises for one alert | Window/alert changes and regression tests | Released |
| Persist antenna band enablement and edited frequencies; show non-standard frequencies in red | Atomic configuration saves and regression tests | Released |
| Portable `.exe`, no-radio smoke path, manual and shareable ZIP | V0.10.0 package, smoke/archive checks, DOCX/PDF manual | Released |
| Reopen with the last selected target instead of T22TT | `save_target_call()` and test 77 | **Development only** |

## Open functional and product gaps

| Gap | Origin | Current position | Recommended disposition | Priority |
|---|---|---|---|---:|
| Package persistent last target | Operator request after V0.10.0 | Packaged in V0.11.0 | Complete | Closed |
| FTDX101MP and other OmniRig CAT search support | Colleague trial discussion | V0.12 removes the model gate and adds strict capability discovery plus a controlled test guide | Development complete; physical profile validation remains per radio | Released for experimental test |
| Conventional Windows installer | Beta/installer discussion and V1 roadmap | Unsigned per-user V0.11 installer built and install/smoke/uninstall tested | Complete; operator installation remains | Closed |
| Cluster adapter | V1 design architecture and V0.7 roadmap | Operator selected PSK Reporter-only product scope | Formally outside current scope | Closed |
| Multi-source evidence and explicit search policy | V1 observe/qualify/rank flow | Operator selected PSK Reporter-only evidence; ranked focus, full sweep and immediate manual band selection cover the approved workflow | Formally outside current scope | Closed |
| Expanded alarm controls | V1 interface/alarm catalogue | V0.11 adds alarm test and 15-minute audible mute while preserving visual alerts; target-reported/repeat controls do not apply to the approved local-decode alarm workflow | Complete for approved scope | Closed |
| Settings and diagnostics UI | V1 dashboard/settings design | V0.11 Diagnostics exposes state/log health and open-log/test-alarm actions; stable configuration remains in the proven inline/config controls | Complete for approved scope | Closed |
| Comprehensive event/audit logging | V1 safety and data-record rules | V0.11 writes append-only UTC JSON Lines and buffers up to 250 records across a write failure | Complete | Closed |
| Multiple radio profiles, including Elecraft K3 | OmniRig translation discussion | V0.12 accepts any candidate profile exposing the complete required OmniRig capability set | Live validation remains per radio | Released for experimental test |
| Signing/public distribution | Installer discussion | Operator approved an unsigned private-Beta installer | Outside current scope until distribution changes | Closed |

## Verification and acceptance gaps

| Acceptance statement | Evidence found | Gap |
|---|---|---|
| Complete automated regression suite | 77 tests pass on 20 July 2026 | None for current source baseline |
| Packaged no-radio smoke and archive verification | Recorded for V0.10.0 | Must be repeated for the next package |
| Live FTDX101D operation | Several successful operator reports, including extended/overnight hunting | Useful Beta evidence, but not a structured V1 acceptance record |
| Eight-hour monitoring without data loss | Overnight operation was reported | No recorded start/end evidence or log-integrity audit |
| Recovery from WSJT-X interruption | Timeout/recovery logic and tests exist | A packaged live recovery rehearsal is not recorded |
| Recovery from CAT interruption/uncertain state | Fail-closed interlocks and a real split/routing failure were observed | Recovery matrix is not fully rehearsed or recorded |
| Recovery from internet-source interruption | PSK Reporter failure fallback is tested and observed | Packaged outage/recovery rehearsal is not recorded |
| Cannot initiate transmission | Safety tests and code inspection show Configure-only WSJT-X output and frequency-only OmniRig writes | Preserve and repeat this inspection at every release |

## Discussed items that are not gaps

The following were discussed and deliberately rejected, superseded, or kept
under operator control:

- **Even/odd transmit-period control:** rejected because the WSJT-X Reply path
  could enable transmission depending on WSJT-X settings. The operator uses the
  latest retained decode and chooses the period in WSJT-X.
- **Separate timeslot guidance panel:** explicitly judged unnecessary because
  the decode already contains the needed time evidence.
- **PTT, Enable Tx, Halt Tx, reply, radio mode, split or power setting:** outside
  the approved safety boundary. Maximum-drive figures are reference values only.
- **Automatic restart of tuning after handover:** deliberately rejected; search
  resumes only through an explicit operator action.
- **Removing the manual WSJT-X preparation button:** superseded by keeping it as
  the clearly labelled **Re-send target to WSJT-X** recovery control.
- **Session-only frequency overrides:** superseded by the later operator decision
  to persist them and show non-standard values in red; that later decision is
  implemented.
- **Propagation maps, multiple simultaneous targets, logbook/award integration,
  mobile notifications, collaborative spotting and automated expedition schedule
  ingestion:** explicitly deferred beyond Version 1 in the design specification.

## Recommended next step

Complete `documentation/OPERATOR_ACCEPTANCE_TEST.md`. Development is packaged;
the outstanding evidence requires the operator's live FTDX101D, WSJT-X, OmniRig
and internet environment.

## Current baseline used for this report

- Maintained source: `source/`
- Current packaged release: V0.12.0 Experimental Multi-Radio Beta
- Current source version string: `0.11.0-beta`
- Current source test result: 81 tests passing on 20 July 2026
- Portable release checksum:
  `46B945AD28CC3BADDE5EE99C5B2AE10FD71870AC7D0599EBBAA2FC21C6E1175D`
- Installer checksum:
  `734717202A410A56412BC85A0000D0B016E752E381BCF1F9CE93AA41AF092AEE`
- Live-radio changes or compatibility claims remain operator checkpoints.
