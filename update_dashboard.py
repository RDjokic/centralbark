import os
API  = os.environ.get("MOEGO_API", "NWY2YmFkNWUtNmE5ZC00MmNlLTk5YzctZWY5OGY1ZjlkMjM3")
BASE = "https://openapi.moego.pet"
LOCS = [
    ("Wauwatosa",          "copyXor", "bizkVbJ"),
    ("Milwaukee Downtown", "copy05r", "biz1wNe"),
    ("Grayslake",          "copn7Fd", "bizkJLJ"),
    ("Milwaukee Eastside", "copqRWC", "bizyYVr"),
    ("Mequon",             "copoHcj", "bizVm0Y"),
]

CAPACITY = {
    "Wauwatosa":          {"daycare": 125, "boarding": 125, "snp": 7},
    "Milwaukee Downtown": {"daycare": 100, "boarding": 100, "snp": 8},
    "Grayslake":          {"daycare": 105, "boarding": 105, "snp": 9},
    "Milwaukee Eastside": {"daycare": 100, "boarding": 100, "snp": 10},
    "Mequon":             {"daycare": 115, "boarding": 11, "snp": 6},
}
def cap_pct(actual, cap):
    if cap == 0 or actual == 0: return 0
    return min(actual / cap * 100, 100)
def cap_color(pct):
    if pct == 0:  return "var(--muted)"
    if pct >= 90: return "#dc2626"
    if pct >= 75: return "#d97706"
    return "#16a34a"
def cap_bar_html(pct, actual, cap_val):
    w   = "{:.0f}%".format(pct)
    col = cap_color(pct)
    lbl = str(actual)+"/"+str(cap_val)+" ("+"{:.0f}".format(pct)+"%)"
    return ("<div class=\"cap-bar-wrap\"><div class=\"cap-bar-fill\" style=\"width:"+w+";background:"+col+";\"></div></div>"
            "<div class=\"cap-val\" style=\"color:"+col+"\">"+lbl+"</div>")

from pathlib import Path
# ── LABOR DATA (auto-loaded from labor_data.json) ──────────────────────────────
import json as _json
_labor_file = Path(__file__).parent / "labor_data.json"
if _labor_file.exists():
    _labor_raw = _json.loads(_labor_file.read_text())
    LABOR = _labor_raw.get("labor", {})
    LABOR_TARGET_PCT = _labor_raw.get("target_pct", 0.32)
else:
    LABOR = {}
    LABOR_TARGET_PCT = 0.32

# Ensure all locations have entries
for _loc, _, _ in LOCS:
    if _loc not in LABOR:
        LABOR[_loc] = {"Sun":0,"Mon":0,"Tue":0,"Wed":0,"Thu":0,"Fri":0,"Sat":0}#!/usr/bin/env python3
import json, subprocess
from datetime import datetime, timedelta
from pathlib import Path

# ── LABOR CONFIG (update daily) ───────────────────────────────────────────────
# Enter actual labor $ spent per location per day each week.
# Leave as 0 for days not yet worked or no data.
LABOR_TARGET_PCT = 0.32  # 32% target for all locations

LABOR = {
    "Wauwatosa": {
        "Mon": 0, "Tue": 0, "Wed": 0, "Thu": 0, "Fri": 0, "Sat": 0, "Sun": 0
    },
    "Milwaukee Downtown": {
        "Mon": 0, "Tue": 0, "Wed": 0, "Thu": 0, "Fri": 0, "Sat": 0, "Sun": 0
    },
    "Grayslake": {
        "Mon": 0, "Tue": 0, "Wed": 0, "Thu": 0, "Fri": 0, "Sat": 0, "Sun": 0
    },
    "Milwaukee Eastside": {
        "Mon": 0, "Tue": 0, "Wed": 0, "Thu": 0, "Fri": 0, "Sat": 0, "Sun": 0
    },
    "Mequon": {
        "Mon": 0, "Tue": 0, "Wed": 0, "Thu": 0, "Fri": 0, "Sat": 0, "Sun": 0
    },
}

# PIN PROTECTION
# Each file has its own PIN. Share only the relevant PIN with each person.
PINS = {
    "owner":              "0000",   # change this - your dashboard (index.html)
    "dm":                 "1111",   # change this - district manager (dm.html)
    "Wauwatosa":          "2222",   # change this - Wauwatosa GM
    "Milwaukee Downtown": "3333",   # change this - MKE Downtown GM
    "Grayslake":          "4444",   # change this - Grayslake GM
    "Milwaukee Eastside": "5555",   # change this - MKE Eastside GM
    "Mequon":             "6666",   # change this - Mequon GM
}
OUTPUT  = Path(__file__).parent / "central_bark_dashboard.html"
OUTPUT2 = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "central_bark_dashboard.html"
LOG     = Path(__file__).parent / "central_bark_dashboard.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[" + ts + "] " + msg
    print(line)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def money(rd, key):
    v = rd.get(key, {}).get("value", {}).get("money", {})
    return int(v.get("units", 0)) + v.get("nanos", 0) / 1e9

def fmt(val):
    return "$" + "{:,.2f}".format(val)

def api_post(payload):
    r = subprocess.run(
        ["curl","-s","-X","POST", BASE + "/v1/reports/data:fetch",
         "-H", "Authorization: Basic " + API,
         "-H","Content-Type: application/json",
         "-d", json.dumps(payload)],
        capture_output=True, text=True, timeout=30
    )
    return json.loads(r.stdout)

def fetch_pages(cid, bid, report_id, date_key, start, end):
    all_rows, page = [], "1"
    while True:
        d = api_post({"pagination":{"pageSize":500,"pageToken":page},"companyId":cid,"businessIds":[bid],"condition":{"id":report_id,"queryPeriod":{"startTime":start,"endTime":end}}})
        rows = d.get("tableData",{}).get("rows",[])
        all_rows.extend(rows)
        npt = d.get("nextPageToken","")
        if not npt or npt == page or len(rows) < 500:
            break
        page = npt
    by_day = {}
    for row in all_rows:
        val = row["data"].get(date_key,{}).get("value",{})
        date = val.get("string","")
        if not date:
            ts = val.get("timestamp","")
            if ts: date = ts[5:7] + "/" + ts[8:10] + "/" + ts[:4]
        if date:
            by_day[date] = by_day.get(date,0) + 1
    return len(all_rows), by_day

def gn(rd, key):
    v = rd.get(key,{}).get("value",{})
    val = v.get("number", v.get("int64", v.get("string",0)))
    try: return int(float(str(val)))
    except: return 0

today = datetime.now()
days_since_sun = (today.weekday() + 1) % 7
week_sun = (today - timedelta(days=days_since_sun)).replace(hour=0,minute=0,second=0,microsecond=0)
week_sat = week_sun + timedelta(days=6,hours=23,minutes=59,seconds=59)
START = week_sun.strftime("%Y-%m-%dT%H:%M:%SZ")
END   = week_sat.strftime("%Y-%m-%dT%H:%M:%SZ")
HIST_START = (week_sun - __import__("datetime").timedelta(weeks=4)).strftime("%Y-%m-%dT%H:%M:%SZ")
last_sun   = week_sun - timedelta(days=7)
last_sat   = week_sun - timedelta(seconds=1)
LAST_START = last_sun.strftime("%Y-%m-%dT%H:%M:%SZ")
LAST_END   = last_sat.strftime("%Y-%m-%dT%H:%M:%SZ")
WEEK_LABEL = week_sun.strftime("%b %d") + "\u2013" + week_sat.strftime("%b %d, %Y")
UPDATED    = today.strftime("%b %d, %Y at %I:%M %p")
DAYS       = [(week_sun + timedelta(days=i)) for i in range(7)]
DAY_LABELS = [d.strftime("%a") + " " + str(d.month) + "/" + str(d.day) for d in DAYS]
DAY_KEYS   = [str(d.month) + "/" + str(d.day) + "/" + str(d.year) for d in DAYS]

def adate(dk):
    p = dk.split("/")
    return "{:02d}/{:02d}/{}".format(int(p[0]), int(p[1]), p[2])

# Archive last week's dashboard if it exists and is a different week
ARCHIVE = Path(__file__).parent / "Archive"
ARCHIVE.mkdir(exist_ok=True)
if OUTPUT.exists():
    import re, shutil
    old_html = OUTPUT.read_text()
    match = re.search(r"Week of ([A-Z][a-z]+ \d+)", old_html)
    if match:
        old_week_label = match.group(1)
        current_label  = week_sun.strftime("%b %d")
        if old_week_label != current_label:
            archive_name = "central_bark_" + week_sun.strftime("%Y-%m-%d") + ".html"
            archive_path = ARCHIVE / archive_name
            if not archive_path.exists():
                shutil.copy(OUTPUT, archive_path)
                print("[ARCHIVE] Saved " + old_week_label + " to Archive folder")

log("Starting update - week " + WEEK_LABEL)

revenue, totals, counts = {}, {}, {}
for name, cid, bid in LOCS:
    log("Pulling " + name + "...")
    revenue[name], totals[name], counts[name] = {}, {}, {}
    d = api_post({"pagination":{"pageSize":500,"pageToken":"1"},"companyId":cid,"businessIds":[bid],"condition":{"id":"reports_daily_sales","queryPeriod":{"startTime":HIST_START,"endTime":END},"groupByFieldKeys":["checkout_date","care_type"]}})
    for row in d.get("tableData",{}).get("rows",[]):
        rd   = row["data"]
        date = rd.get("checkout_date",{}).get("value",{}).get("string","")
        care = rd.get("care_type",{}).get("value",{}).get("string","")
        amt  = money(rd,"total_collected")
        if date not in revenue[name]:
            revenue[name][date] = {}
        revenue[name][date][care] = revenue[name][date].get(care,0) + amt
    d = api_post({"pagination":{"pageSize":100,"pageToken":"1"},"companyId":cid,"businessIds":[bid],"condition":{"id":"reports_sales_summary","queryPeriod":{"startTime":START,"endTime":END},"groupByFieldKeys":["sale_datetime"]}})
    for row in d.get("tableData",{}).get("rows",[]):
        rd   = row["data"]
        date = rd.get("sale_datetime",{}).get("value",{}).get("string","")
        totals[name][date] = {"expected":money(rd,"total_expected"),"collected":money(rd,"total_collected"),"unpaid":money(rd,"outstanding_balance"),"tips":money(rd,"total_tips")}
    for label,report_id,date_key in [("DAYCARE","reports_daycare_appointment_list","appointment_start_date"),("BOARDING","reports_boarding_appointment_list","appointment_start_date"),("GROOMING","reports_appointment_list","appointment_date")]:
        total, by_day = fetch_pages(cid, bid, report_id, date_key, START, END)
        counts[name][label] = {"TOTAL": total}
        counts[name][label].update(by_day)
        log("  " + label + ": " + str(total))
    # SNP from boarding list - filter by service containing SNP
    snp_rows = api_post({"pagination":{"pageSize":500,"pageToken":"1"},"companyId":cid,"businessIds":[bid],"condition":{"id":"reports_boarding_appointment_list","queryPeriod":{"startTime":START,"endTime":END}}})
    snp_by_day = {}
    snp_total = 0
    for row in snp_rows.get("tableData",{}).get("rows",[]):
        rd = row.get("data",{})
        service = str(rd.get("service_type",rd.get("service",rd.get("type",{}))).get("value",{}).get("string","")).upper()
        lodging = str(rd.get("lodgings",rd.get("lodging_type",rd.get("lodging",{}))).get("value",{}).get("string","")).upper()
        combined = service + " " + lodging
        if "SNP" in combined or "STAY" in combined or "PLAY" in combined:
            snp_total += 1
            _dv = rd.get("appointment_start_date",{}).get("value",{})
            _ts = _dv.get("timestamp","")
            date_val = _dv.get("string","") or (_ts[5:7]+"/"+_ts[8:10]+"/"+_ts[:4] if _ts else "")
            if date_val: snp_by_day[date_val] = snp_by_day.get(date_val,0) + 1
    counts[name]["SNP"] = {"TOTAL": snp_total}
    counts[name]["SNP"].update(snp_by_day)
    log("  SNP: " + str(snp_total))

log("Pulling last week + clients + boarding nights...")

last_week_rev = {}
for name, cid, bid in LOCS:
    d = api_post({"pagination":{"pageSize":100,"pageToken":"1"},"companyId":cid,"businessIds":[bid],"condition":{"id":"reports_sales_summary","queryPeriod":{"startTime":LAST_START,"endTime":LAST_END},"groupByFieldKeys":["sale_datetime"]}})
    # Only sum last week days that match this week's completed days (apples to apples)
    total_lw = 0
    for row in d.get("tableData",{}).get("rows",[]):
        rd = row["data"]
        date_str = rd.get("sale_datetime",{}).get("value",{}).get("string","")
        if date_str:
            try:
                from datetime import datetime as dt2
                row_date = dt2.strptime(date_str, "%m/%d/%Y")
                if row_date.weekday() <= today.weekday() or row_date.weekday() == 6:
                    total_lw += money(rd,"total_expected")
            except:
                total_lw += money(rd,"total_expected")
    last_week_rev[name] = total_lw
    log("  Last week " + name + ": " + fmt(last_week_rev[name]))

clients = {}
for name, cid, bid in LOCS:
    all_rows, page = [], "1"
    while True:
        d = api_post({"pagination":{"pageSize":500,"pageToken":page},"companyId":cid,"businessIds":[bid],"condition":{"id":"reports_client_summary","queryPeriod":{"startTime":START,"endTime":END}}})
        rows = d.get("tableData",{}).get("rows",[])
        all_rows.extend(rows)
        npt = d.get("nextPageToken","")
        if not npt or npt == page or len(rows) < 500:
            break
        page = npt
    clients[name] = {
        "new":       sum(gn(r["data"],"new_clients_count")       for r in all_rows),
        "existing":  sum(gn(r["data"],"existing_clients_count")  for r in all_rows),
        "recurring": sum(gn(r["data"],"recurring_clients_count") for r in all_rows),
        "total":     sum(gn(r["data"],"uniq_serviced_clients")   for r in all_rows),
    }
    log("  Clients " + name + ": new=" + str(clients[name]["new"]) + " total=" + str(clients[name]["total"]))

boarding_nights = {}
for name, cid, bid in LOCS:
    d = api_post({"pagination":{"pageSize":500,"pageToken":"1"},"companyId":cid,"businessIds":[bid],"condition":{"id":"reports_boarding_appointment_list","queryPeriod":{"startTime":START,"endTime":END}}})
    rows = d.get("tableData",{}).get("rows",[])
    nights = sum(int(row["data"].get("num_of_nights",{}).get("value",{}).get("int64",0) or 0) for row in rows)
    boarding_nights[name] = {"dogs":len(rows),"nights":nights}
    log("  Boarding " + name + ": " + str(len(rows)) + " dogs, " + str(nights) + " nights")

# ── STAFF PERFORMANCE ─────────────────────────────────────────────────────────
log("Pulling staff performance...")
staff_data = {}
for name, cid, bid in LOCS:
    r = api_post({"pagination":{"pageSize":500,"pageToken":"1"},"companyId":cid,"businessIds":[bid],
                  "condition":{"id":"reports_appointment_list","queryPeriod":{"startTime":START,"endTime":END}}})
    rows = r.get("tableData",{}).get("rows",[])
    staff = {}
    for row in rows:
        rd = row["data"]
        st = rd.get("appointment_status",{}).get("value",{}).get("string","")
        if st in ["Cancelled","No-show"]: continue
        sname = rd.get("assigned_staff",{}).get("value",{}).get("string","") or "Unassigned"
        rev = money(rd, "net_sale")
        if sname not in staff: staff[sname] = {"appts":0,"revenue":0}
        staff[sname]["appts"] += 1
        staff[sname]["revenue"] += rev
    staff_data[name] = dict(sorted(staff.items(), key=lambda x: x[1]["revenue"], reverse=True))
    log(f"  Staff {name}: {len(staff)} groomers")
log("Staff data complete.")

# ── REVIEW SCORES ────────────────────────────────────────────────────────────
log("Pulling review scores...")
review_data = {}
for name, cid, bid in LOCS:
    r = api_post({"pagination":{"pageSize":500,"pageToken":"1"},"companyId":cid,"businessIds":[bid],
                  "condition":{"id":"reports_appointment_list","queryPeriod":{"startTime":START,"endTime":END}}})
    rows = r.get("tableData",{}).get("rows",[])
    scores = []
    staff_scores = {}
    for row in rows:
        rd = row["data"]
        score_val = rd.get("average_review_score",{}).get("value",{})
        score = score_val.get("number", score_val.get("double", None))
        if score:
            try:
                score = float(score)
                scores.append(score)
                sname = rd.get("assigned_staff",{}).get("value",{}).get("string","") or "Unassigned"
                if sname not in staff_scores: staff_scores[sname] = []
                staff_scores[sname].append(score)
            except: pass
    avg = round(sum(scores)/len(scores),2) if scores else 0
    staff_avgs = {s: round(sum(v)/len(v),2) for s,v in staff_scores.items() if v}
    staff_avgs = dict(sorted(staff_avgs.items(), key=lambda x: x[1], reverse=True))
    review_data[name] = {"avg": avg, "count": len(scores), "by_staff": staff_avgs}
    log(f"  Reviews {name}: avg={avg} n={len(scores)}")
log("Review data complete.")

# ── SERVICE MIX ──────────────────────────────────────────────────────────────
log("Pulling service mix...")
service_mix = {}
for name, cid, bid in LOCS:
    all_rows, page = [], "1"
    while True:
        r = api_post({"pagination":{"pageSize":500,"pageToken":page},"companyId":cid,"businessIds":[bid],
                      "condition":{"id":"reports_sales_invoice_item","queryPeriod":{"startTime":START,"endTime":END}}})
        batch = r.get("tableData",{}).get("rows",[])
        all_rows.extend(batch)
        npt = r.get("nextPageToken","")
        if not npt or npt == page or len(batch) < 500: break
        page = npt
    cats = {}
    for row in all_rows:
        rd = row["data"]
        # Filter by appt_start_date to match current week only
        cat = rd.get("revenue_category",{}).get("value",{}).get("string","") or rd.get("category",{}).get("value",{}).get("string","Other")
        rev = money(rd, "net_sales")
        cats[cat] = cats.get(cat, 0) + rev
    total = sum(cats.values())
    service_mix[name] = {"total": total, "cats": dict(sorted(cats.items(), key=lambda x: x[1], reverse=True))}
    log(f"  Service mix {name}: {len(cats)} categories, total={fmt(total)}")
log("Service mix complete.")

