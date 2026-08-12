"""
Fetch daily climate for Upper West Region districts from NASA POWER
and build a climatological "typical year" (365-day day-of-year means)
for each district.

Climate variables:
    T2M          - air temperature (°C)
    RH2M         - relative humidity (%)
    PRECTOTCORR  - bias-corrected precipitation (mm/day)

Output:
    climate/
        <district>_daily_raw.csv
        <district>_climatology.csv
"""

import os
import numpy as np
import pandas as pd
import requests


# ============================================================
# UPPER WEST DISTRICTS
# ============================================================
# Replace these coordinates with your preferred district
# representative coordinates (ideally district centroids).

DISTRICTS = {

    "Wa Municipal": {
    "lat": 10.06,
    "lon": -2.50
},

"Wa West": {
    "lat": 9.95,
    "lon": -2.60
},

"Nadowli-Kaleo": {
    "lat": 10.37,
    "lon": -2.83
},

"Lawra": {
    "lat": 10.65,
    "lon": -2.89
},

"Jirapa": {
    "lat": 10.55,
    "lon": -2.70
},

"Nandom": {
    "lat": 10.85,
    "lon": -2.93
},

"Sissala East": {
    "lat": 10.75,
    "lon": -2.18
},

"Sissala West": {
    "lat": 10.65,
    "lon": -2.38
},

"Daffiama Bussie Issa": {
    "lat": 10.29,
    "lon": -2.45
},

"Lambussie Karni": {
    "lat": 10.88,
    "lon": -2.76
},

"Wa East": {
    "lat": 10.16,
    "lon": -2.15
}

}
# ============================================================
# DATE RANGE
# ============================================================

START = "20150101"
END = "20251231"


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

OUTDIR = os.path.join(os.path.dirname(__file__), "climate")


# ============================================================
# NASA POWER PARAMETERS
# ============================================================

PARAMS = [
    "T2M",
    "RH2M",
    "PRECTOTCORR"
]


# ============================================================
# FETCH NASA POWER DATA
# ============================================================

def fetch(lat, lon):

    url = (
        "https://power.larc.nasa.gov/api/temporal/daily/point"
        f"?parameters={','.join(PARAMS)}"
        f"&community=AG"
        f"&longitude={lon}"
        f"&latitude={lat}"
        f"&start={START}"
        f"&end={END}"
        f"&format=JSON"
    )

    print(f"Requesting NASA POWER data for ({lat}, {lon})...")

    r = requests.get(url, timeout=120)
    r.raise_for_status()

    p = r.json()["properties"]["parameter"]

    df = pd.DataFrame({
        k: p[k]
        for k in PARAMS
    })

    df.index = pd.to_datetime(
        df.index,
        format="%Y%m%d"
    )

    # NASA POWER missing-value code
    df = df.replace(-999, np.nan)

    df = df.dropna()

    return df.rename(
        columns={
            "T2M": "airtemp_C",
            "RH2M": "rh_pct",
            "PRECTOTCORR": "rain_mm"
        }
    )


# ============================================================
# CREATE CLIMATOLOGICAL TYPICAL YEAR
# ============================================================

def climatology(df):

    d = df.copy()

    # Day of year
    d["doy"] = d.index.dayofyear

    # Remove February 29
    d = d[d["doy"] <= 365]

    # Average each day-of-year across all years
    clim = (
        d.groupby("doy")
        .mean(numeric_only=True)
        .reset_index()
    )

    # EMOD-friendly variable names
    clim["airtemp"] = clim["airtemp_C"]

    # Convert RH percentage to 0–1
    clim["humidity"] = (
        clim["rh_pct"] / 100.0
    ).clip(0, 1)

    # Ensure rainfall is non-negative
    clim["rainfall"] = (
        clim["rain_mm"]
        .clip(lower=0)
    )

    return clim[
        [
            "doy",
            "airtemp",
            "humidity",
            "rainfall"
        ]
    ]


# ============================================================
# MAIN
# ============================================================

def main():

    os.makedirs(
        OUTDIR,
        exist_ok=True
    )

    print(
        f"{'district':25s} "
        f"{'ann.rain':>10s} "
        f"{'T mean':>8s} "
        f"{'RH min':>8s}"
    )

    print("-" * 60)

    for district, location in DISTRICTS.items():

        lat = location["lat"]
        lon = location["lon"]

        # Skip districts without coordinates
        if lat is None or lon is None:

            print(
                f"Skipping {district}: "
                f"coordinates not provided"
            )

            continue

        print(
            f"\nFetching climate for {district}..."
        )

        # Fetch daily NASA POWER data
        df = fetch(lat, lon)

        # Safe filename
        district_file = (
            district
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

        # Save raw daily data
        raw_file = os.path.join(
            OUTDIR,
            f"{district_file}_daily_raw.csv"
        )

        df.to_csv(raw_file)

        # Create climatology
        clim = climatology(df)

        # Save climatology
        clim_file = os.path.join(
            OUTDIR,
            f"{district_file}_climatology.csv"
        )

        clim.to_csv(
            clim_file,
            index=False
        )

        # Summary
        print(
            f"{district:25s} "
            f"{clim['rainfall'].sum():10.0f}mm "
            f"{clim['airtemp'].mean():8.1f}C "
            f"{clim['humidity'].min():8.2f}"
        )

    print(
        "\nSaved district-level climate files to:",
        OUTDIR
    )


if __name__ == "__main__":
    main()