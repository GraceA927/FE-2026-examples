"""
Fetch daily climate for the three northern-Ghana study regions from NASA POWER
and build a climatological "typical year" (365-day day-of-year means) per region.

  Regions (representative site = regional capital / research site):
  upper_east -> Navrongo (10.90 N, 1.09 W)
  upper_west -> Wa       (10.06 N, 2.50 W)
  northern   -> Tamale   ( 9.40 N, 0.84 W)
  
  "upper_east": dict(name="Navrongo", lat=10.90, lon=-1.09),
    "upper_west": dict(name="Wa",       lat=10.06, lon=-2.50),
 

NASA POWER daily point API (no key): T2M (air temp C), RH2M (rel humidity %),
PRECTOTCORR (bias-corrected precip mm/day).

Outputs per region in climate/:
  <region>_daily_raw.csv    - full daily record
  <region>_climatology.csv  - 365-day typical year (doy, airtemp, humidity, rainfall)
  
  
"""
import os
import numpy as np
import pandas as pd
import requests

SITES = {
    
    "upper_west": dict(name="Wa",       lat=10.06, lon=-2.50)
    
}
START, END = "20150101", "20151231"          # 1-year climatological base period
OUTDIR = os.path.join(os.path.dirname(__file__), "climate")
PARAMS = ["T2M", "RH2M", "PRECTOTCORR"]


def fetch(lat, lon):
    url = ("https://power.larc.nasa.gov/api/temporal/daily/point"
           f"?parameters={','.join(PARAMS)}&community=AG"
           f"&longitude={lon}&latitude={lat}&start={START}&end={END}&format=JSON")
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    p = r.json()["properties"]["parameter"]
    df = pd.DataFrame({k: p[k] for k in PARAMS})
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df = df.replace(-999, np.nan).dropna()
    return df.rename(columns={"T2M": "airtemp_C", "RH2M": "rh_pct", "PRECTOTCORR": "rain_mm"})


def climatology(df):
    d = df.copy()
    d["doy"] = d.index.dayofyear
    d = d[d["doy"] <= 365]
    clim = d.groupby("doy").mean(numeric_only=True).reset_index()
    clim["airtemp"] = clim["airtemp_C"]
    clim["humidity"] = (clim["rh_pct"] / 100.0).clip(0, 1)
    clim["rainfall"] = clim["rain_mm"].clip(lower=0)
    return clim[["doy", "airtemp", "humidity", "rainfall"]]


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    print(f"{'region':12s} {'site':10s} {'ann.rain':>9s} {'T mean':>7s} {'RH min':>7s}")
    for region, s in SITES.items():
        df = fetch(s["lat"], s["lon"])
        df.to_csv(os.path.join(OUTDIR, f"{region}_daily_raw.csv"))
        clim = climatology(df)
        clim.to_csv(os.path.join(OUTDIR, f"{region}_climatology.csv"), index=False)
        print(f"{region:12s} {s['name']:10s} {clim.rainfall.sum():8.0f}mm "
              f"{clim.airtemp.mean():6.1f}C {clim.humidity.min():6.2f}")
    print("\nSaved per-region climatology CSVs to", OUTDIR)


if __name__ == "__main__":
    main()