# ── MEMBERSHIP CONVERSION ────────────────────────────────────────────────────
log("Pulling membership conversion...")
membership_conv = {}
for name, cid, bid in LOCS:
    all_rows, page = [], "1"
    while True:
        r = api_post({"pagination":{"pageSize":500,"pageToken":page},"companyId":cid,"businessIds":[bid],
                      "condition":{"id":"reports_sales_invoice_item","queryPeriod":{"startTime":START,"endTime":END}}})
        batch = r.get("tableData",{}).get("rows",[])
        all_rows.extend(batch)
        npt = r.get("nextPageToken","")
        if not npt or npt == page or len(batch) < 500: break
        page = npt
    total_clients = set()
    mem_clients = set()
    for row in all_rows:
        rd = row["data"]
        cid_val = rd.get("client_id",{}).get("value",{}).get("string","")
        if cid_val: total_clients.add(cid_val)
        mem_flag = rd.get("membership_redeemed_flag",{}).get("value",{}).get("string","")
        if mem_flag and mem_flag.lower() in ["true","yes","1"] and cid_val:
            mem_clients.add(cid_val)
    rate = round(len(mem_clients)/len(total_clients)*100,1) if total_clients else 0
    membership_conv[name] = {"total": len(total_clients), "members": len(mem_clients), "rate": rate}
    log(f"  Membership {name}: {len(mem_clients)}/{len(total_clients)} ({rate}%)")
log("Membership conversion complete.")

# ── CLIENT RETENTION ─────────────────────────────────────────────────────────
log("Pulling client retention...")
from datetime import date as _date
retention_data = {}
_s90 = (week_sun - timedelta(days=83)).strftime("%Y-%m-%dT00:00:00Z")
for name, cid, bid in LOCS:
    all_rows, page = [], "1"
    while True:
        r = api_post({"pagination":{"pageSize":500,"pageToken":page},"companyId":cid,"businessIds":[bid],
                      "condition":{"id":"reports_daycare_appointment_list","queryPeriod":{"startTime":_s90,"endTime":END}}})
        batch = r.get("tableData",{}).get("rows",[])
        all_rows.extend(batch)
        npt = r.get("nextPageToken","")
        if not npt or npt == page or len(batch) < 500: break
        page = npt
    rows = all_rows
    cli = {}
    for row in rows:
        rd = row["data"]
        if rd.get("appointment_status",{}).get("value",{}).get("string","") == "Cancelled": continue
        cid_val = rd.get("client_id",{}).get("value",{}).get("string","")
        ts = rd.get("appointment_start_date",{}).get("value",{}).get("timestamp","")
        if ts and cid_val:
            vd = datetime.strptime(ts[:10],"%Y-%m-%d").date()
            if cid_val not in cli or cli[cid_val] < vd: cli[cid_val] = vd
    today_d2 = _date.today()
    retention_data[name] = {
        "total": len(cli),
        "active": sum(1 for d in cli.values() if (today_d2-d).days <= 30),
        "lapsed_30": sum(1 for d in cli.values() if 30 < (today_d2-d).days <= 60),
        "lapsed_60": sum(1 for d in cli.values() if 60 < (today_d2-d).days <= 90),
        "lapsed_90": sum(1 for d in cli.values() if (today_d2-d).days > 90),
    }
    log(f"  Retention {name}: {retention_data[name]}")
log("Retention data complete.")

# ── CANCELLATION RATES ────────────────────────────────────────────────────────
log("Pulling cancellation rates...")
cancel_data = {}
for name, cid, bid in LOCS:
    gr = api_post({"pagination":{"pageSize":500,"pageToken":"1"},"companyId":cid,"businessIds":[bid],
                   "condition":{"id":"reports_appointment_list","queryPeriod":{"startTime":START,"endTime":END}}})
    gr_rows = gr.get("tableData",{}).get("rows",[])
    gr_total = len(gr_rows)
    gr_cancel = sum(1 for r in gr_rows if r["data"].get("appointment_status",{}).get("value",{}).get("string","") in ["Cancelled","No-show"])
    gr_noshow = sum(1 for r in gr_rows if r["data"].get("appointment_status",{}).get("value",{}).get("string","") == "No-show")

    dc = api_post({"pagination":{"pageSize":500,"pageToken":"1"},"companyId":cid,"businessIds":[bid],
                   "condition":{"id":"reports_daycare_appointment_list","queryPeriod":{"startTime":START,"endTime":END}}})
    dc_rows = dc.get("tableData",{}).get("rows",[])
    dc_total = len(dc_rows)
    dc_cancel = sum(1 for r in dc_rows if r["data"].get("appointment_status",{}).get("value",{}).get("string","") == "Cancelled")

    cancel_data[name] = {
        "gr_total": gr_total, "gr_cancel": gr_cancel, "gr_noshow": gr_noshow,
        "gr_rate": round(gr_cancel/gr_total*100,1) if gr_total else 0,
        "dc_total": dc_total, "dc_cancel": dc_cancel,
        "dc_rate": round(dc_cancel/dc_total*100,1) if dc_total else 0,
    }
    log(f"  Cancellations {name}: Grooming {gr_cancel}/{gr_total} ({cancel_data[name]['gr_rate']}%) Daycare {dc_cancel}/{dc_total} ({cancel_data[name]['dc_rate']}%)")
log("Cancellation data complete.")

# Q1 Bonus Tracker
BONUS_TARGETS = {
    "Wauwatosa":          {"pct": 0.07, "ly_full": 404791.49},
    "Milwaukee Downtown": {"pct": 0.07, "ly_full": 212902.65},
    "Grayslake":          {"pct": 0.10, "ly_full": 287057.97},
    "Milwaukee Eastside": {"pct": 0.07, "ly_full": 255660.02},
    "Mequon":             {"pct": 0.10, "ly_full":      0.00},
}
q1_ly_start = "2025-01-01T00:00:00Z"
q1_ly_same_end = today.replace(year=2025).strftime("%Y-%m-%dT23:59:59Z")
q1_ty_start = "2026-01-01T00:00:00Z"
q1_ty_end   = today.strftime("%Y-%m-%dT23:59:59Z")
from datetime import date as ddate
days_left_q1 = (ddate(2026,3,31) - today.date()).days
q1_data = {}
for name, cid, bid in LOCS:
    d = api_post({"pagination":{"pageSize":100,"pageToken":"1"},"companyId":cid,"businessIds":[bid],"condition":{"id":"reports_sales_summary","queryPeriod":{"startTime":q1_ly_start,"endTime":q1_ly_same_end},"groupByFieldKeys":["sale_datetime"]}})
    ly_same = sum(money(row["data"],"total_expected") for row in d.get("tableData",{}).get("rows",[]))
    d = api_post({"pagination":{"pageSize":100,"pageToken":"1"},"companyId":cid,"businessIds":[bid],"condition":{"id":"reports_sales_summary","queryPeriod":{"startTime":q1_ty_start,"endTime":q1_ty_end},"groupByFieldKeys":["sale_datetime"]}})
    ty_qtd = sum(money(row["data"],"total_expected") for row in d.get("tableData",{}).get("rows",[]))
    ly_full  = BONUS_TARGETS[name]["ly_full"]
    pct      = BONUS_TARGETS[name]["pct"]
    target_q = ly_full * (1 + pct)
    gap      = max(target_q - ty_qtd, 0)
    progress = min((ty_qtd / target_q * 100) if target_q > 0 else 0, 100)
    vs_ly    = ty_qtd - ly_same
    vs_pct   = (vs_ly / ly_same * 100) if ly_same > 0 else 0
    pace     = gap / days_left_q1 if days_left_q1 > 0 else 0
    q1_data[name] = {"ly_full":ly_full,"ly_same":ly_same,"ty_qtd":ty_qtd,"target":target_q,"gap":gap,"progress":progress,"vs_ly":vs_ly,"vs_pct":vs_pct,"pace":pace,"pct":pct,"days_left":days_left_q1}
    log("  Q1 " + name + ": $" + "{:,.2f}".format(ty_qtd) + " / $" + "{:,.2f}".format(target_q) + " (" + "{:.1f}".format(progress) + "%)")

log("Data complete - building HTML...")

def loc_total(name, field):
    return sum(v[field] for v in totals[name].values())

def loc_mem(name):
    return sum(revenue[name].get(adate(dk),{}).get("Non-service sales",0) for dk in DAY_KEYS)

grand_exp  = sum(loc_total(n,"expected")  for n,_,_ in LOCS)
grand_col  = sum(loc_total(n,"collected") for n,_,_ in LOCS)
grand_unp  = sum(loc_total(n,"unpaid")    for n,_,_ in LOCS)
grand_tips = sum(loc_total(n,"tips")      for n,_,_ in LOCS)
tot_dc = sum(counts[n].get("DAYCARE", {}).get("TOTAL",0) for n,_,_ in LOCS)
# today_counts: use today's specific date key for accurate capacity utilization
# Build today key - try both padded and unpadded to match MoeGo format
_today_key   = "{:02d}/{:02d}/{}".format(today.month, today.day, today.year)
_today_key2  = "{}/{}/{}".format(today.month, today.day, today.year)
def _get_today(name, svc):
    d = counts[name].get(svc, {})
    return d.get(_today_key, d.get(_today_key2, 0))
today_counts = {name: {"daycare": _get_today(name,"DAYCARE"), "boarding": _get_today(name,"BOARDING"), "snp": _get_today(name,"SNP")} for name,_,_ in LOCS}
tot_bo = sum(counts[n].get("BOARDING",{}).get("TOTAL",0) for n,_,_ in LOCS)
tot_gr = sum(counts[n].get("GROOMING",{}).get("TOTAL",0) for n,_,_ in LOCS)

COLORS = {"Wauwatosa":"#f97316","Milwaukee Downtown":"#3b82f6","Grayslake":"#10b981","Milwaukee Eastside":"#a855f7","Mequon":"#f59e0b"}
CARE_ORDER  = ["Non-service sales","Grooming","Boarding","Daycare"]
CARE_LABELS = {"Non-service sales":"Memberships","Grooming":"Grooming","Boarding":"Boarding","Daycare":"Daycare"}
CARE_TAG    = {"Non-service sales":"ms","Grooming":"gr","Boarding":"bo","Daycare":"dc"}

def build_card(name, cid, bid):
    c    = COLORS[name]; exp=loc_total(name,"expected"); col2=loc_total(name,"collected")
    unp  = loc_total(name,"unpaid"); tips=loc_total(name,"tips")
    dc   = counts[name].get("DAYCARE", {}).get("TOTAL",0)
    bo   = counts[name].get("BOARDING",{}).get("TOTAL",0)
    gr   = counts[name].get("GROOMING",{}).get("TOTAL",0)
    mem  = loc_mem(name); no_data=(exp==0 and col2==0)
    op   = "opacity:0.4;" if no_data else ""
    uc   = "red" if unp>0 else "green"; cc="green" if unp==0 else ""
    notice = "<div class=\"notice\">No data returned - contact MoeGo CSM</div>" if no_data else ""
    return ("<div class=\"card\" style=\"--accent:" + c + ";" + op + "\">" +
            "<div class=\"card-name\">" + name + "</div>" +
            "<div class=\"card-rev\">" + fmt(exp) + "</div>" +
            "<div class=\"card-revlbl\">Week Expected (WTD)</div>" +
            "<div class=\"kpi\"><span class=\"kpi-l\">Collected</span><span class=\"kpi-v " + cc + "\">" + fmt(col2) + "</span></div>" +
            "<div class=\"kpi\"><span class=\"kpi-l\">Unpaid</span><span class=\"kpi-v " + uc + "\">" + fmt(unp) + "</span></div>" +
            "<div class=\"kpi\"><span class=\"kpi-l\">Tips</span><span class=\"kpi-v\">" + fmt(tips) + "</span></div>" +
            "<div class=\"divider\"></div>" +
            "<div class=\"svc-row\">" +
            "<div class=\"svc dc\"><span>Daycare</span><strong>" + "{:,}".format(dc) + "</strong></div>" +
            "<div class=\"svc bo\"><span>Boarding</span><strong>" + "{:,}".format(bo) + "</strong></div>" +
            "<div class=\"svc gr\"><span>Grooming</span><strong>" + "{:,}".format(gr) + "</strong></div>" +
            "<div class=\"svc ms\"><span>Memberships</span><strong>" + fmt(mem) + "</strong></div>" +
            "</div>" + notice + "</div>")

cards_html = "\n".join(build_card(n,c,b) for n,c,b in LOCS)
day_headers = "".join("<th class=\"r\">" + l + "</th>" for l in DAY_LABELS)

rev_rows = ""
for name, cid, bid in LOCS:
    c = COLORS[name]; wtd = loc_total(name,"expected")
    day_cells = ""
    for dk in DAY_KEYS:
        val = sum(revenue[name].get(adate(dk),{}).values())
        day_cells += "<td class=\"r mono\">" + (fmt(val) if val > 0 else "\u2014") + "</td>"
    rev_rows += "<tr><td class=\"bold\"><span class=\"dot\" style=\"background:" + c + "\"></span>" + name + "</td>" + day_cells + "<td class=\"r mono bold\">" + fmt(wtd) + "</td></tr>"
    for care in CARE_ORDER:
        tag = CARE_TAG[care]; lbl = CARE_LABELS[care]; cells = ""
        for dk in DAY_KEYS:
            val = revenue[name].get(adate(dk),{}).get(care,0)
            cells += "<td class=\"r mono\">" + (fmt(val) if val > 0 else "\u2014") + "</td>"
        sub = sum(revenue[name].get(adate(dk),{}).get(care,0) for dk in DAY_KEYS)
        rev_rows += "<tr class=\"subrow\"><td><span class=\"tag " + tag + "\">" + lbl + "</span></td>" + cells + "<td class=\"r mono\">" + (fmt(sub) if sub > 0 else "\u2014") + "</td></tr>"
tot_cells = ""
for dk in DAY_KEYS:
    s = sum(sum(revenue[n].get(adate(dk),{}).values()) for n,_,_ in LOCS)
    tot_cells += "<td class=\"r mono\">" + (fmt(s) if s > 0 else "\u2014") + "</td>"
rev_rows += "<tr class=\"total\"><td>TOTAL (4 locations)</td>" + tot_cells + "<td class=\"r mono\">" + fmt(grand_exp) + "</td></tr>"

count_rows = ""; first = True
for name, cid, bid in LOCS:
    c = COLORS[name]; border = "" if first else "style=\"border-top:1px solid #2a2a2a\""; first = False
    for i, (svc, tag) in enumerate([("DAYCARE","dc"),("BOARDING","bo"),("GROOMING","gr")]):
        total = counts[name].get(svc,{}).get("TOTAL",0); cells = ""
        for dk in DAY_KEYS:
            val = counts[name].get(svc,{}).get(adate(dk),0)
            cells += "<td class=\"c mono\">" + (str(val) if val > 0 else "\u2014") + "</td>"
        if i == 0:
            count_rows += "<tr " + border + "><td class=\"bold\" rowspan=\"3\"><span class=\"dot\" style=\"background:" + c + "\"></span>" + name + "</td><td><span class=\"tag " + tag + "\">" + svc.capitalize() + "</span></td>" + cells + "<td class=\"r mono bold\">" + "{:,}".format(total) + "</td></tr>"
        else:
            count_rows += "<tr><td><span class=\"tag " + tag + "\">" + svc.capitalize() + "</span></td>" + cells + "<td class=\"r mono bold\">" + "{:,}".format(total) + "</td></tr>"
for svc, tag in [("DAYCARE","dc"),("BOARDING","bo"),("GROOMING","gr")]:
    gt = sum(counts[n].get(svc,{}).get("TOTAL",0) for n,_,_ in LOCS); cells = ""
    for dk in DAY_KEYS:
        dv = sum(counts[n].get(svc,{}).get(adate(dk),0) for n,_,_ in LOCS)
        cells += "<td class=\"c mono\">" + (str(dv) if dv > 0 else "\u2014") + "</td>"
    bdr = "2" if svc == "DAYCARE" else "1"
    count_rows += "<tr class=\"total\" style=\"border-top:" + bdr + "px solid #2a2a2a\"><td colspan=\"2\">TOTAL " + svc.capitalize() + "</td>" + cells + "<td class=\"r mono\">" + "{:,}".format(gt) + "</td></tr>"

unpaid_rows = ""
for name, cid, bid in LOCS:
    c = COLORS[name]; exp=loc_total(name,"expected"); col2=loc_total(name,"collected")
    unp=loc_total(name,"unpaid"); tips=loc_total(name,"tips")
    if exp == 0:
        unpaid_rows += "<tr><td class=\"dim\"><span class=\"dot\" style=\"background:" + c + "\"></span>" + name + "</td><td class=\"r mono dim\">\u2014</td><td class=\"r mono dim\">\u2014</td><td class=\"r mono dim\">\u2014</td><td class=\"r mono dim\">\u2014</td></tr>"
    else:
        uc = "red" if unp>0 else "green"; cc="green" if unp==0 else ""
        unpaid_rows += "<tr><td class=\"bold\"><span class=\"dot\" style=\"background:" + c + "\"></span>" + name + "</td><td class=\"r mono\">" + fmt(exp) + "</td><td class=\"r mono " + cc + "\">" + fmt(col2) + "</td><td class=\"r mono " + uc + "\">" + fmt(unp) + "</td><td class=\"r mono\">" + fmt(tips) + "</td></tr>"
unpaid_rows += "<tr class=\"total\"><td>TOTAL</td><td class=\"r mono\">" + fmt(grand_exp) + "</td><td class=\"r mono\">" + fmt(grand_col) + "</td><td class=\"r mono red\">" + fmt(grand_unp) + "</td><td class=\"r mono\">" + fmt(grand_tips) + "</td></tr>"

wow_rows = ""; wow_exp_total = wow_last_total = 0
for name, cid, bid in LOCS:
    c=COLORS[name]; this_wtd=loc_total(name,"expected"); last_w=last_week_rev[name]
    diff=this_wtd-last_w; pct=(diff/last_w*100) if last_w>0 else 0
    dc2="green" if diff>=0 else "red"; ps=("+" if pct>=0 else "")+"{:.1f}%".format(pct)
    wow_exp_total+=this_wtd; wow_last_total+=last_w
    if this_wtd==0 and last_w==0:
        wow_rows += "<tr><td class=\"dim\"><span class=\"dot\" style=\"background:"+c+"\"></span>"+name+"</td><td class=\"r mono dim\">\u2014</td><td class=\"r mono dim\">\u2014</td><td class=\"r mono dim\">\u2014</td><td class=\"r mono dim\">\u2014</td></tr>"
    else:
        wow_rows += "<tr><td class=\"bold\"><span class=\"dot\" style=\"background:"+c+"\"></span>"+name+"</td><td class=\"r mono\">"+fmt(this_wtd)+"</td><td class=\"r mono\">"+fmt(last_w)+"</td><td class=\"r mono "+dc2+"\">"+("+" if diff>=0 else "")+fmt(diff)+"</td><td class=\"r mono "+dc2+"\">"+ps+"</td></tr>"
