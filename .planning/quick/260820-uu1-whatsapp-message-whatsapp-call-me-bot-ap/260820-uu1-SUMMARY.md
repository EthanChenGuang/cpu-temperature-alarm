---
phase: 260820-uu1-whatsapp-message-whatsapp-call-me-bot-ap
plan: 01
subsystem: alerts
tags: [whatsapp, settings, callmebot, config, tkinter]

requires:
  - phase: 03-tray-ui-settings
    provides: Settings dialog Sound alerts checkbox pattern and FakeTk tests
provides:
  - AppConfig.whatsapp_alerts_enabled default True
  - AlertEngine idle skip of WhatsApp send/cooldown notices
  - Settings WhatsApp message checkbox with credential field hide/show
  - --test-whatsapp idle fail-closed without HTTP
affects: [alerts, settings, config]

actuals:
  tokens: 18418
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - Config idle flag default True so omitted keys keep current sending
    - Tk grid_remove hides credential widgets without destroying StringVars

key-files:
  created:
    - tests/test_settings_whatsapp.py
  modified:
    - src/config/schema.py
    - src/alerts/engine.py
    - src/ui/settings.py
    - src/main.py
    - config/config.example.json
    - tests/test_alerts.py
    - tests/test_settings_sound.py
    - tests/test_settings_api_key.py
    - tests/test_settings_autostart.py
    - tests/test_tray.py
    - tests/test_main.py

key-decisions:
  - "Idle lives on AppConfig/AlertEngine, not CallMeBotClient.is_configured, so credentials stay configured"
  - "whatsapp_alerts_enabled defaults True so shipped configs without the key keep sending"
  - "Hidden fields use grid_remove; Save still reads StringVars and preserves an empty-masked API key"

patterns-established:
  - "Independent alert-channel checkboxes (Sound vs WhatsApp) with gray hints"
  - "Hide-not-destroy for secret fields so save-preserve cannot wipe keys"

requirements-completed: [QUICK-WA-01]

coverage:
  - id: D1
    description: Config flag defaults True when omitted and serializes through config_to_dict
    requirement: QUICK-WA-01
    verification:
      - kind: unit
        ref: tests/test_alerts.py#test_whatsapp_alerts_enabled_defaults_true_when_omitted
        status: pass
    human_judgment: false
  - id: D2
    description: AlertEngine skips WhatsApp send when idle while sound still beeps and state is ALERTING
    requirement: QUICK-WA-01
    verification:
      - kind: unit
        ref: tests/test_alerts.py#test_whatsapp_alerts_disabled_skips_send
        status: pass
      - kind: unit
        ref: tests/test_alerts.py#test_alert_tracer_peak_crossing_starts_beep_and_sends_whatsapp
        status: pass
    human_judgment: false
  - id: D3
    description: Settings WhatsApp message checkbox saves the flag and preserves phone/API key when off
    requirement: QUICK-WA-01
    verification:
      - kind: unit
        ref: tests/test_settings_whatsapp.py#test_settings_dialog_renders_whatsapp_message_checkbox
        status: pass
      - kind: unit
        ref: tests/test_settings_whatsapp.py#test_settings_save_persists_whatsapp_alerts_enabled_false
        status: pass
    human_judgment: false
  - id: D4
    description: Credential fields hide via grid_remove and reappear with the same StringVar values
    requirement: QUICK-WA-01
    verification:
      - kind: unit
        ref: tests/test_settings_whatsapp.py#test_settings_hides_credential_fields_when_whatsapp_idle
        status: pass
      - kind: unit
        ref: tests/test_settings_whatsapp.py#test_settings_toggle_shows_and_hides_fields_without_clearing_vars
        status: pass
    human_judgment: false
  - id: D5
    description: --test-whatsapp returns FAIL without calling send_alert when WhatsApp is idle
    requirement: QUICK-WA-01
    verification:
      - kind: unit
        ref: tests/test_main.py#test_test_whatsapp_idle_skips_send
        status: pass
    human_judgment: false

duration: 6min
completed: 2026-08-20
status: complete
---

# Phase 260820-uu1 Plan 01: WhatsApp message idle toggle Summary

**Settings WhatsApp message checkbox idles CallMeBot sends without wiping phone or API key, defaulting on so existing configs keep alerting**

## Performance

- **Duration:** 6 min
- **Started:** 2026-08-20T20:17:23Z
- **Completed:** 2026-08-20T20:23:15Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments

