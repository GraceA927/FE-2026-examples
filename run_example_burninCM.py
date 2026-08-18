import os
import pathlib
from functools import partial

import numpy as np

from idmtools.builders import SimulationBuilder
from idmtools.core.platform_factory import Platform
from idmtools.entities.experiment import Experiment

from emodpy.emod_task import EMODTask
import emod_api.campaign as camp

import emodpy_malaria.demographics.MalariaDemographics as Demographics
import emod_api.demographics.PreDefinedDistributions as Distributions
from emodpy_malaria.reporters.builtin import *

import manifest


sim_years = 50
num_seeds = 5
sim_start_year = 2000
serialize_years = 50


def set_param_fn(config):
    """
    Configure the EMOD malaria simulation.
    """
    import emodpy_malaria.malaria_config as conf

    config = conf.set_team_defaults(config, manifest)

    config.parameters.Climate_Model = "CLIMATE_BY_DATA"

    config.parameters.Air_Temperature_Filename = os.path.join(
        "climate",
        "air_temperature.bin"
    )

    config.parameters.Land_Temperature_Filename = os.path.join(
        "climate",
        "land_temperature.bin"
    )

    config.parameters.Rainfall_Filename = os.path.join(
        "climate",
        "rainfall.bin"
    )

    config.parameters.Relative_Humidity_Filename = os.path.join(
        "climate",
        "relative_humidity.bin"
    )

    config.parameters.Enable_Default_Reporting = 1

    conf.add_species(
        config,
        manifest,
        ["gambiae", "arabiensis", "funestus"]
    )

    config.parameters.Simulation_Duration = sim_years * 365
    config.parameters.Run_Number = 0

    config.parameters.Serialized_Population_Writing_Type = "TIMESTEP"
    config.parameters.Serialization_Time_Steps = [
        365 * serialize_years
    ]
    config.parameters.Serialization_Mask_Node_Write = 0
    config.parameters.Serialization_Precision = "REDUCED"

    return config


def set_param(simulation, param, value):
    """
    Set a simulation parameter.
    """
    return simulation.task.set_parameter(param, value)


def build_camp():
    """
    Build the EMOD campaign.
    """
    camp.set_schema(manifest.schema_file)
    return camp


def build_demog():
    """
    Build the demographics file.
    """
    demog = Demographics.from_template_node(
        lat=10.06,
        lon=-2.50,
        pop=1000,
        name="Wa"
    )

    demog.SetEquilibriumVitalDynamics()
    demog.SetAgeDistribution(
        Distributions.AgeDistribution_SSAfrica
    )

    return demog


def general_sim(selected_platform):
    """
    Create and run the 50-year malaria burn-in experiment.
    """

    platform = Platform(
        selected_platform,
        job_directory=manifest.job_directory,
        partition=manifest.partition,
        time=manifest.sim_time,
        modules=[manifest.singularity_module],
        max_running_jobs=manifest.max_running_jobs
    )

    builder = SimulationBuilder()

    builder.add_sweep_definition(
        partial(
            set_param,
            param="Run_Number"
        ),
        range(num_seeds)
    )

    builder.add_sweep_definition(
        partial(
            set_param,
            param="x_Temporary_Larval_Habitat"
        ),
        np.logspace(-0.5, 1, 10)
    )

    print("Creating EMODTask (from files)...")

    task = EMODTask.from_default2(
        config_path="config.json",
        eradication_path=manifest.eradication_path,
        campaign_builder=build_camp,
        schema_path=manifest.schema_file,
        param_custom_cb=set_param_fn,
        ep4_custom_cb=None,
        demog_builder=build_demog,
        plugin_report=None
    )

    task.set_sif(
        manifest.SIF_PATH,
        platform
    )

    climate_dir = os.path.join(
        manifest.input_dir,
        "emod_weather_upper_west"
    )

    task.common_assets.add_directory(
        climate_dir,
        relative_path="climate"
    )

    add_event_recorder(
        task,
        event_list=["HappyBirthday", "Births"],
        start_day=1,
        end_day=sim_years * 365,
        node_ids=[1],
        min_age_years=0,
        max_age_years=100
    )

    for year in range(sim_years):
        start_day = 365 * year
        end_day = 365 * (year + 1)
        calendar_year = sim_start_year + year

        add_malaria_summary_report(
            task,
            manifest,
            start_day=start_day,
            end_day=end_day,
            reporting_interval=30,
            age_bins=[0.25, 5, 115],
            max_number_reports=13,
            pretty_format=True,
            filename_suffix=f"Monthly_U5_{calendar_year}"
        )

    user = os.environ.get("USER", "user")

    experiment = Experiment.from_builder(
        builder,
        task,
        name=f"{user}_FE_example_burnin50CM"
    )

    print(f"Submitting 50-year burn-in experiment: {experiment.uid}")

    experiment.run(
        wait_until_done=False,
        platform=platform
    )


if __name__ == "__main__":
    import emod_malaria.bootstrap as dtk

    dtk.setup(
        pathlib.Path(manifest.eradication_path).parent
    )

    os.chmod(
        manifest.eradication_path,
        0o755
    )

    selected_platform = "SLURM_LOCAL"

    general_sim(selected_platform)