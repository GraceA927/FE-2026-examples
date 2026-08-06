"""
Build EMOD climate/weather files (.bin + .bin.json) for EACH of the three study
regions from its NASA POWER climatological year, tiled to cover the full run.

Each region is an independent single-node model (node id 1), so each gets its own
weather set in climate/emod_weather_<region>/.

Run climate_fetch.py first to produce climate/<region>_climatology.csv.
For future reference, the NASA POWER daily point API (no key) is used to fetch T2M
"upper_east": dict(lat=10.90, lon=-1.09),
    "northern":   dict(lat=9.40,  lon=-0.84),

"""
import os
import json
import numpy as np
import pandas as pd

from emodpy_malaria.weather import csv_to_weather, WeatherVariable, WeatherAttributes

REGIONS = {
    
    "upper_west": dict(lat=10.06, lon=-2.50),
    
}
NODE_ID = 1
YEARS = 1                     # covers 6-yr burn-in + historical + projection
DEMOG_ID_REF = "Gridded world grump2.5arcmin"    # must match demographics IdReference
CLIM_DIR = os.path.join(os.path.dirname(__file__), "climate")

FILE_NAMES = {
    WeatherVariable.AIR_TEMPERATURE: "air_temperature.bin",
    WeatherVariable.RELATIVE_HUMIDITY: "relative_humidity.bin",
    WeatherVariable.RAINFALL: "rainfall.bin",
    WeatherVariable.LAND_TEMPERATURE: "land_temperature.bin",
}


def build_region(region, lat, lon):
    clim = pd.read_csv(os.path.join(CLIM_DIR, f"{region}_climatology.csv")).sort_values("doy")
    assert len(clim) == 365, f"{region}: expected 365-day climatology, got {len(clim)}"

    airtemp = np.tile(clim["airtemp"].values, YEARS)
    humidity = np.tile(clim["humidity"].values, YEARS)
    rainfall = np.tile(clim["rainfall"].values, YEARS)
    n = len(airtemp)
    df = pd.DataFrame({
        "nodes": NODE_ID, "steps": np.arange(n),
        "airtemp": airtemp, "humidity": humidity,
        "rainfall": rainfall, "landtemp": airtemp,
    })

    attrs = WeatherAttributes(
        reference=DEMOG_ID_REF, start_year=2015, end_year=2016, start_doy=1,#edit year NB from climate_fetch.py
        lat_min=lat, lat_max=lat, lon_min=lon, lon_max=lon,
        provenance=f"NASA POWER daily 2015-2016 climatology, {region}", #edit year NB from climate_fetch.py
        resolution="daily", update_freq="CLIMATE_UPDATE_DAY",
    )

    wdir = os.path.join(CLIM_DIR, f"emod_weather_{region}")
    os.makedirs(wdir, exist_ok=True)
    csv_to_weather(
        csv_data=df, node_column="nodes", step_column="steps",
        weather_columns={WeatherVariable.AIR_TEMPERATURE: "airtemp",
                         WeatherVariable.RELATIVE_HUMIDITY: "humidity",
                         WeatherVariable.RAINFALL: "rainfall",
                         WeatherVariable.LAND_TEMPERATURE: "landtemp"},
        attributes=attrs, weather_dir=wdir, weather_file_names=FILE_NAMES,
    )
    # strip WeatherSchemaVersion so this Eradication uses the legacy parser
    for f in os.listdir(wdir):
        if f.endswith(".bin.json"):
            p = os.path.join(wdir, f)
            meta = json.load(open(p))
            meta.get("Metadata", {}).pop("WeatherSchemaVersion", None)
            json.dump(meta, open(p, "w"), indent=4)
    return wdir, n


def main():
    for region, coords in REGIONS.items():
        wdir, n = build_region(region, coords["lat"], coords["lon"])
        print(f"{region:12s} -> {wdir}  ({n} days, node {NODE_ID})")


if __name__ == "__main__":
    main()
