"""
compare_burnin_10yr_vs_50yr.py

AWS/EMOD version.

Purpose
-------
Compare epidemiological outputs from:

    10-year burn-in
    50-year burn-in
    10-year burn-in -> pickup
    50-year burn-in -> pickup

The main objective is to determine whether increasing the burn-in
period from 10 years to 50 years produces meaningful differences
in the simulated epidemiological trajectories.

Expected input files
--------------------
    All_Age_InsetChart_burnin.csv
    All_Age_InsetChart_burnin50.csv
    All_Age_InsetChart_pickup.csv
    All_Age_InsetChart_pickup50.csv

Expected channels
-----------------
    Statistical Population
    New Clinical Cases
    Adult Vectors
    Infected

Outputs
-------
    01_burnin_10yr_vs_50yr.png
    02_pickup_10yr_vs_50yr.png
    03_joined_burnin_to_pickup_10yr_vs_50yr.png
    04_difference_50yr_minus_10yr.png
    05_percentage_difference_50yr_vs_10yr.png
    06_all_scenarios_comparison.png
    07_individual_runs_and_mean_10yr_vs_50yr.png
    08_endpoint_comparison.png
    burnin_10yr_vs_50yr_summary.csv

Run    python compare_burnin_10yr_vs_50yr.py
"""


from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import numpy as np
import pandas as pd


BASE_DIR = Path(
    "/shared/home/grace/FE-2026-examples/experiments/"
    "my_outputs/grace_FE_example_outputs"
)


# Output directory

OUTPUT_DIR = BASE_DIR / "burnin_10yr_vs_50yr_comparison"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# INPUT FILES

FILES = {
    "burnin":
        BASE_DIR / "All_Age_InsetChart_burnin.csv",

    "burnin50":
        BASE_DIR / "All_Age_InsetChart_burnin50.csv",

    "pickup":
        BASE_DIR / "All_Age_InsetChart_pickup.csv",

    "pickup50":
        BASE_DIR / "All_Age_InsetChart_pickup50.csv",
}


# CHANNELS

CHANNELS = [
    "Statistical Population",
    "New Clinical Cases",
    "Adult Vectors",
    "Infected",
]


# LABELS

SCENARIO_LABELS = {
    "burnin": "10-year Burn-in",
    "burnin50": "50-year Burn-in",
    "pickup": "10-year Pickup",
    "pickup50": "50-year Pickup",
}


# COLORS

COLORS = {
    "burnin": "#1f77b4",
    "burnin50": "#d62728",
    "pickup": "#2ca02c",
    "pickup50": "#ff7f0e",
}


# LOAD DATA

def load_scenario(scenario):

    path = FILES[scenario]

    
    print(f"Loading: {scenario}")
    print(f"File:    {path}")

    if not path.exists():

        raise FileNotFoundError(
            f"\n\nERROR: File does not exist:\n{path}\n\n"
            "Check that the analyzer has created the expected CSV "
            "and that BASE_DIR is correct."
        )

    df = pd.read_csv(path)

    print(
        f"Rows:       {len(df):,}"
    )

    print(
        f"Columns:    {len(df.columns)}"
    )

    # Date

    if "date" not in df.columns:

        raise ValueError(
            f"{path} does not contain a 'date' column."
        )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    if df["date"].isna().all():

        raise ValueError(
            f"Could not convert the date column in {path}."
        )


    if "Run_Number" not in df.columns:

        print(
            "[WARNING] Run_Number column not found."
        )

        print(
            "Creating Run_Number = 0."
        )

        df["Run_Number"] = 0

    missing = [
        channel
        for channel in CHANNELS
        if channel not in df.columns
    ]

    if missing:

        print(
            f"[WARNING] Missing channels: {missing}"
        )

    available = [
        channel
        for channel in CHANNELS
        if channel in df.columns
    ]

    print(
        f"Available channels: {available}"
    )


    df = df.sort_values(
        ["Run_Number", "date"]
    ).reset_index(drop=True)

    # Print date range

    print(
        f"Date range: "
        f"{df['date'].min().date()} "
        f"to "
        f"{df['date'].max().date()}"
    )

    print(
        f"Number of runs: "
        f"{df['Run_Number'].nunique()}"
    )

    return df


