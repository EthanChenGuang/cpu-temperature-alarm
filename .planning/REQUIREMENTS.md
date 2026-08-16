# Requirements: CPU High Temperature Alert

**Defined:** 2026-08-16
**Core Value:** The user is reliably warned — audibly and via WhatsApp — before hardware damage occurs from sustained high CPU/GPU temperatures.

## v1 Requirements

### Telemetry

- [x] **TELE-01**: Application reads all CPU temperature sensors via LibreHardwareMonitor every 3 seconds
- [x] **TELE-02**: Application reads all GPU temperature sensors via LibreHardwareMonitor every 3 seconds
- [x] **TELE-03**: Application computes and exposes the maximum current temperature across all CPU and GPU sensors

### Alerting

- [ ] **ALRT-01**: Application triggers continuous local Windows beep while peak temperature exceeds threshold
- [ ] **ALRT-02**: Local beep stops immediately when temperature drops below threshold
- [ ] **ALRT-03**: Application sends WhatsApp message via CallMeBot on first threshold breach (default 85°C)
- [ ] **ALRT-04**: Application re-alerts via WhatsApp immediately when temperature reaches higher tiers (90°C, 95°C)
- [ ] **ALRT-05**: Application suppresses duplicate WhatsApp messages within a 3-minute cooldown window for same tier

### System Tray UI

- [ ] **TRAY-01**: Application displays peak temperature as an integer rendered on the system tray icon
- [ ] **TRAY-02**: Tray icon updates in real time on each poll cycle
- [ ] **TRAY-03**: Right-click menu shows current temperature details for all sensors
- [ ] **TRAY-04**: Right-click menu provides Open Settings and Exit actions

### Configuration

- [ ] **CONF-01**: User can configure WhatsApp phone number in settings
- [ ] **CONF-02**: User can configure CallMeBot API key in settings
- [ ] **CONF-03**: User can configure alarm temperature threshold (°C) in settings
- [ ] **CONF-04**: Settings persist to local config file and reload on restart

### Packaging & Deployment

- [ ] **DEPL-01**: Application packages into standalone Windows `.exe` via PyInstaller
- [ ] **DEPL-02**: Setup script creates Task Scheduler entry for silent autorun on boot with admin privileges
- [ ] **DEPL-03**: Application runs as background system tray process with no console window

## v2 Requirements

Deferred to future release.

### Enhancements

- **ENHN-01**: Configurable alert tier temperatures in settings UI
- **ENHN-02**: Configurable polling interval
- **ENHN-03**: Temperature history log file
- **ENHN-04**: Minimize-to-tray on settings close with validation feedback toast

## Out of Scope

| Feature | Reason |
|---------|--------|
| Linux/macOS support | Windows-only target; winsound and pystray Windows paths |
| Fan speed control | Monitoring/alerting only; hardware repair is out of band |
| Web dashboard | Single-machine local tool |
| Multiple notification channels (email, SMS) | CallMeBot WhatsApp is sufficient for v1 |
| Per-sensor tray icons | Peak temperature only on icon; details in menu |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TELE-01 | Phase 1 | Complete |
| TELE-02 | Phase 1 | Complete |
| TELE-03 | Phase 1 | Complete |
| ALRT-01 | Phase 2 | Pending |
| ALRT-02 | Phase 2 | Pending |
| ALRT-03 | Phase 2 | Pending |
| ALRT-04 | Phase 2 | Pending |
| ALRT-05 | Phase 2 | Pending |
| TRAY-01 | Phase 3 | Pending |
| TRAY-02 | Phase 3 | Pending |
| TRAY-03 | Phase 3 | Pending |
| TRAY-04 | Phase 3 | Pending |
| CONF-01 | Phase 3 | Pending |
| CONF-02 | Phase 3 | Pending |
| CONF-03 | Phase 3 | Pending |
| CONF-04 | Phase 3 | Pending |
| DEPL-01 | Phase 4 | Pending |
| DEPL-02 | Phase 4 | Pending |
| DEPL-03 | Phase 4 | Pending |

**Coverage:**

- v1 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0 ✓

---
*Requirements defined: 2026-08-16*
*Last updated: 2026-08-16 after roadmap creation*