wd=wow_exp_total-wow_last_total; wp=(wd/wow_last_total*100) if wow_last_total>0 else 0; wdc="green" if wd>=0 else "red"
wow_rows += "<tr class=\"total\"><td>TOTAL</td><td class=\"r mono\">"+fmt(wow_exp_total)+"</td><td class=\"r mono\">"+fmt(wow_last_total)+"</td><td class=\"r mono "+wdc+"\">"+("+" if wd>=0 else "")+fmt(wd)+"</td><td class=\"r mono "+wdc+"\">"+("+" if wp>=0 else "")+"{:.1f}%".format(wp)+"</td></tr>"

client_rows = ""; tot_new=tot_existing=tot_recurring=tot_clients=0
for name, cid, bid in LOCS:
    c=COLORS[name]; cl=clients[name]; pct=(cl["new"]/cl["total"]*100) if cl["total"]>0 else 0
    tot_new+=cl["new"]; tot_existing+=cl["existing"]; tot_recurring+=cl["recurring"]; tot_clients+=cl["total"]
    if cl["total"]==0:
        client_rows += "<tr><td class=\"dim\"><span class=\"dot\" style=\"background:"+c+"\"></span>"+name+"</td><td class=\"r mono dim\">\u2014</td><td class=\"r mono dim\">\u2014</td><td class=\"r mono dim\">\u2014</td><td class=\"r mono dim\">\u2014</td><td class=\"r mono dim\">\u2014</td></tr>"
    else:
        client_rows += "<tr><td class=\"bold\"><span class=\"dot\" style=\"background:"+c+"\"></span>"+name+"</td><td class=\"r mono\">"+"{:,}".format(cl["total"])+"</td><td class=\"r mono green\">"+str(cl["new"])+"</td><td class=\"r mono\">"+"{:,}".format(cl["existing"])+"</td><td class=\"r mono\">"+"{:,}".format(cl["recurring"])+"</td><td class=\"r mono\">"+"{:.1f}%".format(pct)+"</td></tr>"
tp=(tot_new/tot_clients*100) if tot_clients>0 else 0
client_rows += "<tr class=\"total\"><td>TOTAL</td><td class=\"r mono\">"+"{:,}".format(tot_clients)+"</td><td class=\"r mono green\">"+str(tot_new)+"</td><td class=\"r mono\">"+"{:,}".format(tot_existing)+"</td><td class=\"r mono\">"+"{:,}".format(tot_recurring)+"</td><td class=\"r mono\">"+"{:.1f}%".format(tp)+"</td></tr>"

boarding_rows = ""; tot_bd_dogs=tot_bd_nights=0
for name, cid, bid in LOCS:
    c=COLORS[name]; bd=boarding_nights[name]; avg=(bd["nights"]/bd["dogs"]) if bd["dogs"]>0 else 0
    tot_bd_dogs+=bd["dogs"]; tot_bd_nights+=bd["nights"]
    if bd["dogs"]==0:
        boarding_rows += "<tr><td class=\"dim\"><span class=\"dot\" style=\"background:"+c+"\"></span>"+name+"</td><td class=\"r mono dim\">\u2014</td><td class=\"r mono dim\">\u2014</td><td class=\"r mono dim\">\u2014</td></tr>"
    else:
        boarding_rows += "<tr><td class=\"bold\"><span class=\"dot\" style=\"background:"+c+"\"></span>"+name+"</td><td class=\"r mono\">"+str(bd["dogs"])+"</td><td class=\"r mono\">"+str(bd["nights"])+"</td><td class=\"r mono\">"+"{:.1f}".format(avg)+"</td></tr>"
tot_avg=(tot_bd_nights/tot_bd_dogs) if tot_bd_dogs>0 else 0
boarding_rows += "<tr class=\"total\"><td>TOTAL</td><td class=\"r mono\">"+str(tot_bd_dogs)+"</td><td class=\"r mono\">"+str(tot_bd_nights)+"</td><td class=\"r mono\">"+"{:.1f}".format(tot_avg)+"</td></tr>"

bonus_rows = ""
for name, cid, bid in LOCS:
    c = COLORS[name]
    q = q1_data[name]
    no_data = (q["ly_full"] == 0 and q["ty_qtd"] == 0)
    if no_data:
        bonus_rows += "<tr><td class=\"bold\"><span class=\"dot\" style=\"background:" + c + "\"></span>" + name + "</td><td colspan=\"7\" style=\"color:#555;font-size:0.75rem\">Starts tracking Q2</td></tr>"
        continue
    bar_color = "#22c55e" if q["progress"] >= 90 else "#f97316" if q["progress"] >= 70 else "#ef4444"
    vs_cls = "green" if q["vs_ly"] >= 0 else "red"
    vs_str = ("+" if q["vs_ly"] >= 0 else "") + "${:,.2f}".format(q["vs_ly"]) + " (" + ("+" if q["vs_pct"] >= 0 else "") + "{:.1f}%".format(q["vs_pct"]) + ")"
    prog_bar = ("<div style=\"background:#2a2a2a;border-radius:4px;height:8px;width:100%;min-width:100px\">" +
               "<div style=\"background:" + bar_color + ";height:8px;border-radius:4px;width:" + "{:.1f}".format(q["progress"]) + "%\"></div></div>" +
               "<div style=\"font-size:0.65rem;color:" + bar_color + ";margin-top:3px;font-family:'DM Mono',monospace\">" + "{:.1f}".format(q["progress"]) + "% to target</div>")
    bonus_rows += ("<tr>" +
        "<td class=\"bold\"><span class=\"dot\" style=\"background:" + c + "\"></span>" + name + "<br><span style=\"font-size:0.65rem;color:#555;font-weight:400\">+" + "{:.0f}".format(q["pct"]*100) + "% target</span></td>" +
        "<td class=\"r mono\">" + "${:,.2f}".format(q["ly_full"]) + "</td>" +
        "<td class=\"r mono bold\">" + "${:,.2f}".format(q["target"]) + "</td>" +
        "<td class=\"r mono\">" + "${:,.2f}".format(q["ly_same"]) + "</td>" +
        "<td class=\"r mono bold green\">" + "${:,.2f}".format(q["ty_qtd"]) + "</td>" +
        "<td class=\"r mono " + vs_cls + "\">" + vs_str + "</td>" +
        "<td class=\"r mono\">" + "${:,.2f}".format(q["gap"]) + "<br><span style=\"font-size:0.65rem;color:#555\">" + "${:,.0f}/day".format(q["pace"]) + " (" + str(q["days_left"]) + "d left)</span></td>" +
        "<td style=\"min-width:120px\">" + prog_bar + "</td>" +
        "</tr>")


# ── RETAIL DATA PULL ─────────────────────────────────────────────────────────
retail = {}
for name, cid, bid in LOCS:
    all_rows, page = [], "1"
    while True:
        d = api_post({"pagination":{"pageSize":500,"pageToken":page},"companyId":cid,"businessIds":[bid],"condition":{"id":"reports_sales_invoice_item","queryPeriod":{"startTime":START,"endTime":END}}})
        rows = d.get("tableData",{}).get("rows",[])
        all_rows.extend(rows)
        npt = d.get("nextPageToken","")
        if not npt or npt == page or len(rows) < 500:
            break
        page = npt
    rrows = [r for r in all_rows if r["data"].get("category",{}).get("value",{}).get("string","") == "Product"]
    all_rev = sum(money(r["data"],"net_sales") for r in all_rows)
    ret_total = sum(money(r["data"],"net_sales") for r in rrows)
    daily_ret = {}
    items_ret = {}
    for row in rrows:
        ts = row["data"].get("checkout_date",{}).get("value",{}).get("timestamp","")
        if ts:
            date = ts[5:7] + "/" + ts[8:10] + "/" + ts[:4]
        else:
            date = row["data"].get("checkout_date",{}).get("value",{}).get("string","")
        amt  = money(row["data"],"net_sales")
        qty  = int(row["data"].get("quantity",{}).get("value",{}).get("int64",1) or 1)
        item = row["data"].get("item_name",{}).get("value",{}).get("string","Unknown")
        daily_ret[date] = daily_ret.get(date,0) + amt
        if item not in items_ret:
            items_ret[item] = {"qty":0,"amt":0}
        items_ret[item]["qty"] += qty
        items_ret[item]["amt"] += amt
    retail[name] = {"total":ret_total,"all_rev":all_rev,"daily":daily_ret,"items":items_ret}
    log("  Retail " + name + ": " + fmt(ret_total) + " (" + "{:.1f}%".format((ret_total/all_rev*100) if all_rev>0 else 0) + "% of revenue)")

# ── YTD DATA PULL ─────────────────────────────────────────────────────────────
TY_YTD_START  = "2026-01-01T00:00:00Z"
TY_YTD_END    = today.strftime("%Y-%m-%dT23:59:59Z")
LY_YTD_START  = "2025-01-01T00:00:00Z"
LY_YTD_END    = today.replace(year=2025).strftime("%Y-%m-%dT23:59:59Z")
LY_FULL_START = "2025-01-01T00:00:00Z"
LY_FULL_END   = "2025-12-31T23:59:59Z"
ytd_data = {}
for name, cid, bid in LOCS:
    d = api_post({"pagination":{"pageSize":500,"pageToken":"1"},"companyId":cid,"businessIds":[bid],"condition":{"id":"reports_sales_summary","queryPeriod":{"startTime":TY_YTD_START,"endTime":TY_YTD_END},"groupByFieldKeys":["sale_datetime"]}})
    ty_ytd = sum(money(row["data"],"total_expected") for row in d.get("tableData",{}).get("rows",[]))
    d = api_post({"pagination":{"pageSize":500,"pageToken":"1"},"companyId":cid,"businessIds":[bid],"condition":{"id":"reports_sales_summary","queryPeriod":{"startTime":LY_YTD_START,"endTime":LY_YTD_END},"groupByFieldKeys":["sale_datetime"]}})
    ly_ytd = sum(money(row["data"],"total_expected") for row in d.get("tableData",{}).get("rows",[]))
    d = api_post({"pagination":{"pageSize":500,"pageToken":"1"},"companyId":cid,"businessIds":[bid],"condition":{"id":"reports_sales_summary","queryPeriod":{"startTime":LY_FULL_START,"endTime":LY_FULL_END},"groupByFieldKeys":["sale_datetime"]}})
    ly_full = sum(money(row["data"],"total_expected") for row in d.get("tableData",{}).get("rows",[]))
    diff = ty_ytd - ly_ytd
    pct  = (diff/ly_ytd*100) if ly_ytd>0 else 0
    LY_MONTHLY_PCT = {1:0.069,2:0.070,3:0.090,4:0.076,5:0.081,6:0.092,7:0.083,8:0.085,9:0.090,10:0.097,11:0.077,12:0.091}
    import calendar
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    month_frac    = today.day / days_in_month
    pct_year_done = sum(LY_MONTHLY_PCT[m] for m in range(1, today.month)) + LY_MONTHLY_PCT[today.month] * month_frac
    proj = (ty_ytd / pct_year_done) if pct_year_done > 0 else 0
    ytd_data[name] = {"ty_ytd":ty_ytd,"ly_ytd":ly_ytd,"ly_full":ly_full,"diff":diff,"pct":pct,"proj":proj}
    log("  YTD " + name + ": " + fmt(ty_ytd) + " vs LY " + fmt(ly_ytd) + " (" + "{:+.1f}%".format(pct) + ")")

log("Data complete - building HTML...")



grand_retail = sum(retail[n]["total"] for n,_,_ in LOCS)

retail_day_rows=""
for name, cid, bid in LOCS:
    c=COLORS[name]; rt=retail[name]; pct2=(rt["total"]/rt["all_rev"]*100) if rt["all_rev"]>0 else 0
    cells="".join("<td class=\"r mono\">"+(fmt(rt["daily"].get(adate(dk),0)) if rt["daily"].get(adate(dk),0)>0 else "\u2014")+"</td>" for dk in DAY_KEYS)
    retail_day_rows+="<tr><td class=\"bold\"><span class=\"dot\" style=\"background:"+c+"\"></span>"+name+"</td>"+cells+"<td class=\"r mono bold\">"+fmt(rt["total"])+"</td><td class=\"r mono\">"+"{:.1f}%".format(pct2)+"</td></tr>"
grand_all_rev=sum(retail[n]["all_rev"] for n,_,_ in LOCS)
grand_ret_pct=(grand_retail/grand_all_rev*100) if grand_all_rev>0 else 0
tot_rc="".join("<td class=\"r mono\">"+(fmt(sum(retail[n]["daily"].get(adate(dk),0) for n,_,_ in LOCS)) if sum(retail[n]["daily"].get(adate(dk),0) for n,_,_ in LOCS)>0 else "\u2014")+"</td>" for dk in DAY_KEYS)
retail_day_rows+="<tr class=\"total\"><td>TOTAL</td>"+tot_rc+"<td class=\"r mono\">"+fmt(grand_retail)+"</td><td class=\"r mono\">"+"{:.1f}%".format(grand_ret_pct)+"</td></tr>"

all_items={}
for name,_,_ in LOCS:
    for item,v in retail[name]["items"].items():
        if item not in all_items: all_items[item]={"qty":0,"amt":0}
        all_items[item]["qty"]+=v["qty"]; all_items[item]["amt"]+=v["amt"]
top10=sorted(all_items.items(),key=lambda x:-x[1]["amt"])[:10]
top_item_rows="".join("<tr><td>"+item+"</td><td class=\"c mono\">"+str(v["qty"])+"</td><td class=\"r mono\">"+fmt(v["amt"])+"</td></tr>" for item,v in top10)

ytd_rows=""; tot_ty=tot_ly=tot_lyfull=0
for name, cid, bid in LOCS:
    c=COLORS[name]; y=ytd_data[name]
    tot_ty+=y["ty_ytd"]; tot_ly+=y["ly_ytd"]; tot_lyfull+=y["ly_full"]
    if y["ty_ytd"]==0 and y["ly_ytd"]==0:
        ytd_rows+="<tr><td class=\"bold\"><span class=\"dot\" style=\"background:"+c+"\"></span>"+name+"</td><td colspan=\"6\" class=\"dim\" style=\"font-size:0.75rem\">No data yet</td></tr>"
        continue
    dc2="green" if y["diff"]>=0 else "red"
    bc="#22c55e" if y["pct"]>=10 else "#f97316" if y["pct"]>=0 else "#ef4444"
    prog=min(max((y["ty_ytd"]/y["ly_ytd"]*100) if y["ly_ytd"]>0 else 0,0),100)
    pb=("<div style=\"background:#e2e2d8;border-radius:4px;height:8px;min-width:100px\"><div style=\"background:"+bc+";height:8px;border-radius:4px;width:"+"{:.1f}".format(prog)+"%\"></div></div>"
        "<div style=\"font-size:0.65rem;color:"+bc+";margin-top:3px;font-family:'DM Mono',monospace\">"+("+" if y["pct"]>=0 else "")+"{:.1f}%".format(y["pct"])+" vs LY</div>")
    ytd_rows+=("<tr><td class=\"bold\"><span class=\"dot\" style=\"background:"+c+"\"></span>"+name+"</td>"
               "<td class=\"r mono bold green\">"+fmt(y["ty_ytd"])+"</td>"
               "<td class=\"r mono\">"+fmt(y["ly_ytd"])+"</td>"
               "<td class=\"r mono "+dc2+"\">"+("+" if y["diff"]>=0 else "")+fmt(y["diff"])+"</td>"
               "<td class=\"r mono\">"+fmt(y["ly_full"])+"</td>"
               "<td class=\"r mono\">"+fmt(y["proj"])+"</td>"
               "<td style=\"min-width:120px\">"+pb+"</td></tr>")
tot_diff=tot_ty-tot_ly; tot_proj=sum(ytd_data[n]["proj"] for n,_,_ in LOCS)
ytd_rows+=("<tr class=\"total\"><td>TOTAL</td>"
           "<td class=\"r mono\">"+fmt(tot_ty)+"</td>"
           "<td class=\"r mono\">"+fmt(tot_ly)+"</td>"
           "<td class=\"r mono "+("green" if tot_diff>=0 else "red")+"\">"+("+" if tot_diff>=0 else "")+fmt(tot_diff)+"</td>"
           "<td class=\"r mono\">"+fmt(tot_lyfull)+"</td>"
           "<td class=\"r mono\">"+fmt(tot_proj)+"</td><td></td></tr>")



# ── TREND DATA PULLS ──────────────────────────────────────────────────────────
# Pulls 8 weeks + 12 months of daycare/boarding/grooming counts + retail revenue
# for each location. Used in the Trends section of Executive View.


# ── DAILY SCORECARD DATA PULLS ────────────────────────────────────────────────
# For each location: today's counts vs same day last week, last month, last year
# Plus avg of last 5 same-days-of-week (e.g. last 5 Thursdays)

log("Pulling daily scorecard data...")

from datetime import date as _date, timedelta as _td
import calendar as _cal

today_d    = today.date()
dow        = today_d.weekday()  # 0=Mon, 6=Sun
day_name   = today_d.strftime("%A")

def day_range(d):
    """Return (start_str, end_str) for a single date."""
    return (d.strftime("%Y-%m-%dT00:00:00Z"), d.strftime("%Y-%m-%dT23:59:59Z"))

def count_day(cid, bid, d, report_id):
    """Pull appointment count for a single day."""
    s, e = day_range(d)
    r = api_post({"pagination":{"pageSize":500,"pageToken":"1"},
                  "companyId":cid,"businessIds":[bid],
                  "condition":{"id":report_id,"queryPeriod":{"startTime":s,"endTime":e}}})
    return len(r.get("tableData",{}).get("rows",[]))

def retail_day(cid, bid, d):
    """Pull retail revenue for a single day."""
    s, e = day_range(d)
    all_rows, page = [], "1"
    while True:
        r = api_post({"pagination":{"pageSize":500,"pageToken":page},
                      "companyId":cid,"businessIds":[bid],
                      "condition":{"id":"reports_sales_invoice_item",
                                   "queryPeriod":{"startTime":s,"endTime":e}}})
        rows = r.get("tableData",{}).get("rows",[])
        all_rows.extend(rows)
        npt = r.get("nextPageToken","")
        if not npt or npt == page or len(rows) < 500: break
        page = npt
    return sum(money(row["data"],"net_sales") for row in all_rows
               if row["data"].get("category",{}).get("value",{}).get("string","") == "Product")

# Reference dates
same_day_last_week  = today_d - _td(weeks=1)
same_day_last_month = today_d.replace(month=today_d.month-1 if today_d.month>1 else 12,
                                       year=today_d.year if today_d.month>1 else today_d.year-1)
# Same day of week last year (closest same weekday)
ly_approx = today_d.replace(year=today_d.year-1)
ly_dow    = ly_approx.weekday()
ly_offset = (dow - ly_dow) % 7
same_dow_last_year  = ly_approx + _td(days=ly_offset)

# Last 5 same days of week (excluding today)
last_5_same_dow = [today_d - _td(weeks=i) for i in range(1, 6)]