# RUN-LEVEL STATISTICS

def calculate_statistics(df):

    available_channels = [
        channel
        for channel in CHANNELS
        if channel in df.columns
    ]

    records = []

    for date, group in df.groupby("date"):

        record = {
            "date": date
        }

        for channel in available_channels:

            values = (
                group[channel]
                .dropna()
                .to_numpy()
            )

            if len(values) == 0:
                continue

            mean = np.mean(values)

            if len(values) > 1:

                sd = np.std(
                    values,
                    ddof=1
                )

                se = sd / np.sqrt(
                    len(values)
                )

                lower = (
                    mean - 1.96 * se
                )

                upper = (
                    mean + 1.96 * se
                )

            else:

                lower = mean
                upper = mean

            record[
                f"{channel}_mean"
            ] = mean

            record[
                f"{channel}_lower"
            ] = lower

            record[
                f"{channel}_upper"
            ] = upper

        records.append(record)

    return (
        pd.DataFrame(records)
        .sort_values("date")
        .reset_index(drop=True)
    )


# FIGURE SETUP

def create_figure(title):

    fig, axes = plt.subplots(
        2,
        2,
        figsize=(15, 10)
    )

    axes = axes.flatten()

    fig.suptitle(
        title,
        fontsize=16,
        fontweight="bold"
    )

    fig.subplots_adjust(
        left=0.08,
        right=0.97,
        bottom=0.10,
        top=0.90,
        hspace=0.35,
        wspace=0.25
    )

    return fig, axes


# AXIS STYLE

def style_axis(ax):

    ax.xaxis.set_major_locator(
        mdates.YearLocator(2)
    )

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%Y")
    )

    ax.tick_params(
        axis="x",
        rotation=45
    )

    ax.grid(
        True,
        linestyle="--",
        alpha=0.3
    )


# LOAD ALL FOUR SCENARIOS

print()
print("=" * 70)
print("LOADING EMOD SERIALIZATION OUTPUTS")
print("=" * 70)

data = {}

for scenario in FILES:

    data[scenario] = load_scenario(
        scenario
    )


# CALCULATE STATISTICS

print()
print("=" * 70)
print("CALCULATING RUN STATISTICS")
print("=" * 70)

statistics = {}

for scenario, df in data.items():

    statistics[scenario] = (
        calculate_statistics(df)
    )


# DETERMINE AVAILABLE CHANNELS

available_channels = [
    channel
    for channel in CHANNELS
    if any(
        channel in df.columns
        for df in data.values()
    )
]

print()
print("Channels to plot:")

for channel in available_channels:

    print(
        f"  {channel}"
    )



# 10-YEAR VS 50-YEAR BURN-IN

print()
print("=" * 70)
print("FIGURE 1: 10-YEAR VS 50-YEAR BURN-IN")
print("=" * 70)

fig, axes = create_figure(
    "10-Year vs 50-Year Burn-in"
)

for i, channel in enumerate(
    available_channels
):

    ax = axes[i]

    for scenario in [
        "burnin",
        "burnin50"
    ]:

        stats = statistics[scenario]

        mean_col = (
            f"{channel}_mean"
        )

        lower_col = (
            f"{channel}_lower"
        )

        upper_col = (
            f"{channel}_upper"
        )

        if mean_col not in stats.columns:
            continue

        ax.plot(
            stats["date"],
            stats[mean_col],
            linewidth=2,
            color=COLORS[scenario],
            label=SCENARIO_LABELS[scenario]
        )

        # 95% CI across simulation runs
        ax.fill_between(
            stats["date"],
            stats[lower_col],
            stats[upper_col],
            color=COLORS[scenario],
            alpha=0.12
        )

    ax.set_title(
        channel,
        fontsize=13,
        fontweight="bold"
    )

    ax.set_ylabel(
        "Simulated value"
    )

    style_axis(ax)

    ax.legend(
        fontsize=9
    )

for j in range(
    len(available_channels),
    len(axes)
):

    axes[j].axis("off")

output = (
    OUTPUT_DIR /
    "01_burnin_10yr_vs_50yr.png"
)