- Added `whatsapp_alerts_enabled` (default True) through schema load/save so omitted keys keep sending
- Gated AlertEngine WhatsApp send, unconfigured warning, cooldown notices, and cooldown state on that flag; sound/toast/mute stay independent
- Settings shows a WhatsApp message checkbox above phone and API key; off hides those fields via `grid_remove` and still writes the stored credentials
- `--test-whatsapp` writes a FAIL idle result and skips HTTP when the flag is false

## Task Commits

Each task was committed atomically (TDD RED then GREEN):

1. **Task 1 RED: failing idle-flag tests** - `62721d5` (test)
2. **Task 1 GREEN: flag, engine skip, Settings checkbox** - `0c7c40b` (feat)
3. **Task 2 RED: failing hide/preserve/idle-CLI tests** - `38df92f` (test)
4. **Task 2 GREEN: hide fields, example config, idle CLI** - `1d8f1fe` (feat)

**Plan metadata:** skipped (orchestrator commits SUMMARY)

## Files Created/Modified

- `src/config/schema.py` - `whatsapp_alerts_enabled` default True in AppConfig, defaults dict, from_dict, to_dict
- `src/alerts/engine.py` - skip WhatsApp send/notices/cooldown state when idle
- `src/ui/settings.py` - checkbox, credential frame show/hide, persist flag without wiping keys
- `src/main.py` - `_test_whatsapp` fail-closed when idle
- `config/config.example.json` - documents `whatsapp_alerts_enabled: true`
- `tests/test_settings_whatsapp.py` - FakeTk checkbox, hide/show, save-preserve
- `tests/test_alerts.py` - default True + idle skip engine cases
- `tests/test_main.py` - idle CLI skip
- `tests/test_settings_sound.py` / `test_settings_api_key.py` / `test_settings_autostart.py` / `test_tray.py` - FakeFrame `grid_remove`

## Decisions Made

- Idle is a config/engine concern; `CallMeBotClient.is_configured` is unchanged so saved credentials remain valid
- Missing `whatsapp_alerts_enabled` merges to True so current WhatsApp sending is unchanged
- Hide uses `grid_remove` rather than destroying widgets so StringVars (and empty-API-key preserve) still work on Save
- Tray poll already reloads config each cycle; no `src/ui/tray.py` change

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Autostart checkbox count broke after adding WhatsApp checkbox**
- **Found during:** Task 2 verification
- **Issue:** `test_settings_dialog_renders_autostart_checkbox` asserted exactly 2 Checkbuttons (Sound + Autostart)
- **Fix:** Assert `>= 2` and still select Autostart by label
- **Files modified:** tests/test_settings_autostart.py
- **Verification:** pytest tests/test_settings_autostart.py passed
- **Committed in:** 1d8f1fe (Task 2)

**2. [Rule 2 - Missing Critical] Idle CLI test lived in test_main.py**
- **Found during:** Task 2 TDD
- **Issue:** Plan `<files>` omitted `tests/test_main.py` but `<verify>` and `_test_whatsapp` behavior require it
- **Fix:** Added `test_test_whatsapp_idle_skips_send`
- **Files modified:** tests/test_main.py
- **Verification:** pytest tests/test_main.py::test_test_whatsapp_idle_skips_send passed
- **Committed in:** 38df92f (Task 2 RED)

### Other notes

Working tree was already dirty. Staging only plan-listed files still included pre-existing uncommitted work already in those files (sound/mute/beep fields, previously untracked FakeTk settings tests). Unrelated dirty files were left unstaged.

WhatsApp hint text `(off = idle; credentials kept)` was applied with the Task 1 checkbox because Task 1 required a gray hint; Task 2 specified the wording.

---

**Total deviations:** 2 auto-fixed (1 bug, 1 missing test file) plus dirty-tree staging note
**Impact on plan:** No scope creep; idle toggle matches the plan truths.

## Issues Encountered

None beyond the autostart count assertion and dirty working tree.

## User Setup Required

None - no external service configuration required. CallMeBot credentials already in Settings are kept when the new checkbox is off.

## Next Phase Readiness

- Toggle is hot-reloaded by the existing tray poll `load_config` + `engine.update_config` path
- Live Windows Settings/CallMeBot check remains a deferred hardware verification item

## Self-Check: PASSED

All listed source/test files exist; commits `62721d5`, `0c7c40b`, `38df92f`, `1d8f1fe` are in git log.

---
*Phase: 260820-uu1-whatsapp-message-whatsapp-call-me-bot-ap*
*Completed: 2026-08-20*
