# Central Bark Dashboard — Master Reference
Last updated: February 19, 2026 (v6)

---

## 1. MoeGo API Credentials

**API Key (Base64):**
```
NWY2YmFkNWUtNmE5ZC00MmNlLTk5YzctZWY5OGY1ZjlkMjM3
```
**Base URL:** `https://openapi.moego.pet`
**Auth header:** `Authorization: Basic NWY2YmFkNWUtNmE5ZC00MmNlLTk5YzctZWY5OGY1ZjlkMjM3`

---

## 2. Location IDs

| Location | Company ID | Business ID |
|---|---|---|
| Wauwatosa | copyXor | bizkVbJ |
| Milwaukee Downtown | copy05r | biz1wNe |
| Grayslake | copn7Fd | bizkJLJ |
| Milwaukee Eastside | copqRWC | bizyYVr |
| Mequon | copoHcj | bizVm0Y |

> **Mequon:** Returns no data until Monday Feb 23, 2026. Update `ly_full` in BONUS_TARGETS once Q1 2025 data is confirmed.

---

## 3. Automation — Fully Set Up

### Script Location
```
~/Desktop/CentralBark/update_dashboard.py
```

### Schedule
- Runs automatically every night at **7:30pm** via macOS launchd
- Mac sleep prevention is on in System Settings → Battery

### Output Files
- **Mac Desktop:** `~/Desktop/central_bark_dashboard.html`
- **iPhone (Files app):** iCloud Drive → `central_bark_dashboard.html`
- **Log file:** `~/Desktop/central_bark_dashboard.log`

### To Run Manually
```bash
python3 ~/Desktop/CentralBark/update_dashboard.py
```

### To Check Last Run
```bash
cat ~/Desktop/central_bark_dashboard.log
```

### To Reload Schedule (if ever needed)
```bash
launchctl unload ~/Library/LaunchAgents/com.centralbark.dashboard.plist
launchctl load ~/Library/LaunchAgents/com.centralbark.dashboard.plist
```