fig.savefig(
    output,
    dpi=300,
    bbox_inches="tight"
)

plt.close(fig)

print(
    f"Saved: {output}"
)



# 10-YEAR VS 50-YEAR PICKUP  

print()
print("=" * 70)
print("FIGURE 2: 10-YEAR VS 50-YEAR PICKUP")
print("=" * 70)

fig, axes = create_figure(
    "10-Year vs 50-Year Pickup"
)

for i, channel in enumerate(
    available_channels
):

    ax = axes[i]

    for scenario in [
        "pickup",
        "pickup50"
    ]:

        stats = statistics[scenario]

        mean_col = (
            f"{channel}_mean"
        )

        lower_col = (
            f"{channel}_lower"
        )

        upper_col = (
            f"{channel}_upper"
        )

        if mean_col not in stats.columns:
            continue

        ax.plot(
            stats["date"],
            stats[mean_col],
            linewidth=2,
            color=COLORS[scenario],
            label=SCENARIO_LABELS[scenario]
        )

        ax.fill_between(
            stats["date"],
            stats[lower_col],
            stats[upper_col],
            color=COLORS[scenario],
            alpha=0.12
        )

    ax.set_title(
        channel,
        fontsize=13,
        fontweight="bold"
    )

    ax.set_ylabel(
        "Simulated value"
    )

    style_axis(ax)

    ax.legend(
        fontsize=9
    )

for j in range(
    len(available_channels),
    len(axes)
):

    axes[j].axis("off")

output = (
    OUTPUT_DIR /
    "02_pickup_10yr_vs_50yr.png"
)

fig.savefig(
    output,
    dpi=300,
    bbox_inches="tight"
)

plt.close(fig)

print(
    f"Saved: {output}"
)

# JOINED BURN-IN -> PICKUP FIGURE 3

print()
print("=" * 70)
print("FIGURE 3: BURN-IN -> PICKUP")
print("=" * 70)

fig, axes = create_figure(
    "Burn-in → Pickup: 10-Year vs 50-Year Serialization"
)

JOIN_PAIRS = [
    (
        "burnin",
        "pickup",
        "10-year Burn-in → Pickup",
        "#1f77b4"
    ),
    (
        "burnin50",
        "pickup50",
        "50-year Burn-in → Pickup",
        "#d62728"
    )
]

for i, channel in enumerate(
    available_channels
):

    ax = axes[i]

    for (
        burnin_key,
        pickup_key,
        label,
        color
    ) in JOIN_PAIRS:

        burnin_stats = (
            statistics[burnin_key]
        )

        pickup_stats = (
            statistics[pickup_key]
        )

        mean_col = (
            f"{channel}_mean"
        )

        if mean_col not in burnin_stats.columns:
            continue

        if mean_col not in pickup_stats.columns:
            continue

        burnin_df = burnin_stats[
            ["date", mean_col]
        ].copy()

        pickup_df = pickup_stats[
            ["date", mean_col]
        ].copy()

        # Join the two periods

        joined = pd.concat(
            [
                burnin_df,
                pickup_df
            ],
            ignore_index=True
        )

        joined = (
            joined
            .drop_duplicates(
                subset="date",
                keep="last"
            )
            .sort_values("date")
        )

        ax.plot(
            joined["date"],
            joined[mean_col],
            linewidth=2,
            color=color,
            label=label
        )

        # Burn-in / pickup transition

        transition_date = (
            burnin_df["date"].max()
        )

        ax.axvline(
            transition_date,
            color=color,
            linestyle=":",
            linewidth=1.5,
            alpha=0.8
        )

    ax.set_title(
        channel,
        fontsize=13,
        fontweight="bold"
    )

    ax.set_ylabel(
        "Simulated value"
    )

    style_axis(ax)

    ax.legend(
        fontsize=8
    )

for j in range(
    len(available_channels),
    len(axes)
):

    axes[j].axis("off")

output = (
    OUTPUT_DIR /
    "03_joined_burnin_to_pickup_10yr_vs_50yr.png"
)

fig.savefig(
    output,
    dpi=300,
    bbox_inches="tight"
)

plt.close(fig)