scorecard = {}
for name, cid, bid in LOCS:
    def pull_day(d):
        dc  = count_day(cid, bid, d, "reports_daycare_appointment_list")
        bo  = count_day(cid, bid, d, "reports_boarding_appointment_list")
        gr  = count_day(cid, bid, d, "reports_appointment_list")
        ret = retail_day(cid, bid, d)
        return {"dc":dc, "bo":bo, "gr":gr, "retail":ret}

    today_data = pull_day(today_d)
    lw_data    = pull_day(same_day_last_week)
    lm_data    = pull_day(same_day_last_month)
    ly_data    = pull_day(same_dow_last_year)

    # Average of last 5 same days of week
    dow_data = [pull_day(d) for d in last_5_same_dow]
    avg_data = {k: sum(d[k] for d in dow_data) / len(dow_data) for k in ["dc","bo","gr","retail"]}

    scorecard[name] = {
        "today": today_data,
        "last_week": lw_data,
        "last_month": lm_data,
        "last_year": ly_data,
        "avg": avg_data,
    }
    log(f"  Scorecard {name}: DC={today_data['dc']} BO={today_data['bo']} GR={today_data['gr']} Retail={fmt(today_data['retail'])}")

log("Scorecard data complete.")
# ── TOMORROW DATA PULL ─────────────────────────────────────────────────────────
log("Pulling tomorrow's bookings...")
tomorrow_d = today_d + _td(days=1)
tomorrow_counts = {}
for name, cid, bid in LOCS:
    dc = count_day(cid, bid, tomorrow_d, "reports_daycare_appointment_list")
    bo = count_day(cid, bid, tomorrow_d, "reports_boarding_appointment_list")
    snp_tm_count = count_day(cid, bid, tomorrow_d, "reports_boarding_appointment_list")
    tomorrow_counts[name] = {"daycare": dc, "boarding": bo, "snp": 0}
    log(f"  Tomorrow {name}: DC={dc} BO={bo}")
log("Tomorrow data complete.")



# ── BUILD SCORECARD HTML ───────────────────────────────────────────────────────
def delta_badge(today_val, bench_val, is_money=False):
    """Return colored +/- badge comparing today to benchmark."""
    if bench_val == 0: return "<span style=\"color:var(--muted);font-size:0.7rem\">—</span>"
    diff = today_val - bench_val
    pct  = (diff / bench_val * 100)
    cls  = "color:var(--green)" if diff >= 0 else "color:var(--red)"
    sign = "+" if diff >= 0 else ""
    return f"<span style=\"font-size:0.7rem;font-family:'DM Mono',monospace;{cls}\">{sign}{pct:.0f}%</span>"

def fmt_count(v):
    return str(int(round(v))) if v else "—"

scorecard_html = ""
for name, cid, bid in LOCS:
    sc = scorecard[name]
    c  = COLORS[name]
    td = sc["today"]; lw = sc["last_week"]; lm = sc["last_month"]; ly = sc["last_year"]; av = sc["avg"]

    if td["dc"]==0 and td["bo"]==0 and td["gr"]==0:
        scorecard_html += (
            f"<div class=\"sc-card\" style=\"--accent:{c};opacity:0.4\">"
            f"<div class=\"sc-name\">{name}</div>"
            f"<div style=\"font-size:0.75rem;color:var(--muted);padding:12px 0\">No data today</div>"
            f"</div>"
        )
        continue

    def metric_row(label, tag, key, is_money=False):
        fmt_fn = fmt if is_money else fmt_count
        avg_fmt = fmt(av[key]) if is_money else f"{av[key]:.1f}"
        return (
            f"<div class=\"sc-row\">"
            f"<div class=\"sc-metric\"><span class=\"tag {tag}\">{label}</span></div>"
            f"<div class=\"sc-val\">{fmt_fn(td[key])}</div>"
            f"<div class=\"sc-bench\">{fmt_fn(lw[key])} {delta_badge(td[key],lw[key],is_money)}</div>"
            f"<div class=\"sc-bench\">{fmt_fn(lm[key])} {delta_badge(td[key],lm[key],is_money)}</div>"
            f"<div class=\"sc-bench\">{fmt_fn(ly[key])} {delta_badge(td[key],ly[key],is_money)}</div>"
            f"<div class=\"sc-bench\">{avg_fmt} {delta_badge(td[key],av[key],is_money)}</div>"
            f"</div>"
        )

    scorecard_html += (
        f"<div class=\"sc-card\" style=\"--accent:{c}\">"
        f"<div class=\"sc-name\">{name}</div>"
        f"<div class=\"sc-header-row\">"
        f"<div class=\"sc-metric\"></div>"
        f"<div class=\"sc-val-hdr\">Today</div>"
        f"<div class=\"sc-bench-hdr\">Last {day_name}</div>"
        f"<div class=\"sc-bench-hdr\">Last Month</div>"
        f"<div class=\"sc-bench-hdr\">Last Year</div>"
        f"<div class=\"sc-bench-hdr\">5-{day_name} Avg</div>"
        f"</div>"
        + metric_row("Daycare",  "dc", "dc")
        + metric_row("Boarding", "bo", "bo")
        + metric_row("Grooming", "gr", "gr")
        + metric_row("Retail",   "ms", "retail", is_money=True)
        + "</div>"
    )



# ── LABOR CALCULATIONS ────────────────────────────────────────────────────────
DAY_ORDER = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
DOW_MAP   = {0:"Mon",1:"Tue",2:"Wed",3:"Thu",4:"Fri",5:"Sat",6:"Sun"}

def labor_wtd(name):
    """WTD labor $ — sum days up to and including today."""
    today_dow = today.weekday()  # 0=Mon
    total = 0
    for i, d in enumerate(DAY_ORDER):
        if i <= today_dow:
            total += LABOR[name].get(d, 0)
    return total

def labor_pct(name):
    """WTD labor % vs WTD revenue."""
    rev = loc_total(name, "expected")
    lab = labor_wtd(name)
    return (lab / rev * 100) if rev > 0 else 0

def labor_color(pct):
    if pct == 0:   return "var(--muted)"
    if pct <= 30:  return "var(--green)"
    if pct <= 35:  return "#d97706"
    return "var(--red)"

def labor_badge(pct):
    c = labor_color(pct)
    if pct == 0: return "<span style='color:var(--muted);font-size:0.8rem'>No data</span>"
    return f"<span style='color:{c};font-family:DM Mono,monospace;font-weight:700'>{pct:.1f}%</span>"

# Labor summary bar (all locations)
grand_labor_wtd = sum(labor_wtd(n) for n,_,_ in LOCS)
grand_labor_pct = (grand_labor_wtd / grand_exp * 100) if grand_exp > 0 else 0

# Labor rows for Full Detail table
labor_rows = ""
for name, cid, bid in LOCS:
    c   = COLORS[name]
    lab = LABOR[name]
    wtd = labor_wtd(name)
    rev = loc_total(name, "expected")
    pct = labor_pct(name)
    lc  = labor_color(pct)
    today_dow = today.weekday()
    day_cells = ""
    for i, d in enumerate(DAY_ORDER):
        v = lab.get(d, 0)
        if i > today_dow:
            day_cells += "<td class='r mono dim'>—</td>"
        elif v == 0:
            day_cells += "<td class='r mono dim'>—</td>"
        else:
            day_cells += f"<td class='r mono'>{fmt(v)}</td>"
    labor_rows += (
        f"<tr><td class='bold'><span class='dot' style='background:{c}'></span>{name}</td>"
        f"{day_cells}"
        f"<td class='r mono bold'>{fmt(wtd)}</td>"
        f"<td class='r mono bold' style='color:{lc}'>{pct:.1f}%</td>"
        f"<td class='r mono' style='color:var(--muted)'>{fmt(rev)}</td></tr>"
    )
# Total row
grand_today_dow = today.weekday()
grand_day_cells = ""
for i, d in enumerate(DAY_ORDER):
    if i > grand_today_dow:
        grand_day_cells += "<td class='r mono dim'>—</td>"
    else:
        dv = sum(LABOR[n].get(d,0) for n,_,_ in LOCS)
        grand_day_cells += f"<td class='r mono'>{'—' if dv==0 else fmt(dv)}</td>"
glc = labor_color(grand_labor_pct)
labor_rows += (
    f"<tr class='total'><td>TOTAL</td>{grand_day_cells}"
    f"<td class='r mono'>{fmt(grand_labor_wtd)}</td>"
    f"<td class='r mono' style='color:{glc}'>{grand_labor_pct:.1f}%</td>"
    f"<td class='r mono'>{fmt(grand_exp)}</td></tr>"
)

# Compact labor summary for exec cards and GM cards
labor_summary_html = ""
for name, cid, bid in LOCS:
    pct = labor_pct(name)
    lc  = labor_color(pct)
    wtd = labor_wtd(name)
    labor_summary_html += (
        f"<div style='display:flex;justify-content:space-between;align-items:center;"
        f"padding:5px 0;border-bottom:1px solid var(--border);font-size:0.82rem;'>"
        f"<span style='color:var(--muted2);font-weight:500'>"
        f"<span class='dot' style='background:{COLORS[name]}'></span>{name}</span>"
        f"<span style='font-family:DM Mono,monospace;font-weight:700;color:{lc}'>"
        f"{fmt(wtd)} &nbsp;·&nbsp; {pct:.1f}%</span></div>"
    )

CSS = (
":root{--bg:#f5f5f0;--surface:#fff;--surface2:#f0f0eb;--border:#e2e2d8;--text:#1a1a1a;--muted:#888;--muted2:#555;--red:#dc2626;--green:#16a34a;}"
"*{margin:0;padding:0;box-sizing:border-box;}"
"body{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;font-size:15px;}"
"header{padding:20px 36px;background:var(--surface);border-bottom:2px solid var(--border);display:flex;align-items:center;justify-content:space-between;}"
".logo{font-family:'Bebas Neue',sans-serif;font-size:2.2rem;letter-spacing:3px;color:#1a1a1a;}.logo span{color:#ea580c;}"
".meta{text-align:right;font-family:'DM Mono',monospace;font-size:0.78rem;color:var(--muted);line-height:2;}"
".tabs{display:flex;background:var(--surface);border-bottom:2px solid var(--border);padding:0 36px;}"
".tab{padding:14px 28px;font-size:0.85rem;font-weight:600;color:var(--muted);cursor:pointer;border-bottom:3px solid transparent;margin-bottom:-2px;text-transform:uppercase;}"
".tab:hover{color:var(--text);}.tab.active{color:#ea580c;border-bottom-color:#ea580c;}"
".tab-content{display:none;}.tab-content.active{display:block;}"
".green{color:var(--green)!important;}.red{color:var(--red)!important;}.dim{color:var(--muted)!important;}"
".summary{display:flex;flex-wrap:wrap;background:var(--surface);border-bottom:1px solid var(--border);}"
".sstat{padding:20px 24px;text-align:center;border-right:1px solid var(--border);}.sstat:last-child{border-right:none;}"
".sstat .v{font-family:'Bebas Neue',sans-serif;font-size:2rem;letter-spacing:1px;color:#1a1a1a;}"
".sstat .l{font-size:0.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:1.5px;margin-top:4px;font-weight:500;}"
".cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));background:var(--border);border-bottom:1px solid var(--border);gap:1px;}"
".card{background:var(--surface);padding:22px 18px;position:relative;}"
".card::before{content:'';position:absolute;top:0;left:0;right:0;height:4px;background:var(--accent);}"
".card-name{font-family:'Bebas Neue',sans-serif;font-size:1rem;letter-spacing:1.5px;color:var(--accent);margin-bottom:10px;}"
".card-rev{font-family:'Bebas Neue',sans-serif;font-size:1.9rem;color:#1a1a1a;letter-spacing:1px;line-height:1;}"
".card-revlbl{font-size:0.68rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;margin-top:2px;}"
".kpi{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;}"
".kpi-l{font-size:0.78rem;color:var(--muted2);font-weight:500;}.kpi-v{font-family:'DM Mono',monospace;font-size:0.82rem;font-weight:500;}"
".divider{height:1px;background:var(--border);margin:10px 0;}"
".svc-row{display:flex;flex-direction:column;gap:4px;}"
".svc{font-size:0.74rem;padding:4px 8px;border-radius:4px;display:flex;justify-content:space-between;align-items:center;font-weight:500;}"
".svc.dc{background:#fff3e8;color:#c2410c;}.svc.bo{background:#f3e8ff;color:#7e22ce;}.svc.gr{background:#e8f0ff;color:#1d4ed8;}.svc.ms{background:#e8f8ee;color:#15803d;}"
".notice{background:#fef2f2;border:1px solid #fecaca;border-radius:6px;padding:8px 10px;font-size:0.72rem;color:#b91c1c;margin-top:10px;}"
".section{padding:28px 36px;border-bottom:1px solid var(--border);background:var(--surface);}"
".section-title{font-family:'Bebas Neue',sans-serif;font-size:1rem;letter-spacing:2.5px;color:var(--muted);text-transform:uppercase;margin-bottom:16px;padding-bottom:10px;border-bottom:1px solid var(--border);}"
"table{width:100%;border-collapse:collapse;}"
"th{font-size:0.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px;padding:9px 12px;border-bottom:2px solid var(--border);font-weight:600;white-space:nowrap;background:var(--surface2);}"
"th.r,td.r{text-align:right;}th.c,td.c{text-align:center;}"
"td{padding:11px 12px;font-size:0.85rem;border-bottom:1px solid var(--border);white-space:nowrap;}"
"td.mono{font-family:'DM Mono',monospace;font-size:0.82rem;}td.bold{font-weight:700;}"
"tr:hover td{background:#fafaf8;}"
"tr.total{background:var(--surface2);}tr.total td{font-weight:700;border-bottom:none;border-top:2px solid var(--border);}"
"tr.subrow td{background:#fafaf8;font-size:0.8rem;color:var(--muted2);padding:6px 12px 6px 28px;}"
".dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:8px;vertical-align:middle;}"
".note{margin-top:12px;font-size:0.74rem;color:var(--muted);font-family:'DM Mono',monospace;background:var(--surface2);padding:8px 12px;border-radius:4px;border-left:3px solid var(--border);}"
".tag{display:inline-block;font-size:0.7rem;padding:2px 7px;border-radius:3px;margin-left:4px;vertical-align:middle;font-weight:500;}"
".tag.dc{background:#fff3e8;color:#c2410c;}.tag.bo{background:#f3e8ff;color:#7e22ce;}.tag.gr{background:#e8f0ff;color:#1d4ed8;}.tag.ms{background:#e8f8ee;color:#15803d;}"
".exec-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px;padding:8px;background:var(--bg);}"
".exec-card{background:var(--surface);border-radius:8px;padding:20px;border:1px solid var(--border);border-top:4px solid var(--accent);}"
".exec-card-name{font-family:'Bebas Neue',sans-serif;font-size:0.9rem;letter-spacing:1.5px;color:var(--accent);margin-bottom:12px;}"
".exec-card-rev{font-family:'Bebas Neue',sans-serif;font-size:1.7rem;color:#1a1a1a;line-height:1;}"
".exec-card-sub{font-size:0.68rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;margin-top:2px;}"
".exec-kpi{display:flex;justify-content:space-between;margin-bottom:7px;font-size:0.8rem;}"
".exec-kpi-l{color:var(--muted2);font-weight:500;}.exec-kpi-v{font-family:'DM Mono',monospace;font-weight:600;}"
".tl{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:middle;}"
".tl.green{background:#16a34a;}.tl.yellow{background:#d97706;}.tl.red{background:#dc2626;}"
".exec-bonus-bar{height:6px;background:#e2e2d8;border-radius:4px;margin-top:6px;}"
".exec-bonus-fill{height:6px;border-radius:4px;}"
".exec-summary{display:flex;flex-wrap:wrap;background:var(--surface);border-bottom:1px solid var(--border);border-top:1px solid var(--border);}"
".exec-stat{padding:16px 20px;text-align:center;border-right:1px solid var(--border);}.exec-stat:last-child{border-right:none;}"
".exec-stat .v{font-family:'Bebas Neue',sans-serif;font-size:1.7rem;color:#1a1a1a;}"
".exec-stat .l{font-size:0.67rem;color:var(--muted);text-transform:uppercase;letter-spacing:1.5px;margin-top:3px;font-weight:500;}"
".alert-banner{margin:16px 36px;padding:12px 20px;border-radius:6px;font-size:0.85rem;font-weight:500;display:flex;align-items:center;gap:10px;}"
".alert-banner.warn{background:#fefce8;border:1px solid #fde047;color:#854d0e;}"
".alert-banner.good{background:#f0fdf4;border:1px solid #86efac;color:#166534;}"
".gm-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px;padding:8px;background:var(--bg);}"
".gm-card{background:var(--surface);border-radius:8px;border:1px solid var(--border);overflow:hidden;min-width:0;}"
".gm-card-header{padding:14px 18px;border-bottom:1px solid var(--border);border-top:4px solid var(--accent);}"
".gm-card-name{font-family:'Bebas Neue',sans-serif;font-size:1rem;letter-spacing:1.5px;color:var(--accent);}"
".gm-card-body{padding:16px 18px;}"
".gm-stat{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border);font-size:0.82rem;}"
".gm-stat:last-child{border-bottom:none;}"
".gm-stat-l{color:var(--muted2);font-weight:500;}.gm-stat-v{font-family:'DM Mono',monospace;font-weight:600;font-size:0.82rem;}"
".gm-bonus-section{padding:14px 18px;background:var(--surface2);border-top:1px solid var(--border);}"
".gm-bonus-title{font-size:0.68rem;text-transform:uppercase;letter-spacing:1px;color:var(--muted);font-weight:600;margin-bottom:8px;}"
".gm-bonus-bar{height:8px;background:#e2e2d8;border-radius:4px;margin-bottom:5px;}"
".gm-bonus-fill{height:8px;border-radius:4px;}.gm-bonus-pct{font-family:'DM Mono',monospace;font-size:0.78rem;font-weight:600;}"
".gm-retail-item{display:flex;justify-content:space-between;font-size:0.76rem;padding:3px 0;border-bottom:1px solid var(--border);color:var(--muted2);}"
".gm-retail-item:last-child{border-bottom:none;}.gm-retail-item span{font-family:'DM Mono',monospace;color:var(--text);font-weight:500;}"
".status-badge{display:inline-flex;align-items:center;gap:4px;font-size:0.72rem;font-weight:600;padding:2px 7px;border-radius:10px;}"
".status-badge.ahead{background:#f0fdf4;color:#15803d;}.status-badge.on-pace{background:#fefce8;color:#854d0e;}.status-badge.behind{background:#fef2f2;color:#b91c1c;}"
# Trend styles
".trend-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:20px;}"
".trend-card{background:var(--surface);border-radius:8px;border:1px solid var(--border);padding:20px;}"
".trend-card-title{font-family:'Bebas Neue',sans-serif;font-size:0.95rem;letter-spacing:2px;color:var(--muted);text-transform:uppercase;margin-bottom:14px;}"
".trend-chart{display:flex;align-items:flex-end;gap:4px;height:140px;padding-bottom:36px;position:relative;}"
".trend-col{display:flex;flex-direction:column;align-items:center;flex:1;gap:2px;}"
".trend-bars{display:flex;flex-direction:column-reverse;align-items:center;width:100%;height:80px;gap:1px;}"
".trend-seg{width:100%;border-radius:1px;transition:opacity 0.2s;}"
".trend-seg:hover{opacity:1!important;}"
".trend-total{font-family:'DM Mono',monospace;font-size:0.65rem;font-weight:600;color:var(--text);white-space:nowrap;}"
".trend-chg-pos{font-family:'DM Mono',monospace;font-size:0.6rem;color:var(--green);}"
".trend-chg-neg{font-family:'DM Mono',monospace;font-size:0.6rem;color:var(--red);}"
".trend-lbl{font-size:0.6rem;color:var(--muted);margin-top:2px;white-space:nowrap;}"
".trend-toggles{display:flex;gap:6px;}"
".trend-btn{padding:6px 14px;border:1px solid var(--border);background:var(--surface);border-radius:20px;font-size:0.75rem;font-weight:600;color:var(--muted);cursor:pointer;}"
".trend-btn.active{background:#ea580c;border-color:#ea580c;color:#fff;}"
".trend-legend{display:flex;gap:12px;flex-wrap:wrap;font-size:0.72rem;color:var(--muted2);}"
".trend-legend-item{display:flex;align-items:center;gap:4px;}"

# Scorecard styles
".sc-grid{display:grid;grid-template-columns:repeat(1,1fr);gap:12px;}"
".sc-card{background:var(--surface);border-radius:8px;border:1px solid var(--border);border-left:4px solid var(--accent);padding:16px 20px;}"
".sc-name{font-family:'Bebas Neue',sans-serif;font-size:1rem;letter-spacing:1.5px;color:var(--accent);margin-bottom:10px;}"
".sc-header-row{display:grid;grid-template-columns:130px 80px repeat(4,1fr);gap:8px;padding:6px 0;border-bottom:2px solid var(--border);margin-bottom:4px;}"
".sc-row{display:grid;grid-template-columns:130px 80px repeat(4,1fr);gap:8px;padding:7px 0;border-bottom:1px solid var(--border);align-items:center;}"
".sc-row:last-child{border-bottom:none;}"
".sc-val-hdr,.sc-bench-hdr{font-size:0.68rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px;font-weight:600;text-align:right;}"
".sc-val-hdr{color:var(--text);}"
".sc-val{font-family:'DM Mono',monospace;font-size:0.95rem;font-weight:700;text-align:right;}"
".sc-bench{font-family:'DM Mono',monospace;font-size:0.82rem;text-align:right;display:flex;align-items:center;justify-content:flex-end;gap:4px;}"
".sc-metric{font-size:0.8rem;}"
".labor-bar{display:flex;flex-wrap:wrap;background:var(--surface);border-bottom:1px solid var(--border);}"
".labor-stat{padding:14px 20px;text-align:center;border-right:1px solid var(--border);}.labor-stat:last-child{border-right:none;}"
".labor-stat .v{font-family:'DM Mono',sans-serif;font-size:1.4rem;font-weight:700;}"
".labor-stat .l{font-size:0.68rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-top:2px;}"
".cap-grid{display:flex;flex-direction:column;gap:0;}.cap-row{display:grid;grid-template-columns:180px repeat(3,1fr);gap:16px;align-items:center;padding:12px 0;border-bottom:1px solid var(--border);}.cap-row:last-child{border-bottom:none;}.cap-name{font-size:0.82rem;font-weight:600;}.cap-metric{display:flex;flex-direction:column;gap:3px;}.cap-lbl{font-size:0.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px;font-weight:600;}.cap-bar-wrap{height:7px;background:#e2e2d8;border-radius:4px;overflow:hidden;}.cap-bar-fill{height:7px;border-radius:4px;}.cap-val{font-family:'DM Mono',monospace;font-size:0.75rem;font-weight:600;}"
".cc-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px;padding:8px;background:var(--bg);}.cc-card{background:var(--surface);border-radius:10px;border:1px solid var(--border);overflow:hidden;min-width:0;}.cc-card-header{padding:10px 14px;display:flex;align-items:center;gap:8px;border-bottom:1px solid var(--border);}.cc-card-name{font-size:0.78rem;font-weight:700;}.cc-card-body{padding:12px 14px;display:flex;flex-direction:column;gap:8px;}.cc-metric{display:flex;justify-content:space-between;align-items:baseline;}.cc-metric-label{font-size:0.68rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.8px;}.cc-metric-val{font-family:'DM Mono',monospace;font-size:0.88rem;font-weight:700;}.cc-delta{font-size:0.68rem;font-family:'DM Mono',monospace;margin-left:4px;}.cc-section-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px;padding:0 8px 8px;}.cc-mini{background:var(--surface);border-radius:8px;border:1px solid var(--border);padding:10px 12px;min-width:0;}.cc-mini-title{font-size:0.65rem;text-transform:uppercase;letter-spacing:1px;color:var(--muted);font-weight:600;margin-bottom:6px;}.cc-mini-val{font-family:'DM Mono',monospace;font-size:1.1rem;font-weight:700;}.cc-mini-sub{font-size:0.68rem;color:var(--muted);margin-top:2px;}.cc-row{display:flex;justify-content:space-between;align-items:center;padding:3px 0;border-bottom:1px solid var(--border);font-size:0.75rem;}.cc-row:last-child{border-bottom:none;}.cc-row-label{color:var(--muted);}.cc-row-val{font-family:'DM Mono',monospace;font-weight:600;}.cc-bonus-bar{height:6px;background:#e2e2d8;border-radius:3px;overflow:hidden;margin:4px 0;}.cc-bonus-fill{height:6px;border-radius:3px;}.sparkbar{display:inline-flex;align-items:flex-end;gap:2px;height:24px;vertical-align:middle;margin-left:6px;}.sparkbar span{width:6px;border-radius:2px 2px 0 0;display:inline-block;}.cc-tomorrow{background:var(--surface);border-radius:8px;border:1px solid var(--border);padding:10px 12px;}.cc-tmr-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px;padding:0 8px 8px;}.green{color:var(--green);} .red{color:var(--red);} .yellow{color:#d97706;}"
)

