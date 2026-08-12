"""
Build EMOD climate/weather files (.bin + .bin.json) for EACH Upper West
district from its NASA POWER climatological year.

Each district is an independent single-node model (node id 1), so each gets
its own weather set in climate/emod_weather_<district>/.

Run the district climate-fetch script first to produce:
    climate/<district>_climatology.csv
"""

import os
import json
import numpy as np
import pandas as pd

from emodpy_malaria.weather import (
    csv_to_weather,
    WeatherVariable,
    WeatherAttributes
)


# ============================================================
# UPPER WEST DISTRICTS
# ============================================================

DISTRICTS = {

    "wa_municipal": dict(lat=10.06, lon=-2.50),

    "wa_west": dict(lat=9.95, lon=-2.60),

    "nadowli_kaleo": dict(lat=10.37, lon=-2.83),

    "lawra": dict(lat=10.65, lon=-2.89),

    "jirapa": dict(lat=10.55, lon=-2.70),

    "nandom": dict(lat=10.85, lon=-2.93),

    "sissala_east": dict(lat=10.75, lon=-2.18),

    "sissala_west": dict(lat=10.65, lon=-2.38),

    "daffiama_bussie_issa": dict(lat=10.29, lon=-2.45),

    "lambussie_karni": dict(lat=10.88, lon=-2.76),

    "wa_east": dict(lat=10.16, lon=-2.15),

}


NODE_ID = 1
YEARS = 50  # # total weather coverage: burn-in + historical + projection

DEMOG_ID_REF = "Gridded world grump2.5arcmin"

CLIM_DIR = os.path.join(
    os.path.dirname(__file__),
    "climate"
)


# ============================================================
# WEATHER FILE NAMES
# ============================================================

FILE_NAMES = {

    WeatherVariable.AIR_TEMPERATURE:
        "air_temperature.bin",

    WeatherVariable.RELATIVE_HUMIDITY:
        "relative_humidity.bin",

    WeatherVariable.RAINFALL:
        "rainfall.bin",

    WeatherVariable.LAND_TEMPERATURE:
        "land_temperature.bin",
}


# ============================================================
# BUILD WEATHER FOR ONE DISTRICT
# ============================================================

def build_district(district, lat, lon):

    # Read district climatology
    clim = pd.read_csv(
        os.path.join(
            CLIM_DIR,
            f"{district}_climatology.csv"
        )
    ).sort_values("doy")

    assert len(clim) == 365, (
        f"{district}: expected 365-day climatology, "
        f"got {len(clim)}"
    )


    # --------------------------------------------------------
    # Tile climatology
    # --------------------------------------------------------

    airtemp = np.tile(
        clim["airtemp"].values,
        YEARS
    )

    humidity = np.tile(
        clim["humidity"].values,
        YEARS
    )

    rainfall = np.tile(
        clim["rainfall"].values,
        YEARS
    )

    n = len(airtemp)


    # --------------------------------------------------------
    # Create EMOD weather dataframe
    # --------------------------------------------------------

    df = pd.DataFrame({

        "nodes": NODE_ID,

        "steps": np.arange(n),

        "airtemp": airtemp,

        "humidity": humidity,

        "rainfall": rainfall,

        # Use air temperature as land temperature,
        # as no separate land-temperature variable was
        # downloaded from NASA POWER.
        "landtemp": airtemp,
    })


    # --------------------------------------------------------
    # Weather metadata
    # --------------------------------------------------------

    attrs = WeatherAttributes(

        reference=DEMOG_ID_REF,

        start_year=2015,

        end_year=2016,

        start_doy=1,

        lat_min=lat,

        lat_max=lat,

        lon_min=lon,

        lon_max=lon,

        provenance=(
            f"NASA POWER daily 2015-2025 climatology, "
            f"{district}"
        ),

        resolution="daily",

        update_freq="CLIMATE_UPDATE_DAY",
    )


    # --------------------------------------------------------
    # District-specific EMOD weather directory
    # --------------------------------------------------------

    wdir = os.path.join(
        CLIM_DIR,
        f"emod_weather_{district}"
    )

    os.makedirs(
        wdir,
        exist_ok=True
    )


    # --------------------------------------------------------
    # Convert CSV data to EMOD weather binaries
    # --------------------------------------------------------

    csv_to_weather(

        csv_data=df,

        node_column="nodes",

        step_column="steps",

        weather_columns={

            WeatherVariable.AIR_TEMPERATURE:
                "airtemp",

            WeatherVariable.RELATIVE_HUMIDITY:
                "humidity",

            WeatherVariable.RAINFALL:
                "rainfall",

            WeatherVariable.LAND_TEMPERATURE:
                "landtemp",
        },

        attributes=attrs,

        weather_dir=wdir,

        weather_file_names=FILE_NAMES,
    )


    # --------------------------------------------------------
    # Remove WeatherSchemaVersion so this Eradication
    # uses the legacy parser
    # --------------------------------------------------------

    for f in os.listdir(wdir):

        if f.endswith(".bin.json"):

            p = os.path.join(
                wdir,
                f
            )

            with open(p, "r") as file:

                meta = json.load(file)

            meta.get(
                "Metadata",
                {}
            ).pop(
                "WeatherSchemaVersion",
                None
            )

            with open(p, "w") as file:

                json.dump(
                    meta,
                    file,
                    indent=4
                )


    return wdir, n


# ============================================================
# MAIN
# ============================================================

def main():

    for district, coords in DISTRICTS.items():

        wdir, n = build_district(

            district,

            coords["lat"],

            coords["lon"]
        )

        print(
            f"{district:25s} -> "
            f"{wdir}  "
            f"({n} days, node {NODE_ID})"
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()