print(
    f"Saved: {output}"
)

# 50-YEAR - 10-YEAR ABSOLUTE DIFFERENCE

print()
print("=" * 70)
print("FIGURE 4: ABSOLUTE DIFFERENCE")
print("=" * 70)

fig, axes = create_figure(
    "Difference: 50-Year Burn-in − 10-Year Burn-in"
)

for i, channel in enumerate(
    available_channels
):

    ax = axes[i]

    stats10 = statistics[
        "burnin"
    ]

    stats50 = statistics[
        "burnin50"
    ]

    mean_col = (
        f"{channel}_mean"
    )

    if (
        mean_col not in stats10.columns
        or
        mean_col not in stats50.columns
    ):

        continue

    merged = pd.merge(
        stats10[
            ["date", mean_col]
        ],
        stats50[
            ["date", mean_col]
        ],
        on="date",
        suffixes=(
            "_10yr",
            "_50yr"
        )
    )

    difference = (
        merged[
            f"{mean_col}_50yr"
        ]
        -
        merged[
            f"{mean_col}_10yr"
        ]
    )

    ax.plot(
        merged["date"],
        difference,
        linewidth=2,
        color="#9467bd",
        label="50-year − 10-year"
    )

    ax.axhline(
        0,
        color="black",
        linewidth=1
    )

    ax.set_title(
        channel,
        fontsize=13,
        fontweight="bold"
    )

    ax.set_ylabel(
        "Absolute difference"
    )

    style_axis(ax)

    ax.legend(
        fontsize=9
    )

for j in range(
    len(available_channels),
    len(axes)
):

    axes[j].axis("off")

output = (
    OUTPUT_DIR /
    "04_difference_50yr_minus_10yr.png"
)

fig.savefig(
    output,
    dpi=300,
    bbox_inches="tight"
)

plt.close(fig)

print(
    f"Saved: {output}"
)

# ((50-year - 10-year) / 10-year) * 100 PERCENTAGE DIFFERENCE

print()
print("=" * 70)
print("FIGURE 5: PERCENTAGE DIFFERENCE")
print("=" * 70)

fig, axes = create_figure(
    "Percentage Difference: 50-Year vs 10-Year Burn-in"
)

for i, channel in enumerate(
    available_channels
):

    ax = axes[i]

    stats10 = statistics[
        "burnin"
    ]

    stats50 = statistics[
        "burnin50"
    ]

    mean_col = (
        f"{channel}_mean"
    )

    if (
        mean_col not in stats10.columns
        or
        mean_col not in stats50.columns
    ):

        continue

    merged = pd.merge(
        stats10[
            ["date", mean_col]
        ],
        stats50[
            ["date", mean_col]
        ],
        on="date",
        suffixes=(
            "_10yr",
            "_50yr"
        )
    )

    denominator = (
        merged[
            f"{mean_col}_10yr"
        ].replace(
            0,
            np.nan
        )
    )

    percentage = (
        (
            merged[
                f"{mean_col}_50yr"
            ]
            -
            merged[
                f"{mean_col}_10yr"
            ]
        )
        /
        denominator
    ) * 100

    ax.plot(
        merged["date"],
        percentage,
        linewidth=2,
        color="#e377c2",
        label="% difference"
    )

    ax.axhline(
        0,
        color="black",
        linewidth=1
    )

    ax.set_title(
        channel,
        fontsize=13,
        fontweight="bold"
    )

    ax.set_ylabel(
        "Difference (%)"
    )

    style_axis(ax)

    ax.legend(
        fontsize=9
    )

for j in range(
    len(available_channels),
    len(axes)
):

    axes[j].axis("off")

output = (
    OUTPUT_DIR /
    "05_percentage_difference_50yr_vs_10yr.png"
)

fig.savefig(
    output,
    dpi=300,
    bbox_inches="tight"
)

plt.close(fig)

print(
    f"Saved: {output}"
)



# ALL FOUR SCENARIOS



fig, axes = create_figure(
    "All Serialization Scenarios"
)

