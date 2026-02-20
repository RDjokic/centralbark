# Central Bark Dashboard — Master Reference

## Files
| File | Purpose |
|---|---|
| `update_dashboard.py` | Main script — run this daily |
| `labor_input.html` | Open in browser to enter weekly labor $ |
| `DASHBOARD_README.md` | This file |

## Daily Workflow
1. Open `labor_input.html` → enter labor $ → click Save → move `labor_data.json` to CentralBark folder
2. Run: `python3 ~/Desktop/CentralBark/update_dashboard.py`
3. Push to GitHub: `cd ~/Desktop/CentralBark && git add -A && git commit -m "daily update" && git push`

## Dashboard URLs
| Role | URL | PIN |
|---|---|---|
| Owner | rdjokic.github.io/centralbark | (your PIN) |
| DM | rdjokic.github.io/centralbark/dm.html | (your PIN) |
| Wauwatosa GM | rdjokic.github.io/centralbark/gm-wauwatosa.html | (your PIN) |
| Milwaukee Downtown GM | rdjokic.github.io/centralbark/gm-milwaukee-downtown.html | (your PIN) |
| Grayslake GM | rdjokic.github.io/centralbark/gm-grayslake.html | (your PIN) |
| Milwaukee Eastside GM | rdjokic.github.io/centralbark/gm-milwaukee-eastside.html | (your PIN) |
| Mequon GM | rdjokic.github.io/centralbark/gm-mequon.html | (your PIN) |

## Capacity Config
| Location | Daycare Max | Boarding Max | SNP/DNP |
|---|---|---|---|
| Wauwatosa | 125 | 125 | 7 |
| Milwaukee Downtown | 100 | 100 | 8 |
| Grayslake | 105 | 105 | 9 |
| Milwaukee Eastside | 100 | 100 | 10 |
| Mequon | 115 | 115 | 6 |

## What's Tracked
**Executive View**
- Revenue WTD per location (with vs last week, vs last year)
- Unpaid balances
- Q1 bonus progress
- Labor % (color coded: green ≤30%, yellow ≤35%, red >35%)
- Today's capacity utilization — Daycare / Boarding / SNP/DNP

**Full Detail View**
- All of the above plus full labor $ breakdown table

**GM View**
- Per-location card with revenue, boarding, clients, retail, labor %, Q1 bonus

## Next Up (TODO)
- [ ] Set up GitHub Actions for automatic daily updates (no Mac needed)
- [ ] Add membership metrics (retention, churn, new member conversion)
- [ ] Add revenue per labor hour
- [ ] Add new client conversion rate
- [ ] Add boarding occupancy % (separate from daycare when data available)

## Keep Mac Awake (temporary until GitHub Actions)
Run in Terminal and leave open:
```bash
caffeinate -i
```
Or: System Settings → Battery → Options → Prevent automatic sleeping when plugged in