unp_color = "red" if grand_unp > 0 else "green"

def traffic(val, good=5.0, warn=0.0):
    return "green" if val>=good else "yellow" if val>=warn else "red"

exec_cards = ""
for name, cid, bid in LOCS:
    c=COLORS[name]; q=q1_data[name]; y=ytd_data[name]
    exp=loc_total(name,"expected"); unp=loc_total(name,"unpaid")
    lw=last_week_rev[name]; wow_pct=((exp-lw)/lw*100) if lw>0 else 0
    q1_prog=q["progress"]
    if exp==0 and q["ty_qtd"]==0: continue
    bc="#16a34a" if q1_prog>=90 else "#d97706" if q1_prog>=70 else "#dc2626"
    exec_cards += (
        "<div class=\"exec-card\" style=\"--accent:"+c+";\">"
        "<div class=\"exec-card-name\">"+name+"</div>"
        "<div class=\"exec-card-rev\">"+fmt(exp)+"</div>"
        "<div class=\"exec-card-sub\">Week to Date</div>"
        "<div class=\"exec-kpi\"><span class=\"exec-kpi-l\"><span class=\"tl "+traffic(wow_pct)+"\"></span>vs Last Week</span>"
        "<span class=\"exec-kpi-v "+("green" if wow_pct>=0 else "red")+"\">"+("+" if wow_pct>=0 else "")+"{:.1f}%".format(wow_pct)+"</span></div>"
        "<div class=\"exec-kpi\"><span class=\"exec-kpi-l\"><span class=\"tl "+traffic(y["pct"],10,0)+"\"></span>YTD vs LY</span>"
        "<span class=\"exec-kpi-v "+("green" if y["pct"]>=0 else "red")+"\">"+("+" if y["pct"]>=0 else "")+"{:.1f}%".format(y["pct"])+"</span></div>"
        "<div class=\"exec-kpi\"><span class=\"exec-kpi-l\"><span class=\"tl "+("green" if unp==0 else "red")+"\"></span>Unpaid</span>"
        "<span class=\"exec-kpi-v "+("red" if unp>0 else "green")+"\">"+fmt(unp)+"</span></div>"
        "<div class=\"exec-kpi\"><span class=\"exec-kpi-l\">Retail WTD</span><span class=\"exec-kpi-v\">"+fmt(retail[name]["total"])+"</span></div>"
        "<div class=\\\"exec-kpi\\\"><span class=\\\"exec-kpi-l\\\">Labor %</span><span class=\\\"exec-kpi-v\\\" style=\\\"color:"+labor_color(labor_pct(name))+"\\\">"+("\u2014" if labor_pct(name)==0 else "{:.1f}%".format(labor_pct(name)))+"</span></div>"
        "<div style=\"margin-top:8px;font-size:0.68rem;color:var(--muted2);font-weight:500;\">Q1 BONUS</div>"
        "<div class=\"exec-bonus-bar\"><div class=\"exec-bonus-fill\" style=\"width:"+"{:.1f}".format(min(q1_prog,100))+"%;background:"+bc+"\"></div></div>"
        "<div style=\"font-size:0.7rem;font-family:'DM Mono',monospace;color:"+bc+";margin-top:3px;\">"+"{:.1f}".format(q1_prog)+"% &nbsp;&#183;&nbsp; Gap: "+fmt(q["gap"])+"</div>"
        "</div>"
    )

alerts_html = ("<div class=\"alert-banner warn\">&#9888; Unpaid balance of "+fmt(grand_unp)+" requires follow-up</div>"
               if grand_unp>0 else
               "<div class=\"alert-banner good\">&#10003; All balances collected this week</div>")

gm_cards = ""
for name, cid, bid in LOCS:
    c=COLORS[name]; q=q1_data[name]; y=ytd_data[name]
    exp=loc_total(name,"expected"); unp=loc_total(name,"unpaid")
    lw=last_week_rev[name]; bd=boarding_nights[name]; cl=clients[name]
    wow_pct=((exp-lw)/lw*100) if lw>0 else 0
    if exp==0 and q["ty_qtd"]==0: continue
    bc="#16a34a" if q["progress"]>=90 else "#d97706" if q["progress"]>=70 else "#dc2626"
    if q["progress"]>=90:   badge="<span class=\"status-badge ahead\">&#9679; Ahead</span>"
    elif q["progress"]>=70: badge="<span class=\"status-badge on-pace\">&#9679; On Pace</span>"
    else:                   badge="<span class=\"status-badge behind\">&#9679; Behind</span>"
    top3=sorted(retail[name]["items"].items(),key=lambda x:-x[1]["amt"])[:3]
    ri = ("".join("<div class=\"gm-retail-item\">"+item[:24]+("..." if len(item)>24 else "")+"<span>"+fmt(v["amt"])+"</span></div>" for item,v in top3) or "<div class=\"gm-retail-item\" style=\"color:var(--muted)\">No retail this week</div>")
    card = "<div class=\"gm-card\" style=\"--accent:"+c+";\">"
    card += "<div class=\"gm-card-header\"><div class=\"gm-card-name\">"+name+"</div><div style=\"margin-top:4px\">"+badge+"</div></div>"
    card += "<div class=\"gm-card-body\">"
    card += "<div class=\"gm-stat\"><span class=\"gm-stat-l\">Revenue WTD</span><span class=\"gm-stat-v\">"+fmt(exp)+"</span></div>"
    card += "<div class=\"gm-stat\"><span class=\"gm-stat-l\">vs Last Week</span><span class=\"gm-stat-v "+("green" if wow_pct>=0 else "red")+"\">"+("+\u200b" if wow_pct>=0 else "")+"{:.1f}%".format(wow_pct)+"</span></div>"
    card += "<div class=\"gm-stat\"><span class=\"gm-stat-l\">YTD vs LY</span><span class=\"gm-stat-v "+("green" if y["pct"]>=0 else "red")+"\">"+("+" if y["pct"]>=0 else "")+"{:.1f}%".format(y["pct"])+"</span></div>"
    card += "<div class=\"gm-stat\"><span class=\"gm-stat-l\">2026 YTD</span><span class=\"gm-stat-v\">"+fmt(y["ty_ytd"])+"</span></div>"
    card += "<div class=\"gm-stat\"><span class=\"gm-stat-l\">Unpaid</span><span class=\"gm-stat-v "+("red" if unp>0 else "green")+"\">"+ fmt(unp)+"</span></div>"
    card += "<div class=\"gm-stat\"><span class=\"gm-stat-l\">Clients</span><span class=\"gm-stat-v\">"+"{:,}".format(cl["total"])+" ("+str(cl["new"])+" new)</span></div>"
    card += "<div class=\"gm-stat\"><span class=\"gm-stat-l\">Boarding</span><span class=\"gm-stat-v\">"+str(bd["dogs"])+" dogs / "+str(bd["nights"])+" nights</span></div>"
    card += "<div class=\"gm-stat\"><span class=\"gm-stat-l\">Retail WTD</span><span class=\"gm-stat-v\">"+fmt(retail[name]["total"])+"</span></div>"
    card += "<div class=\\\"gm-stat\\\"><span class=\\\"gm-stat-l\\\">Labor %</span><span class=\\\"gm-stat-v\\\" style=\\\"color:"+labor_color(labor_pct(name))+"\\\">"+("—" if labor_pct(name)==0 else "{:.1f}%".format(labor_pct(name)))+"</span></div>"
    card += "<div class=\"gm-bonus-section\">"
    card += "<div class=\"gm-bonus-title\">Q1 Bonus ("+"{:.0f}".format(q["pct"]*100)+"% target)</div>"
    card += "<div class=\"gm-bonus-bar\"><div class=\"gm-bonus-fill\" style=\"width:"+"{:.1f}".format(min(q["progress"],100))+"%;background:"+bc+"\"></div></div>"
    card += "<div class=\"gm-bonus-pct\" style=\"color:"+bc+"\">"+"{:.1f}".format(q["progress"])+"% reached</div>"
    card += "<div style=\"font-size:0.75rem;margin-top:6px;font-family:'DM Mono',monospace;\">"+fmt(q["ty_qtd"])+" / "+fmt(q["target"])+"</div>"
    card += "<div style=\"font-size:0.72rem;color:var(--muted2);margin-top:3px;\">Gap: "+fmt(q["gap"])+" &#183; "+str(q["days_left"])+"d left</div>"
    card += "<div style=\"margin-top:12px;font-size:0.68rem;text-transform:uppercase;letter-spacing:1px;color:var(--muted);font-weight:600;margin-bottom:5px;\">Top Retail</div>"
    card += ri + "</div></div>"
    gm_cards += card




# ── PIN PROTECTION WRAPPER ────────────────────────────────────────────────────
def pin_wrap(inner_html, pin, css, js_extra="", title="Central Bark Dashboard"):
    pin_css = """
#pin-screen{display:flex;align-items:center;justify-content:center;min-height:100vh;background:#f5f5f0;}
.pin-box{background:#fff;border:1px solid #e2e2d8;border-radius:12px;padding:48px 40px;text-align:center;width:320px;}
.pin-logo{font-family:'Bebas Neue',sans-serif;font-size:2rem;letter-spacing:3px;margin-bottom:8px;}
.pin-logo span{color:#ea580c;}
.pin-sub{font-size:0.8rem;color:#888;margin-bottom:28px;}
.pin-input{width:100%;padding:12px;border:2px solid #e2e2d8;border-radius:8px;font-size:1.1rem;text-align:center;letter-spacing:6px;font-family:'DM Mono',monospace;outline:none;margin-bottom:12px;box-sizing:border-box;}
.pin-input:focus{border-color:#ea580c;}
.pin-btn{width:100%;padding:12px;background:#ea580c;color:#fff;border:none;border-radius:8px;font-size:0.9rem;font-weight:600;cursor:pointer;}
.pin-err{color:#dc2626;font-size:0.8rem;margin-top:8px;display:none;}
#dashboard{display:none;}.five-col-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;padding:0 36px 28px;}}
"""
    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"UTF-8\">\n"
        "<meta name=\"viewport\" content=\"width=1200\">\n"
        f"<title>{title}</title>\n"
        "<link href=\"https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap\" rel=\"stylesheet\">\n"
        "<style>" + pin_css + css + "</style>\n"
        + f"""<script>
var CORRECT = "{pin}";
function tryPin() {{
  var v = document.getElementById("pin-input").value;
  if (v === CORRECT) {{
    document.getElementById("pin-screen").style.display = "none";
    document.getElementById("dashboard").style.display = "block";
    sessionStorage.setItem("cb_auth", CORRECT);
  }} else {{
    document.getElementById("pin-err").style.display = "block";
  }}
}}
window.onload = function() {{
  if (sessionStorage.getItem("cb_auth") === CORRECT) {{
    document.getElementById("pin-screen").style.display = "none";
    document.getElementById("dashboard").style.display = "block";
  }}
}};
document.addEventListener("keydown", function(e) {{ if (e.key === "Enter") tryPin(); }});

function showTab(id, el) {{
  document.querySelectorAll(".tab-content").forEach(function(t) {{ t.classList.remove("active"); }});
  document.querySelectorAll(".tab").forEach(function(t) {{ t.classList.remove("active"); }});
  document.getElementById(id).classList.add("active");
  el.classList.add("active");
}}
</script>
</head>
<body>
<div id="pin-screen">
  <div class="pin-box">
    <div class="pin-logo">Central <span>Bark</span></div>
    <div class="pin-sub">Enter your PIN to continue</div>
    <input id="pin-input" class="pin-input" type="password" maxlength="6" placeholder="****" autofocus>
    <button class="pin-btn" onclick="tryPin()">Unlock</button>
    <div id="pin-err" class="pin-err">Incorrect PIN. Try again.</div>
  </div>
</div>
<div id="dashboard">{inner_html}</div>
</body>
</html>"""
    )
# ── HTML BUILDERS ─────────────────────────────────────────────────────────────
def build_header():
    return (
        "<header><div class=\"logo\">Central <span>Bark</span></div>"
        "<div class=\"meta\">Week of "+WEEK_LABEL+" &nbsp;&middot;&nbsp; Updated "+UPDATED+"</div></header>"
    )


