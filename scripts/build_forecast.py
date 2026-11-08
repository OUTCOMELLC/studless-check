#!/usr/bin/env python3
"""Studless Check Japan: build one shared forecast file for every visitor.

Run by GitHub Actions every 6 hours. Visitors then read data/forecast.json from
GitHub Pages instead of each calling the weather service, so the number of
weather calls stays the same whether 10 or 100,000 people use the site.

Uses only the Python standard library. Weather data: Open-Meteo (free, non-commercial).
"""
import datetime, json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "index.html")
DATA = os.path.join(ROOT, "data")
GRID_FILE = os.path.join(DATA, "grid.json")
OUT_FILE = os.path.join(DATA, "forecast.json")

GRID_STEP = 0.2                      # degrees, about 20 km
BOX = (31.0, 45.6, 129.4, 146.0)     # Hokkaido, Honshu, Shikoku, Kyushu (Okinawa excluded)
BATCH = 100                          # locations per request
PAUSE = 15                           # seconds between requests: stays under the free per-minute limit
VARS = "temperature_2m_min,snowfall_sum,precipitation_sum"
HEADERS = {"User-Agent": "StudlessCheckJapan (+https://outcometn.com)"}


def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # network error or rate limit: back off and retry
            print(f"  request failed ({e}); retry {i + 1}/{tries}", flush=True)
            if i == tries - 1:
                raise
            time.sleep(60 * (i + 1))


def named_places():
    """Read POINTS, PASSES and PICKUPS from index.html so there is one source of truth."""
    html = open(HTML, encoding="utf-8").read()
    out = []
    for name, lat_i in (("POINTS", 2), ("PASSES", 2), ("PICKUPS", 3)):
        m = re.search(r"const " + name + r"\s*=\s*(\[.*?\])\.map\(", html, re.S)
        if not m:
            sys.exit(f"Could not find {name} in index.html")
        for row in json.loads(m.group(1)):
            out.append([row[lat_i], row[lat_i + 1]])
    return out


def is_japan(lat, lon):
    if lat >= 34.9 and lon <= 130.6:   # Korean east coast
        return False
    if lat >= 43.55 and lon >= 145.4:  # Kunashir
        return False
    return True


def build_grid():
    """Land points on a 0.2 degree grid. Built once (sea points have height 0), then reused."""
    if os.path.exists(GRID_FILE):
        return json.load(open(GRID_FILE))
    cand, lat = [], BOX[0]
    while lat <= BOX[1] + 1e-9:
        lon = BOX[2]
        while lon <= BOX[3] + 1e-9:
            if is_japan(lat, lon):
                cand.append((round(lat, 2), round(lon, 2)))
            lon += GRID_STEP
        lat += GRID_STEP
    print(f"Building land grid from {len(cand)} candidates (first run only)", flush=True)
    keep = []
    for i in range(0, len(cand), BATCH):
        b = cand[i:i + BATCH]
        q = urllib.parse.urlencode({"latitude": ",".join(str(p[0]) for p in b),
                                    "longitude": ",".join(str(p[1]) for p in b)})
        j = get("https://api.open-meteo.com/v1/elevation?" + q)
        for p, e in zip(b, j.get("elevation", [])):
            if e is not None and e > 0:
                keep.append([p[0], p[1]])
        time.sleep(PAUSE)
    os.makedirs(DATA, exist_ok=True)
    json.dump(keep, open(GRID_FILE, "w"), separators=(",", ":"))
    print(f"Land grid: {len(keep)} points", flush=True)
    return keep


def fetch(points):
    out = []
    for i in range(0, len(points), BATCH):
        b = points[i:i + BATCH]
        q = urllib.parse.urlencode({"latitude": ",".join(f"{p[0]:.3f}" for p in b),
                                    "longitude": ",".join(f"{p[1]:.3f}" for p in b),
                                    "daily": VARS, "timezone": "Asia/Tokyo", "forecast_days": 16})
        j = get("https://api.open-meteo.com/v1/forecast?" + q)
        out.extend(j if isinstance(j, list) else [j])
        print(f"  forecast {min(i + BATCH, len(points))}/{len(points)}", flush=True)
        if i + BATCH < len(points):
            time.sleep(PAUSE)
    return out


def r1(v):
    return None if v is None else round(v, 1)


def main():
    points = named_places() + build_grid()
    print(f"Fetching forecasts for {len(points)} locations", flush=True)
    fcs = fetch(points)
    if len(fcs) != len(points) or len(fcs) < 500:
        sys.exit("Incomplete forecast; keeping the previous file")
    rows = []
    for p, f in zip(points, fcs):
        d = f["daily"]
        rows.append([p[0], p[1], round(f.get("elevation") or 0),
                     [r1(v) for v in d["temperature_2m_min"]],
                     [r1(v or 0) for v in d["snowfall_sum"]],
                     [r1(v or 0) for v in d["precipitation_sum"]]])
    doc = {"generated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="minutes"),
           "source": "Open-Meteo", "days": fcs[0]["daily"]["time"], "pts": rows}
    os.makedirs(DATA, exist_ok=True)
    tmp = OUT_FILE + ".tmp"
    json.dump(doc, open(tmp, "w"), separators=(",", ":"))
    os.replace(tmp, OUT_FILE)
    print(f"Wrote {OUT_FILE}: {len(rows)} locations, {os.path.getsize(OUT_FILE) // 1024} KB", flush=True)


if __name__ == "__main__":
    main()