for i, channel in enumerate(
    available_channels
):

    ax = axes[i]

    for scenario in [
        "burnin",
        "burnin50",
        "pickup",
        "pickup50"
    ]:

        stats = statistics[
            scenario
        ]

        mean_col = (
            f"{channel}_mean"
        )

        if mean_col not in stats.columns:
            continue

        ax.plot(
            stats["date"],
            stats[mean_col],
            linewidth=1.7,
            color=COLORS[scenario],
            label=SCENARIO_LABELS[scenario]
        )

    ax.set_title(
        channel,
        fontsize=13,
        fontweight="bold"
    )

    ax.set_ylabel(
        "Simulated value"
    )

    style_axis(ax)

    ax.legend(
        fontsize=8
    )

for j in range(
    len(available_channels),
    len(axes)
):

    axes[j].axis("off")

output = (
    OUTPUT_DIR /
    "06_all_scenarios_comparison.png"
)

fig.savefig(
    output,
    dpi=300,
    bbox_inches="tight"
)

plt.close(fig)

print(
    f"Saved: {output}"
)


# INDIVIDUAL RUNS + MEAN

print()
print("=" * 70)
print("FIGURE 7: INDIVIDUAL RUNS + MEAN")
print("=" * 70)

fig, axes = create_figure(
    "Simulation Variability: 10-Year vs 50-Year Burn-in"
)

for i, channel in enumerate(
    available_channels
):

    ax = axes[i]

    for scenario in [
        "burnin",
        "burnin50"
    ]:

        df = data[
            scenario
        ]

        # Individual simulation runs

        for (
            run_number,
            run_df
        ) in df.groupby(
            "Run_Number"
        ):

            if channel not in run_df.columns:
                continue

            ax.plot(
                run_df["date"],
                run_df[channel],
                color=COLORS[scenario],
                linewidth=0.6,
                alpha=0.25
            )

        # Mean

        stats = statistics[
            scenario
        ]

        mean_col = (
            f"{channel}_mean"
        )

        if mean_col not in stats.columns:
            continue

        ax.plot(
            stats["date"],
            stats[mean_col],
            color=COLORS[scenario],
            linewidth=2.5,
            label=SCENARIO_LABELS[scenario]
        )

    ax.set_title(
        channel,
        fontsize=13,
        fontweight="bold"
    )

    ax.set_ylabel(
        "Simulated value"
    )

    style_axis(ax)

    ax.legend(
        fontsize=8
    )

for j in range(
    len(available_channels),
    len(axes)
):

    axes[j].axis("off")

output = (
    OUTPUT_DIR /
    "07_individual_runs_and_mean_10yr_vs_50yr.png"
)

fig.savefig(
    output,
    dpi=300,
    bbox_inches="tight"
)

plt.close(fig)

print(
    f"Saved: {output}"
)


# FIGURE 8
#
# ENDPOINT COMPARISON

print()
print("=" * 70)
print("FIGURE 8: ENDPOINT COMPARISON")
print("=" * 70)

fig, axes = create_figure(
    "End-of-Series Epidemiological Comparison"
)

endpoint_records = []

for i, channel in enumerate(
    available_channels
):

    ax = axes[i]

    labels = []
    values = []

    for scenario in [
        "burnin",
        "burnin50",
        "pickup",
        "pickup50"
    ]:

        stats = statistics[
            scenario
        ]

        mean_col = (
            f"{channel}_mean"
        )

        if mean_col not in stats.columns:
            continue

        stats = (
            stats
            .sort_values("date")
        )

        endpoint = (
            stats[
                mean_col
            ].iloc[-1]
        )

        labels.append(
            SCENARIO_LABELS[
                scenario
            ]
        )

        values.append(
            endpoint
        )

        endpoint_records.append(
            {
                "Channel":
                    channel,

                "Scenario":
                    SCENARIO_LABELS[
                        scenario
                    ],

                "Endpoint":
                    endpoint
            }
        )

    ax.bar(
        labels,
        values
    )

    ax.set_title(
        channel,
        fontsize=13,
        fontweight="bold"
    )

    ax.set_ylabel(
        "Final simulated value"
    )

    ax.tick_params(
        axis="x",
        rotation=35
    )

    ax.grid(
        True,
        axis="y",
        linestyle="--",
        alpha=0.3
    )