def build_labor_section():
    return (
        "<div class=\"section\"><div class=\"section-title\">Labor % This Week</div>"
        "<table><thead><tr><th>Location</th>"
        "<th class=\"r\">Mon</th><th class=\"r\">Tue</th><th class=\"r\">Wed</th>"
        "<th class=\"r\">Thu</th><th class=\"r\">Fri</th><th class=\"r\">Sat</th><th class=\"r\">Sun</th>"
        "<th class=\"r\">WTD Labor</th><th class=\"r\">Labor %</th><th class=\"r\">WTD Revenue</th>"
        "</tr></thead>"
        "<tbody>"+labor_rows+"</tbody></table>"
        "<div class=\"note\">Target: 32% &nbsp;&#183;&nbsp; Green ≤30% &nbsp;&#183;&nbsp; Yellow 30–35% &nbsp;&#183;&nbsp; Red >35%</div>"
        "</div>"
    )

def build_capacity_section(loc_filter=None):
    rows = ""
    for name, cid, bid in LOCS:
        if loc_filter and name != loc_filter: continue
        if name not in CAPACITY: continue
        c   = COLORS[name]
        cap = CAPACITY[name]
        dc  = today_counts.get(name, {}).get("daycare", 0)
        bo  = today_counts.get(name, {}).get("boarding", 0)
        rows += (
            "<div class=\"cap-row\">"
            "<div class=\"cap-name\"><span class=\"dot\" style=\"background:"+c+";\"></span>"+name+"</div>"
            "<div class=\"cap-metric\"><div class=\"cap-lbl\">Daycare</div>"+cap_bar_html(cap_pct(dc,cap["daycare"]),dc,cap["daycare"])+"</div>"
            "<div class=\"cap-metric\"><div class=\"cap-lbl\">Boarding</div>"+cap_bar_html(cap_pct(bo,cap["boarding"]),bo,cap["boarding"])+"</div>"
            "<div class=\"cap-metric\"><div class=\"cap-lbl\">SNP/DNP</div>"+cap_bar_html(cap_pct(bo,cap["snp"]),bo,cap["snp"])+"</div>"
            "</div>"
        )
    return (
        "<div class=\"section\"><div class=\"section-title\">Today\'s Capacity Utilization</div>"
        "<div class=\"cap-grid\">"+rows+"</div>"
        "<div class=\"note\">Green &lt;75% &nbsp;&#183;&nbsp; Yellow 75&#8211;90% &nbsp;&#183;&nbsp; Red &ge;90%</div>"
        "</div>"
    )

def build_command_center_tab(loc_filter=None):
    locs = [n for n,_,_ in LOCS] if loc_filter is None else [loc_filter]

    def pct_badge(val, base):
        if base == 0: return "<span style=\"color:var(--muted)\">—</span>"
        p = (val-base)/base*100
        col = "#16a34a" if p>=0 else "#dc2626"
        return "<span style=\"color:"+col+";font-weight:700\">"+("▲" if p>=0 else "▼")+" "+("{:+.1f}%".format(p))+"</span>"

    def row(label, val):
        return ("<div style=\"display:flex;justify-content:space-between;padding:5px 0;"
                "border-bottom:1px solid var(--border);\">"
                "<span style=\"font-size:0.68rem;text-transform:uppercase;color:var(--muted);font-weight:600\">"
                +label+"</span><span style=\"font-family:\'DM Mono\',monospace;font-size:0.82rem;font-weight:700\">"
                +str(val)+"</span></div>")

    def card(color, name, body):
        return ("<div style=\"border-radius:12px;border:1px solid var(--border);overflow:hidden;"
                "box-shadow:0 2px 8px rgba(0,0,0,0.05);\">"
                "<div style=\"height:4px;background:"+color+"\"></div>"
                "<div style=\"padding:14px 16px;\">"
                "<div style=\"font-size:0.8rem;font-weight:800;color:"+color+";margin-bottom:10px\">"
                +name+"</div>"+body+"</div></div>")

    def grid(cards):
        return "<div class=\"five-col-grid\">"+cards+"</div>"

    def section(icon, title, sub):
        return ("<div style=\"padding:28px 36px 10px;\"><div style=\"font-size:1rem;font-weight:800\">"
                +icon+" "+title+"</div><div style=\"font-size:0.7rem;color:var(--muted)\">"
                +sub+"</div></div>")

    # Revenue
    rev_cards = ""
    for name in locs:
        c = COLORS[name]; sc = scorecard[name]
        exp = loc_total(name,"expected"); lw = last_week_rev[name]
        dc_t = today_counts[name]["daycare"]; bo_t = today_counts[name]["boarding"]
        dogs = dc_t + bo_t
        today_rev = sum(sum(revenue[name].get(adate(dk),{}).values()) for dk in DAY_KEYS[:today.weekday()+1])
        # 4-week avg: average revenue on this same day of week over last 4 weeks
        same_dow_revs = []
        for wk in range(1,5):
            past_d = today_d - __import__("datetime").timedelta(weeks=wk)
            past_key = "{:02d}/{:02d}/{}".format(past_d.month,past_d.day,past_d.year)
            past_rev = sum(scorecard[name].get("daily_rev",{}).get(past_key,{}).values()) if isinstance(scorecard[name].get("daily_rev",{}).get(past_key),dict) else scorecard[name].get("daily_rev",{}).get(past_key,0)
            if past_rev == 0: past_rev = sum(revenue[name].get(past_key,{}).values())
            if past_rev > 0: same_dow_revs.append(past_rev)
        avg_4wk = sum(same_dow_revs)/len(same_dow_revs) if same_dow_revs else 0
        today_only = sum(revenue[name].get("{:02d}/{:02d}/{}".format(today_d.month,today_d.day,today_d.year),{}).values())
        avg_ticket = (today_only/dogs) if dogs>0 else 0

        vs4 = ((today_only-avg_4wk)/avg_4wk*100) if avg_4wk>0 else 0
        retail_wtd = sum(retail[name]["daily"].get(adate(dk),0) for dk in DAY_KEYS)
        mem_wtd = loc_mem(name)
        unp = loc_total(name,"unpaid"); unp_col = "#dc2626" if unp>0 else "#16a34a"
        lw_full = last_week_rev[name]
        spark = ""
        for j,dk in enumerate(DAY_KEYS):
            drev = sum(revenue[name].get(adate(dk),{}).values())
            h = max(3,min(32,int(drev/200))) if drev>0 else 2
            clr = c if j==today.weekday() else ("#16a34a" if drev>0 else "#e2e2d8")
            spark += "<div style=\"height:{}px;width:8px;background:{};border-radius:3px 3px 0 0;display:inline-block;margin-right:2px\"></div>".format(h,clr)
        vs4col = "#16a34a" if vs4>=0 else "#dc2626"
        body = (
            "<div style=\"font-size:0.65rem;font-weight:700;color:var(--muted);text-transform:uppercase;margin-bottom:2px\">REVENUE TODAY</div>"
            +"<div style=\"display:flex;align-items:baseline;gap:12px;margin-bottom:8px\">"
            +"<span style=\"font-size:1.5rem;font-weight:800;font-family:'DM Mono',monospace;color:"+c+"\">"+fmt(today_only)+"</span>"
            +"<span style=\"font-size:1.5rem;font-weight:800;font-family:'DM Mono',monospace;color:"+c+"\"> / "+fmt(exp)+"</span>"
            +"</div>"
            +row("WTD Revenue", fmt(exp))
            +row("vs Last Week WTD", pct_badge(exp,lw))
            +row("vs 4-Wk Same Day", "<span style=\"color:"+vs4col+"\">"+("{:+.1f}%".format(vs4))+"</span>")
            +row("Last Week Total", fmt(lw_full))
            +"<div style=\"height:6px\"></div>"
            +row("Dogs Today", str(dogs))
            +row("Avg Ticket/Dog", fmt(avg_ticket) if avg_ticket>0 else "—")
            +row("Retail WTD", fmt(retail_wtd))
            +row("Membership WTD", fmt(mem_wtd))
            +row("Unpaid", "<span style=\"color:"+unp_col+"\">"+fmt(unp)+"</span>")
            +"<div style=\"display:flex;align-items:flex-end;height:36px;margin-top:8px\">"+spark+"</div>"
        )
        rev_cards += card(c, name, body)

    # Capacity
    cap_cards = ""
    for name in locs:
        c = COLORS[name]; cap = CAPACITY[name]
        dc_t=today_counts[name]["daycare"]; bo_t=today_counts[name]["boarding"]
        dc_tm=tomorrow_counts[name]["daycare"]; bo_tm=tomorrow_counts[name]["boarding"]
        def cv(v,mx):
            p=(v/mx*100) if mx>0 else 0
            col=cap_color(p)
            return "<span style=\"color:"+col+";font-weight:700\">"+str(v)+"/"+str(mx)+" ({:.0f}%)</span>".format(p)
        snp_t = today_counts[name].get("snp", 0)
        snp_tm = 0  # SNP tomorrow not available from API
        snp_cap = cap.get("snp", 0)
        body=(
            "<div style=\"font-size:1.5rem;font-weight:800;font-family:\'DM Mono\',monospace;color:"+c+";margin-bottom:8px\">{:.0f}%</div>".format(cap_pct(dc_t,cap["daycare"]))
            +"<div style=\"font-size:0.75rem;font-weight:900;color:#111;text-transform:uppercase;padding:4px 0\">TODAY</div>"
            +row("Daycare", cv(dc_t,cap["daycare"]))+row("Boarding", cv(bo_t,cap["boarding"]))
            +row("Stay & Play", cv(snp_t,snp_cap))
            +"<div style=\"font-size:0.75rem;font-weight:900;color:#111;text-transform:uppercase;padding:4px 0\">TOMORROW</div>"
            +row("Daycare", cv(dc_tm,cap["daycare"]))+row("Boarding", cv(bo_tm,cap["boarding"]))+row("Stay & Play", cv(snp_tm,snp_cap))
        )
        cap_cards += card(c, name, body)

    # Labor
    lab_cards = ""
    for name in locs:
        c=COLORS[name]; lp=labor_pct(name); lc=labor_color(lp)
        body=(
            "<div style=\"font-size:1.5rem;font-weight:800;font-family:\'DM Mono\',monospace;color:"+lc+";margin-bottom:8px\">"+(("{:.1f}%".format(lp)) if lp>0 else "—")+"</div>"
            +row("WTD Labor $", fmt(labor_wtd(name)) if labor_wtd(name)>0 else "—")
            +row("Target", "{:.0f}%".format(LABOR_TARGET_PCT*100))
            +row("Tomorrow", "<span style=\"color:var(--muted)\">Homebase soon</span>")
        )
        lab_cards += card(c, name, body)

    # Bonus
    bon_cards = ""
    for name in locs:
        c=COLORS[name]; q=q1_data[name]
        bp=q.get("progress",0); bc="#16a34a" if bp>=90 else "#d97706" if bp>=70 else "#dc2626"
        gap=q.get("gap",0); daily=(gap/days_left_q1) if days_left_q1>0 else 0
        target_amt = q.get("target",0)
        ty_qtd = q.get("ty_qtd",0)
        bar="<div style=\"height:8px;background:#e2e2d8;border-radius:4px;overflow:hidden;margin:8px 0\"><div style=\"height:8px;background:"+bc+";width:{:.1f}%25;\"></div></div>".format(min(bp,100))
        body=(
            "<div style=\"font-size:0.65rem;font-weight:700;color:var(--muted);text-transform:uppercase;margin-bottom:2px\">Q1 PROGRESS</div>"
            +"<div style=\"font-size:1.5rem;font-weight:800;font-family:\'DM Mono\',monospace;color:"+bc+";margin-bottom:4px\">{:.1f}%</div>".format(bp)
            +bar
            +row("Q1 Goal", fmt(target_amt) if target_amt>0 else "—")
            +row("Revenue to Date", fmt(ty_qtd) if ty_qtd>0 else fmt(loc_total(name,"expected")))
            +row("Gap to Goal", "<span style=\"color:"+bc+"\">"+fmt(gap)+"</span>")
            +row("Daily Needed", "<span style=\"color:"+bc+"\">"+fmt(daily)+"</span>")
            +row("Days Left", str(days_left_q1))
        )
        bon_cards += card(c, name, body)

    # Growth
    gro_cards = ""
    for name in locs:
        c=COLORS[name]; cl=clients[name]
        new_pct=(cl["new"]/cl["total"]*100) if cl["total"]>0 else 0
        mw=loc_mem(name); ex=loc_total(name,"expected")
        body=(
            "<div style=\"font-size:1.5rem;font-weight:800;font-family:\'DM Mono\',monospace;color:#16a34a;margin-bottom:8px\">"+str(cl["new"])+" new</div>"
            +row("Total Clients WTD",str(cl["total"]))+row("Returning",str(cl["existing"]))
            +row("New Client Rate","{:.1f}%".format(new_pct))
            +"<div style=\"height:6px\"></div>"
            +row("Membership WTD",fmt(mw))+row("Membership % Rev","{:.1f}%".format((mw/ex*100) if ex>0 else 0))
        )
        gro_cards += card(c, name, body)

    # Summary totals bar
    total_rev = sum(loc_total(n,"expected") for n,_,_ in LOCS)
    total_today = sum(sum(revenue[n].get("{:02d}/{:02d}/{}".format(today_d.month,today_d.day,today_d.year),{}).values()) for n,_,_ in LOCS)
    total_dogs = sum(counts[n].get("DAYCARE",{}).get("TOTAL",0)+counts[n].get("BOARDING",{}).get("TOTAL",0) for n,_,_ in LOCS)
    total_unp = sum(loc_total(n,"unpaid") for n,_,_ in LOCS)
    total_retail = sum(retail[n]["total"] for n,_,_ in LOCS)
    total_mem = sum(loc_mem(n) for n,_,_ in LOCS)
    total_lw = sum(last_week_rev[n] for n,_,_ in LOCS)
    total_wow = ((total_rev-total_lw)/total_lw*100) if total_lw>0 else 0
    wow_col = "#16a34a" if total_wow>=0 else "#dc2626"
    def sbox(label, val, color="var(--text)"):
        return ("<div style=\"flex:1;text-align:center;padding:12px 8px;border-right:1px solid var(--border);\">"
                +"<div style=\"font-size:1.2rem;font-weight:800;font-family:'DM Mono',monospace;color:"+color+"\">"+val+"</div>"
                +"<div style=\"font-size:0.65rem;text-transform:uppercase;letter-spacing:0.8px;color:var(--muted);font-weight:600;margin-top:2px\">"+label+"</div>"
                +"</div>")
    summary_bar = ("<div style=\"display:flex;align-items:center;justify-content:space-between;background:white;border-bottom:2px solid var(--border);padding:0;width:100%;\">"
        +sbox("Today Sales", fmt(total_today), "#1a1a1a")
        +sbox("WTD Revenue", fmt(total_rev), "#1a1a1a")
        +sbox("vs Last Week", ("{:+.1f}%".format(total_wow)), wow_col)
        +sbox("Total Dogs", str(total_dogs))
        +sbox("Unpaid", fmt(total_unp), "#dc2626" if total_unp>0 else "#16a34a")
        +sbox("Retail WTD", fmt(total_retail))
        +sbox("Membership WTD", fmt(total_mem))
        +"</div>")

    # Membership conversion cards
    mem_cards = ""
    for name in locs:
        c = COLORS[name]
        mc = membership_conv.get(name, {})
        rate = mc.get("rate", 0)
        members = mc.get("members", 0)
        total = mc.get("total", 0)
        rate_col = "#16a34a" if rate >= 50 else "#d97706" if rate >= 25 else "#dc2626"
        body = (
            "<div style=\"font-size:1.5rem;font-weight:800;font-family:'DM Mono',monospace;color:"+rate_col+";margin-bottom:8px\">{:.1f}%</div>".format(rate)
            +row("Members WTD", str(members))
            +row("Total Clients WTD", str(total))
            +row("Non-Members", str(total - members))
        )
        mem_cards += card(c, name, body)

    # Service mix cards
    mix_cards = ""
    for name in locs:
        c = COLORS[name]
        sm = service_mix.get(name, {})
        total = sm.get("total", 0)
        cats = sm.get("cats", {})
        cat_rows = ""
        for cat, rev in list(cats.items())[:6]:
            pct = round(rev/total*100,1) if total else 0
            cat_rows += row(cat, fmt(rev)+" ({:.1f}%)".format(pct))
        body = (
            "<div style=\"font-size:1.5rem;font-weight:800;font-family:'DM Mono',monospace;color:"+c+";margin-bottom:4px\">"+fmt(total)+"</div>"
            +"<div style=\"font-size:0.65rem;color:var(--muted);font-style:italic;margin-bottom:8px\">Based on checkout date</div>"
            +cat_rows
        )
        mix_cards += card(c, name, body)

    # Review score cards
    rev_score_cards = ""
    for name in locs:
        c = COLORS[name]
        rd = review_data.get(name, {})
        avg = rd.get("avg", 0)
        count = rd.get("count", 0)
        by_staff = rd.get("by_staff", {})
        avg_col = "#16a34a" if avg >= 4.5 else "#d97706" if avg >= 4.0 else "#dc2626"
        stars = "★" * int(round(avg)) + "☆" * (5 - int(round(avg))) if avg else "—"
        staff_rows = ""
        for sname, sc in list(by_staff.items())[:4]:
            short = sname.split()[0] if sname != "Unassigned" else "Unassigned"
            s_col = "#16a34a" if sc >= 4.5 else "#d97706" if sc >= 4.0 else "#dc2626"
            staff_rows += row(short, "<span style=\"color:"+s_col+"\">"+str(sc)+"</span>")
        body = (
            "<div style=\"font-size:1.5rem;font-weight:800;font-family:'DM Mono',monospace;color:"+avg_col+";margin-bottom:4px\">"+(str(avg) if avg else "—")+"</div>"
            +"<div style=\"font-size:0.8rem;color:"+avg_col+";margin-bottom:8px\">"+stars+"</div>"
            +row("Total Reviews", str(count))
            +staff_rows
        )
        rev_score_cards += card(c, name, body)

    # Client retention cards
    ret_cards = ""
    for name in locs:
        c = COLORS[name]
        rd = retention_data.get(name, {})
        total = rd.get("total", 0)
        active = rd.get("active", 0)
        l30 = rd.get("lapsed_30", 0)
        l60 = rd.get("lapsed_60", 0)
        l90 = rd.get("lapsed_90", 0)
        rate = round(active/total*100,1) if total else 0
        rate_col = "#16a34a" if rate >= 70 else "#d97706" if rate >= 50 else "#dc2626"
        body = (
            "<div style=\"font-size:1.5rem;font-weight:800;font-family:'DM Mono',monospace;color:"+rate_col+";margin-bottom:8px\">{:.1f}%</div>".format(rate)
            +row("Active (0-30d)", "<span style=\"color:#16a34a\">"+str(active)+"</span>")
            +row("Lapsed 30-60d", "<span style=\"color:#d97706\">"+str(l30)+"</span>")
            +row("Lapsed 60-90d", "<span style=\"color:#dc2626\">"+str(l60)+"</span>")
            +row("Total Clients", str(total))
        )
        ret_cards += card(c, name, body)

    # Staff performance cards
    stf_cards = ""
    for name in locs:
        c = COLORS[name]
        sd = staff_data.get(name, {})
        rows_html = ""
        for sname, stats in list(sd.items())[:5]:
            short = sname.split()[0] if sname != "Unassigned" else "Unassigned"
            rows_html += row(short, str(stats["appts"])+" appts · "+fmt(stats["revenue"]))
        if not rows_html:
            rows_html = row("No data","—")
        top_rev = list(sd.values())[0]["revenue"] if sd else 0
        body = (
            "<div style=\"font-size:1.5rem;font-weight:800;font-family:'DM Mono',monospace;color:"+c+";margin-bottom:8px\">"+str(len(sd))+" staff</div>"
            +rows_html
        )
        stf_cards += card(c, name, body)

    can_cards = ""
    for name in locs:
        c = COLORS[name]; cd = cancel_data.get(name,{})
        gr_rate = cd.get("gr_rate",0); dc_rate = cd.get("dc_rate",0)
        gr_col = "#dc2626" if gr_rate>15 else "#d97706" if gr_rate>10 else "#16a34a"
        dc_col = "#dc2626" if dc_rate>25 else "#d97706" if dc_rate>15 else "#16a34a"
        body = (
            "<div style=\"font-size:1.5rem;font-weight:800;font-family:'DM Mono',monospace;color:"+gr_col+";margin-bottom:8px\">{:.1f}%</div>".format(gr_rate)
            +row("Grooming Cancel","<span style=\"color:"+gr_col+"\">"+str(cd.get("gr_cancel",0))+"/"+str(cd.get("gr_total",0))+"</span>")
            +row("Grooming No-Show",str(cd.get("gr_noshow",0)))
            +row("Daycare Cancel","<span style=\"color:"+dc_col+"\">"+str(cd.get("dc_cancel",0))+"/"+str(cd.get("dc_total",0))+"</span>")
        )
        can_cards += card(c, name, body)

    return ("<div style=\"background:var(--bg);min-height:100vh;padding-bottom:48px;\">" + summary_bar
        +section("💰","TODAY\'S REVENUE",today.strftime("%A, %B %d")+" · WTD vs Last Week")
        +grid(rev_cards)
        +section("🐾","CAPACITY","Today vs Tomorrow")
        +grid(cap_cards)
        +section("👥","LABOR","WTD % vs target")
        +grid(lab_cards)
        +section("🎯","Q1 BONUS TRACKER",str(days_left_q1)+" days remaining")
        +grid(bon_cards)
        +section("📈","GROWTH PULSE","Week to date")
        +grid(gro_cards)
        +section("💳","MEMBERSHIP CONVERSION","WTD % of clients using membership")
        +grid(mem_cards)
        +section("📊","SERVICE MIX","WTD revenue by category")
        +grid(mix_cards)
        +section("⭐","REVIEW SCORES","WTD grooming reviews by location & staff")
        +grid(rev_score_cards)
        +section("🔄","CLIENT RETENTION","Rolling 90-day daycare clients")
        +grid(ret_cards)
        +section("✂️","STAFF PERFORMANCE","WTD grooming appointments & revenue")
        +grid(stf_cards)
        +section("❌","CANCELLATIONS","Rolling WTD grooming & daycare")
        +grid(can_cards)
        +"</div>")