### Expected Run Time
- ~2-3 minutes (pulls today's data + daily scorecard benchmarks)

---

## 4. Dashboard Structure (v6 — 3 Tabs)

### Tab 1: Executive View
1. **Alert banner** — unpaid balance warning or all-clear
2. **Summary bar** — Week Expected, Unpaid, Daycare Dogs, Boarding Dogs, Grooming Appts, Retail WTD
3. **Location cards (5)** — Revenue WTD, vs last week %, YTD vs LY %, unpaid, retail, Q1 bonus progress
4. **Today vs Benchmarks** — Per location: Daycare / Boarding / Grooming / Retail today vs:
   - Same day last week
   - Same day last month
   - Same day last year (closest same weekday)
   - Last 5 same-days-of-week average (e.g. last 5 Thursdays)

### Tab 2: Full Detail
1. Daily Revenue by Service Type (Memberships/Grooming/Boarding/Daycare)
2. Daily Dog & Appointment Counts — 7-day grid × location × service
3. Unpaid Balances — Expected vs Collected vs Unpaid vs Tips
4. Q1 2026 GM Bonus Tracker
5. YTD Sales vs Last Year
6. Week over Week Revenue
7. Retail Sales — daily + top 10 items
8. New vs Returning Clients
9. Boarding Occupancy

### Tab 3: GM View
- Per-location cards with: Revenue WTD, vs last week, YTD vs LY, unpaid, clients, boarding, retail
- Q1 bonus progress bar with pace/gap/days remaining
- Top 3 retail items
- Status badge: Ahead / On Pace / Behind

---

## 5. GM Bonus Tracker Config

| Location | Q1 2025 Full | Bonus % | Q1 2026 Target |
|---|---|---|---|
| Wauwatosa | $404,791.49 | 7% | $433,126.89 |
| Milwaukee Downtown | $212,902.65 | 7% | $227,805.84 |
| Grayslake | $287,057.97 | 10% | $315,763.77 |
| Milwaukee Eastside | $255,660.02 | 7% | $273,556.22 |
| Mequon | $0.00 | 10% | Starts Q2 |

**Q1 2026 QTD (through Feb 19):**
- Wauwatosa: $230,275.63 (53.2% to target)
- Milwaukee Downtown: $126,564.17 (55.6% to target)
- Grayslake: $164,713.32 (52.2% to target)
- Milwaukee Eastside: $149,226.45 (54.6% to target)

> All 4 active locations are ahead of last year's same-day pace!

---

## 6. Critical Data Notes

- **"Non-service sales"** = weekly membership billing — hits every Monday
- **Monday revenue spike is normal**
- **Revenue based on sale date** not appointment date
- **Week = Sunday–Saturday**
- **Money format:** `units` + `nanos` / 1,000,000,000
- **Boarding nights field:** stored as `int64` not `number`
- **Appointment dates:** return as `timestamp` format (`2026-02-18T00:00:00Z`) — parse as `ts[5:7]/ts[8:10]/ts[:4]`
- **Pagination required** for Wauwatosa daycare (585+ records)
- **Mac Terminal = /bin/sh** — always use Python scripts, not heredocs
- **Week over week:** compares same completed days only (apples to apples)
- **Client summary:** paginate and sum `new_clients_count` + `uniq_serviced_clients`
- **Bonus tracker:** pulls LY same days dynamically each run using `today.replace(year=2025)`
- **Daily scorecard avg:** averages last 5 of the same day-of-week (e.g. last 5 Thursdays), not a rolling 30-day average

---

## 7. Available Report IDs

| Report ID | Key Use |
|---|---|
| `reports_sales_summary` | Daily revenue, collected, unpaid, tips |
| `reports_daily_sales` | Revenue by care_type per day |
| `reports_sales_invoice_item` | Retail (Product category) — item-level detail |
| `reports_daycare_appointment_list` | Daycare counts — timestamp date format |
| `reports_boarding_appointment_list` | Boarding dogs + nights (int64) |
| `reports_appointment_list` | Grooming counts |
| `reports_client_summary` | New vs returning clients |
| `reports_staff_performance` | Sales by staff, utilization, rebook rate |
| `reports_package_redeem_v2` | Package redemptions |
| `reports_package_remaining_balance` | Unused package balances |

---

## 8. Location Colors (Dashboard)

| Location | Color |
|---|---|
| Wauwatosa | #f97316 (orange) |
| Milwaukee Downtown | #3b82f6 (blue) |
| Grayslake | #10b981 (green) |
| Milwaukee Eastside | #a855f7 (purple) |
| Mequon | #f59e0b (amber) |

---

## 9. Script Version History

| Version | Lines | Date | Notes |
|---|---|---|---|
| v1 | ~200 | Feb 2026 | Basic revenue + counts |
| v2 | ~350 | Feb 2026 | Added unpaid, tips, clients, boarding |
| v3 | ~467 | Feb 2026 | Added Q1 bonus tracker |
| v4 | ~722 | Feb 2026 | Added retail + YTD pulls |
| v5 | ~770 | Feb 18 | Fixed missing row builders |
| v6 | ~914 | Feb 19 | 3-tab layout + 5th location (Mequon) + daily scorecard |

---

## 10. Outstanding Issues / Backlog

- [ ] **Mequon** — starts reporting Monday Feb 23. Update `ly_full` in BONUS_TARGETS once Q1 2025 data confirmed
- [ ] **Homebase integration** — labor % KPI. Need to confirm API plan (Settings → API Access in Homebase). Requires All-in-One or Enterprise plan.
- [ ] **Staff performance section** — available via `reports_staff_performance` report ID
- [ ] **iPhone home screen shortcut** — Files app preview works for now
- [ ] **MKE Eastside unpaid balance** — follow up with location manager