for j in range(
    len(available_channels),
    len(axes)
):

    axes[j].axis("off")

output = (
    OUTPUT_DIR /
    "08_endpoint_comparison.png"
)

fig.savefig(
    output,
    dpi=300,
    bbox_inches="tight"
)

plt.close(fig)

print(
    f"Saved: {output}"
)


# NUMERICAL SUMMARY

print()
print("=" * 70)
print("CALCULATING NUMERICAL 10-YEAR VS 50-YEAR COMPARISON")
print("=" * 70)

summary_records = []

for channel in available_channels:

    mean_col = (
        f"{channel}_mean"
    )

    stats10 = statistics[
        "burnin"
    ]

    stats50 = statistics[
        "burnin50"
    ]

    if (
        mean_col not in stats10.columns
        or
        mean_col not in stats50.columns
    ):

        continue

    merged = pd.merge(
        stats10[
            ["date", mean_col]
        ],
        stats50[
            ["date", mean_col]
        ],
        on="date",
        suffixes=(
            "_10yr",
            "_50yr"
        )
    )

    if merged.empty:

        print(
            f"[WARNING] No matching dates for "
            f"{channel}"
        )

        continue

    value10 = merged[
        f"{mean_col}_10yr"
    ]

    value50 = merged[
        f"{mean_col}_50yr"
    ]

    absolute_difference = (
        value50 - value10
    )

    percentage_difference = (
        absolute_difference
        /
        value10.replace(
            0,
            np.nan
        )
    ) * 100

    summary_records.append(
        {
            "Channel":
                channel,

            "Mean_10yr":
                value10.mean(),

            "Mean_50yr":
                value50.mean(),

            "Mean_Absolute_Difference":
                absolute_difference.mean(),

            "Mean_Percentage_Difference":
                percentage_difference.mean(),

            "Maximum_Absolute_Difference":
                absolute_difference.abs().max(),

            "Maximum_Percentage_Difference":
                percentage_difference.abs().max(),

            "Final_10yr":
                value10.iloc[-1],

            "Final_50yr":
                value50.iloc[-1],

            "Final_Absolute_Difference":
                absolute_difference.iloc[-1],

            "Final_Percentage_Difference":
                percentage_difference.iloc[-1],
        }
    )


# SAVE SUMMARY

summary_df = pd.DataFrame(
    summary_records
)

summary_file = (
    OUTPUT_DIR /
    "burnin_10yr_vs_50yr_summary.csv"
)

summary_df.to_csv(
    summary_file,
    index=False
)

print(
    f"\nSaved summary:"
)

print(
    summary_file
)


# PRINT SUMMARY

print()
print("=" * 80)
print("10-YEAR VS 50-YEAR BURN-IN RESULTS")
print("=" * 80)

if summary_df.empty:

    print(
        "No numerical comparison was generated."
    )

else:

    for _, row in summary_df.iterrows():

        print()
        print(
            f"CHANNEL: {row['Channel']}"
        )

        print(
            f"  Mean 10-year: "
            f"{row['Mean_10yr']:.4f}"
        )

        print(
            f"  Mean 50-year: "
            f"{row['Mean_50yr']:.4f}"
        )

        print(
            f"  Mean absolute difference: "
            f"{row['Mean_Absolute_Difference']:.4f}"
        )

        print(
            f"  Mean percentage difference: "
            f"{row['Mean_Percentage_Difference']:.2f}%"
        )

        print(
            f"  Maximum percentage difference: "
            f"{row['Maximum_Percentage_Difference']:.2f}%"
        )

        print(
            f"  Final 10-year: "
            f"{row['Final_10yr']:.4f}"
        )

        print(
            f"  Final 50-year: "
            f"{row['Final_50yr']:.4f}"
        )

        print(
            f"  Final percentage difference: "
            f"{row['Final_Percentage_Difference']:.2f}%"
        )


# FINAL OUTPUT

print()
print("=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)

print()
print(
    "Output directory:"
)

print(
    OUTPUT_DIR
)

print()
print(
    "Generated files:"
)

for file in sorted(
    OUTPUT_DIR.iterdir()
):

    print(
        f"  {file.name}"
    )

print()
print("=" * 80)