def build_exec_tab(loc_filter=None):
    """Build Executive View tab. loc_filter=None means all locations."""
    locs = [n for n,_,_ in LOCS] if loc_filter is None else [loc_filter]
    # Filter exec_cards, scorecard_html, alerts for this location set
    if loc_filter is None:
        ec = exec_cards
        sc = scorecard_html
        al = alerts_html
        dc = tot_dc; bo = tot_bo; gr = tot_gr
        ge = grand_exp; gu = grand_unp; gr2 = grand_retail
        uc = unp_color
        gl_wtd = grand_labor_wtd; gl_pct = grand_labor_pct
    else:
        ec = build_exec_card_single(loc_filter)
        sc = build_scorecard_single(loc_filter)
        al = build_alert_single(loc_filter)
        dc = counts[loc_filter].get("DAYCARE",{}).get("TOTAL",0)
        bo = counts[loc_filter].get("BOARDING",{}).get("TOTAL",0)
        gr = counts[loc_filter].get("GROOMING",{}).get("TOTAL",0)
        ge = loc_total(loc_filter,"expected")
        gu = loc_total(loc_filter,"unpaid")
        gr2 = retail[loc_filter]["total"]
        uc = "red" if gu>0 else "green"
        gl_wtd = labor_wtd(loc_filter)
        gl_pct = labor_pct(loc_filter)
        
    lc = labor_color(gl_pct)
    return (
        al +
        "<div class=\"exec-summary\">"
        "<div class=\"exec-stat\"><div class=\"v green\">"+fmt(ge)+"</div><div class=\"l\">Week Expected</div></div>"
        "<div class=\"exec-stat\"><div class=\"v "+uc+"\">"+fmt(gu)+"</div><div class=\"l\">Unpaid</div></div>"
        "<div class=\"exec-stat\"><div class=\"v\">"+""+"{:,}".format(dc)+"</div><div class=\"l\">Daycare Dogs</div></div>"
        "<div class=\"exec-stat\"><div class=\"v\">"+""+"{:,}".format(bo)+"</div><div class=\"l\">Boarding Dogs</div></div>"
        "<div class=\"exec-stat\"><div class=\"v\">"+""+"{:,}".format(gr)+"</div><div class=\"l\">Grooming Appts</div></div>"
        "<div class=\"exec-stat\"><div class=\"v\">"+fmt(gr2)+"</div><div class=\"l\">Retail WTD</div></div>"
        "</div>"
        "<div class=\"exec-grid\">"+ec+"</div>"
        "<div class=\"section\" style=\"background:var(--bg);\"><div class=\"section-title\">Today vs Benchmarks &mdash; "+day_name+"</div><div class=\"sc-grid\">"+sc+"</div></div>"
        + build_capacity_section(loc_filter)
    )

def build_exec_card_single(name):
    c=COLORS[name]; q=q1_data[name]; y=ytd_data[name]
    exp=loc_total(name,"expected"); unp=loc_total(name,"unpaid")
    lw=last_week_rev[name]; wow_pct=((exp-lw)/lw*100) if lw>0 else 0
    q1_prog=q["progress"]
    bc="#16a34a" if q1_prog>=90 else "#d97706" if q1_prog>=70 else "#dc2626"
    return (
        "<div class=\"exec-card\" style=\"--accent:"+c+";\">"
        "<div class=\"exec-card-name\">"+name+"</div>"
        "<div class=\"exec-card-rev\">"+fmt(exp)+"</div>"
        "<div class=\"exec-card-sub\">Week to Date</div>"
        "<div class=\"exec-kpi\"><span class=\"exec-kpi-l\"><span class=\"tl "+("green" if wow_pct>=0 else "red")+"\"></span>vs Last Week</span>"
        "<span class=\"exec-kpi-v "+("green" if wow_pct>=0 else "red")+"\">"+("+" if wow_pct>=0 else "")+"{:.1f}%".format(wow_pct)+"</span></div>"
        "<div class=\"exec-kpi\"><span class=\"exec-kpi-l\"><span class=\"tl "+("green" if y["pct"]>=0 else "red")+"\"></span>YTD vs LY</span>"
        "<span class=\"exec-kpi-v "+("green" if y["pct"]>=0 else "red")+"\">"+("+" if y["pct"]>=0 else "")+"{:.1f}%".format(y["pct"])+"</span></div>"
        "<div class=\"exec-kpi\"><span class=\"exec-kpi-l\"><span class=\"tl "+("green" if loc_total(name,"unpaid")==0 else "red")+"\"></span>Unpaid</span>"
        "<span class=\"exec-kpi-v "+("red" if unp>0 else "green")+"\">"+fmt(unp)+"</span></div>"
        "<div class=\"exec-kpi\"><span class=\"exec-kpi-l\">Labor %</span>"
        "<span class=\"exec-kpi-v\" style=\"color:"+labor_color(labor_pct(name))+"\">"+"{:.1f}%".format(labor_pct(name))+"</span></div>"
        "<div class=\"exec-kpi\"><span class=\"exec-kpi-l\">Retail WTD</span><span class=\"exec-kpi-v\">"+fmt(retail[name]["total"])+"</span></div>"
        "<div style=\"margin-top:8px;font-size:0.68rem;color:var(--muted2);font-weight:500;\">Q1 BONUS</div>"
        "<div class=\"exec-bonus-bar\"><div class=\"exec-bonus-fill\" style=\"width:"+"{:.1f}".format(min(q1_prog,100))+"%;background:"+bc+"\"></div></div>"
        "<div style=\"font-size:0.7rem;font-family:\'DM Mono\',monospace;color:"+bc+";margin-top:3px;\">"+""+"{:.1f}".format(q1_prog)+"% &nbsp;&#183;&nbsp; Gap: "+fmt(q["gap"])+"</div>"
        "</div>"
    )

def build_alert_single(name):
    unp = loc_total(name,"unpaid")
    return ("<div class=\"alert-banner warn\">&#9888; Unpaid balance of "+fmt(unp)+" requires follow-up</div>"
            if unp>0 else
            "<div class=\"alert-banner good\">&#10003; All balances collected this week</div>")

def build_scorecard_single(name):
    sc = scorecard[name]
    c  = COLORS[name]
    td = sc["today"]; lw2 = sc["last_week"]; lm = sc["last_month"]; ly = sc["last_year"]; av = sc["avg"]
    if td["dc"]==0 and td["bo"]==0 and td["gr"]==0:
        return (f"<div class=\"sc-card\" style=\"--accent:{c};opacity:0.4\">"
                f"<div class=\"sc-name\">{name}</div>"
                f"<div style=\"font-size:0.75rem;color:var(--muted);padding:12px 0\">No data today</div>"
                f"</div>")
    def delta_b(tv, bv):
        if bv==0: return "<span style=\"color:var(--muted);font-size:0.7rem\">—</span>"
        d=tv-bv; p=(d/bv*100)
        cls="color:var(--green)" if d>=0 else "color:var(--red)"
        return f"<span style=\"font-size:0.7rem;font-family:\'DM Mono\',monospace;{cls}\">"+("+\u200b" if d>=0 else "")+f"{p:.0f}%</span>"
    def fmt_c(v): return str(int(round(v))) if v else "—"
    def mrow(label,tag,key,is_money=False):
        ff=fmt if is_money else fmt_c
        af=fmt(av[key]) if is_money else f"{av[key]:.1f}"
        return (f"<div class=\"sc-row\"><div class=\"sc-metric\"><span class=\"tag {tag}\">{label}</span></div>"
                f"<div class=\"sc-val\">{ff(td[key])}</div>"
                f"<div class=\"sc-bench\">{ff(lw2[key])} {delta_b(td[key],lw2[key])}</div>"
                f"<div class=\"sc-bench\">{ff(lm[key])} {delta_b(td[key],lm[key])}</div>"
                f"<div class=\"sc-bench\">{ff(ly[key])} {delta_b(td[key],ly[key])}</div>"
                f"<div class=\"sc-bench\">{af} {delta_b(td[key],av[key])}</div></div>")
    return (f"<div class=\"sc-card\" style=\"--accent:{c}\">"
            f"<div class=\"sc-name\">{name}</div>"
            f"<div class=\"sc-header-row\"><div class=\"sc-metric\"></div>"
            f"<div class=\"sc-val-hdr\">Today</div>"
            f"<div class=\"sc-bench-hdr\">Last {day_name}</div>"
            f"<div class=\"sc-bench-hdr\">Last Month</div>"
            f"<div class=\"sc-bench-hdr\">Last Year</div>"
            f"<div class=\"sc-bench-hdr\">5-{day_name} Avg</div></div>"
            + mrow("Daycare","dc","dc")
            + mrow("Boarding","bo","bo")
            + mrow("Grooming","gr","gr")
            + mrow("Retail","ms","retail",is_money=True)
            + "</div>")

def build_full_tab(loc_filter=None):
    """Build Full Detail tab. loc_filter=None = all locations."""
    if loc_filter is None:
        rr=rev_rows; cr=count_rows; ur=unpaid_rows; br2=bonus_rows
        yr=ytd_rows; wr=wow_rows; rdr=retail_day_rows; tir=top_item_rows
        clr=client_rows; bdr=boarding_rows; ch=cards_html
        ge=grand_exp; gu=grand_unp; dc=tot_dc; bo=tot_bo; gr=tot_gr
        uc=unp_color
    else:
        # Filter all row builders to single location
        rr  = build_rev_rows_single(loc_filter)
        cr  = build_count_rows_single(loc_filter)
        ur  = build_unpaid_rows_single(loc_filter)
        br2 = build_bonus_rows_single(loc_filter)
        yr  = build_ytd_rows_single(loc_filter)
        wr  = build_wow_rows_single(loc_filter)
        rdr = build_retail_day_rows_single(loc_filter)
        tir = build_top_item_rows_single(loc_filter)
        clr = build_client_rows_single(loc_filter)
        bdr = build_boarding_rows_single(loc_filter)
        ch  = build_card(loc_filter, *[(c,b) for n,c,b in LOCS if n==loc_filter][0])
        ge  = loc_total(loc_filter,"expected")
        gu  = loc_total(loc_filter,"unpaid")
        dc  = counts[loc_filter].get("DAYCARE",{}).get("TOTAL",0)
        bo  = counts[loc_filter].get("BOARDING",{}).get("TOTAL",0)
        gr  = counts[loc_filter].get("GROOMING",{}).get("TOTAL",0)
        uc  = "red" if gu>0 else "green"

    return (
        "<div class=\"summary\">"
        "<div class=\"sstat\"><div class=\"v green\">"+fmt(ge)+"</div><div class=\"l\">Week Expected</div></div>"
        "<div class=\"sstat\"><div class=\"v "+uc+"\">"+fmt(gu)+"</div><div class=\"l\">Total Unpaid</div></div>"
        "<div class=\"sstat\"><div class=\"v\">"+"{:,}".format(dc)+"</div><div class=\"l\">Daycare Dogs</div></div>"
        "<div class=\"sstat\"><div class=\"v\">"+"{:,}".format(bo)+"</div><div class=\"l\">Boarding Dogs</div></div>"
        "<div class=\"sstat\"><div class=\"v\">"+"{:,}".format(gr)+"</div><div class=\"l\">Grooming Appts</div></div>"
        "</div>"
        "<div class=\"cards\">"+ch+"</div>"
        + build_labor_section() +
        "<div class=\"section\"><div class=\"section-title\">Daily Revenue by Service Type</div>"
        "<table><thead><tr><th>Location / Category</th>"+day_headers+"<th class=\"r\">WTD Total</th></tr></thead>"
        "<tbody>"+rr+"</tbody></table>"
        "<div class=\"note\">* Memberships = weekly billing (hits every Monday)</div></div>"
        "<div class=\"section\"><div class=\"section-title\">Daily Dog &amp; Appointment Counts</div>"
        "<table><thead><tr><th>Location</th><th></th>"+day_headers+"<th class=\"r\">WTD Total</th></tr></thead>"
        "<tbody>"+cr+"</tbody></table></div>"
        "<div class=\"section\"><div class=\"section-title\">Unpaid Balances</div>"
        "<table><thead><tr><th>Location</th><th class=\"r\">Expected</th><th class=\"r\">Collected</th><th class=\"r\">Unpaid</th><th class=\"r\">Tips WTD</th></tr></thead>"
        "<tbody>"+ur+"</tbody></table></div>"
        "<div class=\"section\"><div class=\"section-title\">Q1 2026 GM Bonus Tracker</div>"
        "<table><thead><tr><th>Location</th><th class=\"r\">Q1 2025 Full</th><th class=\"r\">Q1 Target</th><th class=\"r\">LY Same Days</th><th class=\"r\">Q1 2026 QTD</th><th class=\"r\">vs LY Pace</th><th class=\"r\">Gap to Bonus</th><th>Progress</th></tr></thead>"
        "<tbody>"+br2+"</tbody></table>"
        "<div class=\"note\">Target = Q1 2025 full x bonus % &#183; "+str(days_left_q1)+" days remaining in Q1</div></div>"
        "<div class=\"section\"><div class=\"section-title\">YTD Sales vs Last Year</div>"
        "<table><thead><tr><th>Location</th><th class=\"r\">2026 YTD</th><th class=\"r\">2025 Same Days</th><th class=\"r\">Difference</th><th class=\"r\">2025 Full Year</th><th class=\"r\">2026 Projection</th><th>vs Last Year</th></tr></thead>"
        "<tbody>"+yr+"</tbody></table>"
        "<div class=\"note\">* Projection = seasonally weighted by 2025 monthly distribution</div></div>"
        "<div class=\"section\"><div class=\"section-title\">Week over Week Revenue</div>"
        "<table><thead><tr><th>Location</th><th class=\"r\">This Week (WTD)</th><th class=\"r\">Last Week</th><th class=\"r\">Difference</th><th class=\"r\">Change</th></tr></thead>"
        "<tbody>"+wr+"</tbody></table></div>"
        "<div class=\"section\"><div class=\"section-title\">Retail Sales</div>"
        "<table><thead><tr><th>Location</th>"+day_headers+"<th class=\"r\">WTD Total</th><th class=\"r\">% of Revenue</th></tr></thead>"
        "<tbody>"+rdr+"</tbody></table>"
        "<div style=\"margin-top:24px\"><div class=\"section-title\" style=\"margin-bottom:12px\">Top Selling Retail Items</div>"
        "<table><thead><tr><th>Item</th><th class=\"c\">Qty Sold</th><th class=\"r\">Revenue</th></tr></thead>"
        "<tbody>"+tir+"</tbody></table></div></div>"
        "<div class=\"section\"><div class=\"section-title\">New vs Returning Clients</div>"
        "<table><thead><tr><th>Location</th><th class=\"r\">Total Clients</th><th class=\"r\">New</th><th class=\"r\">Existing</th><th class=\"r\">Recurring</th><th class=\"r\">% New</th></tr></thead>"
        "<tbody>"+clr+"</tbody></table></div>"
        "<div class=\"section\"><div class=\"section-title\">Boarding Occupancy</div>"
        "<table><thead><tr><th>Location</th><th class=\"r\">Dogs Boarded</th><th class=\"r\">Total Nights</th><th class=\"r\">Avg Nights / Dog</th></tr></thead>"
        "<tbody>"+bdr+"</tbody></table></div>"
    )

def build_gm_tab(loc_filter=None):
    if loc_filter is None:
        gc = gm_cards
    else:
        gc = build_gm_card_single(loc_filter)
    return (
        "<div class=\"section\" style=\"padding:18px 36px;\"><div class=\"section-title\">GM Performance View &mdash; Week of "+WEEK_LABEL+"</div></div>"
        "<div class=\"gm-grid\">"+gc+"</div>"
    )

def build_gm_card_single(name):
    c=COLORS[name]; q=q1_data[name]; y=ytd_data[name]
    exp=loc_total(name,"expected"); unp=loc_total(name,"unpaid")
    lw=last_week_rev[name]; bd=boarding_nights[name]; cl=clients[name]
    wow_pct=((exp-lw)/lw*100) if lw>0 else 0
    bc="#16a34a" if q["progress"]>=90 else "#d97706" if q["progress"]>=70 else "#dc2626"
    if q["progress"]>=90:   badge="<span class=\"status-badge ahead\">&#9679; Ahead</span>"
    elif q["progress"]>=70: badge="<span class=\"status-badge on-pace\">&#9679; On Pace</span>"
    else:                   badge="<span class=\"status-badge behind\">&#9679; Behind</span>"
    top3=sorted(retail[name]["items"].items(),key=lambda x:-x[1]["amt"])[:3]
    ri=("".join("<div class=\"gm-retail-item\">"+item[:24]+("..." if len(item)>24 else "")+"<span>"+fmt(v["amt"])+"</span></div>" for item,v in top3)
        or "<div class=\"gm-retail-item\" style=\"color:var(--muted)\">No retail this week</div>")
    lp = labor_pct(name); lc2 = labor_color(lp)
    card = "<div class=\"gm-card\" style=\"--accent:"+c+";\">"
    card += "<div class=\"gm-card-header\"><div class=\"gm-card-name\">"+name+"</div><div style=\"margin-top:4px\">"+badge+"</div></div>"
    card += "<div class=\"gm-card-body\">"
    card += "<div class=\"gm-stat\"><span class=\"gm-stat-l\">Revenue WTD</span><span class=\"gm-stat-v\">"+fmt(exp)+"</span></div>"
    card += "<div class=\"gm-stat\"><span class=\"gm-stat-l\">vs Last Week</span><span class=\"gm-stat-v "+("green" if wow_pct>=0 else "red")+"\">"+("+\u200b" if wow_pct>=0 else "")+"{:.1f}%".format(wow_pct)+"</span></div>"
    card += "<div class=\"gm-stat\"><span class=\"gm-stat-l\">YTD vs LY</span><span class=\"gm-stat-v "+("green" if y["pct"]>=0 else "red")+"\">"+("+" if y["pct"]>=0 else "")+"{:.1f}%".format(y["pct"])+"</span></div>"
    card += "<div class=\"gm-stat\"><span class=\"gm-stat-l\">2026 YTD</span><span class=\"gm-stat-v\">"+fmt(y["ty_ytd"])+"</span></div>"
    card += "<div class=\"gm-stat\"><span class=\"gm-stat-l\">Unpaid</span><span class=\"gm-stat-v "+("red" if unp>0 else "green")+"\">"+ fmt(unp)+"</span></div>"
    card += "<div class=\"gm-stat\"><span class=\"gm-stat-l\">Labor %</span><span class=\"gm-stat-v\" style=\"color:"+lc2+"\">"+"{:.1f}%".format(lp)+"</span></div>"
    card += "<div class=\"gm-stat\"><span class=\"gm-stat-l\">Clients</span><span class=\"gm-stat-v\">"+"{:,}".format(cl["total"])+" ("+str(cl["new"])+" new)</span></div>"
    card += "<div class=\"gm-stat\"><span class=\"gm-stat-l\">Boarding</span><span class=\"gm-stat-v\">"+str(bd["dogs"])+" dogs / "+str(bd["nights"])+" nights</span></div>"
    card += "<div class=\"gm-stat\"><span class=\"gm-stat-l\">Retail WTD</span><span class=\"gm-stat-v\">"+fmt(retail[name]["total"])+"</span></div>"
    card += "</div>"
    card += "<div class=\"gm-bonus-section\">"
    card += "<div class=\"gm-bonus-title\">Q1 Bonus ("+"{:.0f}".format(q["pct"]*100)+"% target)</div>"
    card += "<div class=\"gm-bonus-bar\"><div class=\"gm-bonus-fill\" style=\"width:"+"{:.1f}".format(min(q["progress"],100))+"%;background:"+bc+"\"></div></div>"
    card += "<div class=\"gm-bonus-pct\" style=\"color:"+bc+"\">"+"{:.1f}".format(q["progress"])+"% reached</div>"
    card += "<div style=\"font-size:0.75rem;margin-top:6px;font-family:\'DM Mono\',monospace;\">"+fmt(q["ty_qtd"])+" / "+fmt(q["target"])+"</div>"
    card += "<div style=\"font-size:0.72rem;color:var(--muted2);margin-top:3px;\">Gap: "+fmt(q["gap"])+" &#183; "+str(q["days_left"])+"d left</div>"
    card += "<div style=\"margin-top:12px;font-size:0.68rem;text-transform:uppercase;letter-spacing:1px;color:var(--muted);font-weight:600;margin-bottom:5px;\">Top Retail</div>"
    card += ri + "</div></div>"
    return card

# Single-location row builders
def build_rev_rows_single(name):
    c=COLORS[name]; wtd=loc_total(name,"expected")
    day_cells="".join("<td class=\"r mono\">"+( fmt(sum(revenue[name].get(adate(dk),{}).values())) if sum(revenue[name].get(adate(dk),{}).values())>0 else "—")+"</td>" for dk in DAY_KEYS)
    rows="<tr><td class=\"bold\"><span class=\"dot\" style=\"background:"+c+"\"></span>"+name+"</td>"+day_cells+"<td class=\"r mono bold\">"+fmt(wtd)+"</td></tr>"
    for care in CARE_ORDER:
        tag=CARE_TAG[care]; lbl=CARE_LABELS[care]
        cells="".join("<td class=\"r mono\">"+(fmt(revenue[name].get(adate(dk),{}).get(care,0)) if revenue[name].get(adate(dk),{}).get(care,0)>0 else "—")+"</td>" for dk in DAY_KEYS)
        sub=sum(revenue[name].get(adate(dk),{}).get(care,0) for dk in DAY_KEYS)
        rows+="<tr class=\"subrow\"><td><span class=\"tag "+tag+"\">"+lbl+"</span></td>"+cells+"<td class=\"r mono\">"+(fmt(sub) if sub>0 else "—")+"</td></tr>"
    return rows

def build_count_rows_single(name):
    c=COLORS[name]; rows=""; first=True
    for i,(svc,tag) in enumerate([("DAYCARE","dc"),("BOARDING","bo"),("GROOMING","gr")]):
        total=counts[name].get(svc,{}).get("TOTAL",0)
        cells="".join("<td class=\"c mono\">"+(str(counts[name].get(svc,{}).get(adate(dk),0)) if counts[name].get(svc,{}).get(adate(dk),0)>0 else "—")+"</td>" for dk in DAY_KEYS)
        if i==0:
            rows+="<tr><td class=\"bold\" rowspan=\"3\"><span class=\"dot\" style=\"background:"+c+"\"></span>"+name+"</td><td><span class=\"tag "+tag+"\">"+svc.capitalize()+"</span></td>"+cells+"<td class=\"r mono bold\">"+""+"{:,}".format(total)+"</td></tr>"
        else:
            rows+="<tr><td><span class=\"tag "+tag+"\">"+svc.capitalize()+"</span></td>"+cells+"<td class=\"r mono bold\">"+""+"{:,}".format(total)+"</td></tr>"
    return rows

def build_unpaid_rows_single(name):
    c=COLORS[name]; exp=loc_total(name,"expected"); col2=loc_total(name,"collected")
    unp=loc_total(name,"unpaid"); tips=loc_total(name,"tips")
    uc="red" if unp>0 else "green"; cc="green" if unp==0 else ""
    return "<tr><td class=\"bold\"><span class=\"dot\" style=\"background:"+c+"\"></span>"+name+"</td><td class=\"r mono\">"+fmt(exp)+"</td><td class=\"r mono "+cc+"\">"+fmt(col2)+"</td><td class=\"r mono "+uc+"\">"+fmt(unp)+"</td><td class=\"r mono\">"+fmt(tips)+"</td></tr>"

def build_bonus_rows_single(name):
    c=COLORS[name]; q=q1_data[name]
    if q["ly_full"]==0 and q["ty_qtd"]==0:
        return "<tr><td class=\"bold\"><span class=\"dot\" style=\"background:"+c+"\"></span>"+name+"</td><td colspan=\"7\" style=\"color:#555;font-size:0.75rem\">Starts tracking Q2</td></tr>"
    bc="#22c55e" if q["progress"]>=90 else "#f97316" if q["progress"]>=70 else "#ef4444"
    vs_cls="green" if q["vs_ly"]>=0 else "red"
    vs_str=("+\u200b" if q["vs_ly"]>=0 else "")+"$"+"{:,.2f}".format(q["vs_ly"])+" ("+("+\u200b" if q["vs_pct"]>=0 else "")+"{:.1f}%".format(q["vs_pct"])+")"
    pb=("<div style=\"background:#e2e2d8;border-radius:4px;height:8px;width:100%;min-width:100px\">"
        "<div style=\"background:"+bc+";height:8px;border-radius:4px;width:"+"{:.1f}".format(q["progress"])+"%\"></div></div>"
        "<div style=\"font-size:0.65rem;color:"+bc+";margin-top:3px;font-family:\'DM Mono\',monospace\">"+"{:.1f}".format(q["progress"])+"% to target</div>")
    return ("<tr><td class=\"bold\"><span class=\"dot\" style=\"background:"+c+"\"></span>"+name+"<br><span style=\"font-size:0.65rem;color:#555;font-weight:400\">+"+"{:.0f}".format(q["pct"]*100)+"% target</span></td>"
            "<td class=\"r mono\">"+"$"+"{:,.2f}".format(q["ly_full"])+"</td>"
            "<td class=\"r mono bold\">"+"$"+"{:,.2f}".format(q["target"])+"</td>"
            "<td class=\"r mono\">"+"$"+"{:,.2f}".format(q["ly_same"])+"</td>"
            "<td class=\"r mono bold green\">"+"$"+"{:,.2f}".format(q["ty_qtd"])+"</td>"
            "<td class=\"r mono "+vs_cls+"\">"+vs_str+"</td>"
            "<td class=\"r mono\">"+"$"+"{:,.2f}".format(q["gap"])+"<br><span style=\"font-size:0.65rem;color:#555\">"+"$"+"{:,.0f}/day".format(q["pace"])+" ("+str(q["days_left"])+"d left)</span></td>"
            "<td style=\"min-width:120px\">"+pb+"</td></tr>")

def build_ytd_rows_single(name):
    c=COLORS[name]; y=ytd_data[name]
    diff=y["diff"]; dc2="green" if diff>=0 else "red"
    bc="#16a34a" if y["pct"]>=10 else "#d97706" if y["pct"]>=0 else "#dc2626"
    pb=("<div style=\"background:#e2e2d8;border-radius:4px;height:6px;width:100%;min-width:80px\">"
        "<div style=\"background:"+bc+";height:6px;border-radius:4px;width:"+"{:.1f}".format(min(max((y["ty_ytd"]/y["ly_ytd"]*100) if y["ly_ytd"]>0 else 0,0),150))+"%;max-width:100%\"></div></div>"
        "<div style=\"font-size:0.65rem;color:"+bc+";margin-top:3px;font-family:\'DM Mono\',monospace\">"+("+\u200b" if y["pct"]>=0 else "")+"{:.1f}%".format(y["pct"])+" vs LY</div>")
    return ("<tr><td class=\"bold\"><span class=\"dot\" style=\"background:"+c+"\"></span>"+name+"</td>"
            "<td class=\"r mono bold green\">"+fmt(y["ty_ytd"])+"</td>"
            "<td class=\"r mono\">"+fmt(y["ly_ytd"])+"</td>"
            "<td class=\"r mono "+dc2+"\">"+("+" if diff>=0 else "")+fmt(diff)+"</td>"
            "<td class=\"r mono\">"+fmt(y["ly_full"])+"</td>"
            "<td class=\"r mono\">"+fmt(y["proj"])+"</td>"
            "<td style=\"min-width:120px\">"+pb+"</td></tr>")

def build_wow_rows_single(name):
    c=COLORS[name]; this_wtd=loc_total(name,"expected"); last_w=last_week_rev[name]
    diff=this_wtd-last_w; pct=(diff/last_w*100) if last_w>0 else 0
    dc2="green" if diff>=0 else "red"; ps=("+\u200b" if pct>=0 else "")+"{:.1f}%".format(pct)
    return "<tr><td class=\"bold\"><span class=\"dot\" style=\"background:"+c+"\"></span>"+name+"</td><td class=\"r mono\">"+fmt(this_wtd)+"</td><td class=\"r mono\">"+fmt(last_w)+"</td><td class=\"r mono "+dc2+"\">"+("+" if diff>=0 else "")+fmt(diff)+"</td><td class=\"r mono "+dc2+"\">"+ps+"</td></tr>"

def build_retail_day_rows_single(name):
    c=COLORS[name]; rt=retail[name]; pct2=(rt["total"]/rt["all_rev"]*100) if rt["all_rev"]>0 else 0
    cells="".join("<td class=\"r mono\">"+(fmt(rt["daily"].get(adate(dk),0)) if rt["daily"].get(adate(dk),0)>0 else "—")+"</td>" for dk in DAY_KEYS)
    return "<tr><td class=\"bold\"><span class=\"dot\" style=\"background:"+c+"\"></span>"+name+"</td>"+cells+"<td class=\"r mono bold\">"+fmt(rt["total"])+"</td><td class=\"r mono\">"+"{:.1f}%".format(pct2)+"</td></tr>"

def build_top_item_rows_single(name):
    items=retail[name]["items"]
    sorted_items=sorted(items.items(),key=lambda x:-x[1]["amt"])[:10]
    rows=""
    for item,v in sorted_items:
        rows+="<tr><td>"+item+"</td><td class=\"c mono\">"+"{:,}".format(v["qty"])+"</td><td class=\"r mono\">"+fmt(v["amt"])+"</td></tr>"
    return rows or "<tr><td colspan=\"3\" class=\"dim\">No retail this week</td></tr>"

def build_client_rows_single(name):
    c=COLORS[name]; cl=clients[name]; pct=(cl["new"]/cl["total"]*100) if cl["total"]>0 else 0
    return "<tr><td class=\"bold\"><span class=\"dot\" style=\"background:"+c+"\"></span>"+name+"</td><td class=\"r mono\">"+"{:,}".format(cl["total"])+"</td><td class=\"r mono green\">"+str(cl["new"])+"</td><td class=\"r mono\">"+"{:,}".format(cl["existing"])+"</td><td class=\"r mono\">"+"{:,}".format(cl["recurring"])+"</td><td class=\"r mono\">"+"{:.1f}%".format(pct)+"</td></tr>"

def build_boarding_rows_single(name):
    c=COLORS[name]; bd=boarding_nights[name]; avg=(bd["nights"]/bd["dogs"]) if bd["dogs"]>0 else 0
    return "<tr><td class=\"bold\"><span class=\"dot\" style=\"background:"+c+"\"></span>"+name+"</td><td class=\"r mono\">"+str(bd["dogs"])+"</td><td class=\"r mono\">"+str(bd["nights"])+"</td><td class=\"r mono\">"+"{:.1f}".format(avg)+"</td></tr>"

def build_full_html(tabs, loc_filter=None, pin="0000", title="Central Bark Dashboard"):
    """
    tabs: list of tab names to include e.g. ["cc","full"]
    loc_filter: None = all locations, else location name string
    """
    tab_buttons = ""
    tab_contents = ""
    first = True
    for tab in tabs:
        active = "active" if first else ""
        first = False
        if tab == "cc":
            tab_buttons += f"<div class=\"tab {active}\" onclick=\"showTab('tab-cc',this)\">Command Center</div>"
            tab_contents += f"<div id=\"tab-cc\" class=\"tab-content {active}\">" + build_command_center_tab(loc_filter) + "</div>"
        elif tab == "exec":
            tab_buttons += f"<div class=\"tab {active}\" onclick=\"showTab(\'tab-exec\',this)\">Executive View</div>"
            tab_contents += f"<div id=\"tab-exec\" class=\"tab-content {active}\">" + build_exec_tab(loc_filter) + "</div>"
        elif tab == "full":
            tab_buttons += f"<div class=\"tab {active}\" onclick=\"showTab(\'tab-full\',this)\">Full Detail</div>"
            tab_contents += f"<div id=\"tab-full\" class=\"tab-content {active}\">" + build_full_tab(loc_filter) + "</div>"
        elif tab == "gm":
            tab_buttons += f"<div class=\"tab {active}\" onclick=\"showTab(\'tab-gm\',this)\">GM View</div>"
            tab_contents += f"<div id=\"tab-gm\" class=\"tab-content {active}\">" + build_gm_tab(loc_filter) + "</div>"

    inner = (
        build_header() +
        f"<div class=\"tabs\">{tab_buttons}</div>" +
        tab_contents
    )
    return pin_wrap(inner, pin, CSS, title=title)

# ── GENERATE ALL FILES ─────────────────────────────────────────────────────────
REPO = Path(__file__).parent

log("Generating dashboard files...")

# Owner - all tabs, all locations
owner_html = build_full_html(["cc","full"], loc_filter=None, pin=PINS["owner"], title="Central Bark - Owner")
OUTPUT.write_text(owner_html)
try: OUTPUT2.write_text(owner_html)
except: pass
(REPO / "index.html").write_text(owner_html)
log("  Generated index.html (owner)")

# District Manager - full + gm, all locations
dm_html = build_full_html(["cc","full"], loc_filter=None, pin=PINS["dm"], title="Central Bark - District Manager")
(REPO / "dm.html").write_text(dm_html)
log("  Generated dm.html (district manager)")

# Per-GM files
GM_FILES = {
    "Wauwatosa":          "gm-wauwatosa.html",
    "Milwaukee Downtown": "gm-milwaukee-downtown.html",
    "Grayslake":          "gm-grayslake.html",
    "Milwaukee Eastside": "gm-milwaukee-eastside.html",
    "Mequon":             "gm-mequon.html",
}
for name, filename in GM_FILES.items():
    gm_html = build_full_html(["cc","full"], loc_filter=name, pin=PINS[name], title=f"Central Bark - {name}")
    (REPO / filename).write_text(gm_html)
    log(f"  Generated {filename}")

log("Dashboard saved to " + str(OUTPUT))

# ── PUSH TO GITHUB ─────────────────────────────────────────────────────────────
import shutil as _shutil
try:
    files_to_push = ["index.html","dm.html"] + list(GM_FILES.values())
    for f in files_to_push:
        subprocess.run(["git","-C",str(REPO),"add",f], check=True)
    subprocess.run(["git","-C",str(REPO),"commit","-m","dashboard update "+UPDATED], check=True)
    subprocess.run(["git","-C",str(REPO),"push","origin","main"], check=True)
    log("Pushed all files to GitHub Pages")
except Exception as e:
    log("GitHub push failed: " + str(e))

log("Done.")
