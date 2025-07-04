#!/usr/bin/env python
import os, argparse, itertools, traceback
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as patches

from freeda import main as freeda

##### This is super ugly, but it reserchers code :) ######
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from brew_update_policy import (brewBestFit)

from update_policy import (scenarioDEMOinfrastructure, 
                           scenarioDEMOapplication, 
                           scenarioDEMOapplication2, 
                           scenario3, noscenario,
                           energyapp1, energyapp2, energyapp3,
                           energyinfr1, energyinfr2, energyinfr3, ebestfit, edatabase, eloadbalancer, efrontend)
##########################################################

from kpis.generateKPIs import getKPIs, saveKPIs

# Validation parameters
location = Path("./validations-" + datetime.today().strftime('%Y-%m-%d_%H:%M:%S'))
os.makedirs(location, exist_ok=True)
application_policies = [
    [noscenario, noscenario, noscenario, noscenario]
]
infrastructure_policies = [
    [brewBestFit, brewBestFit, brewBestFit, brewBestFit]
]
loops = min(len(application_policies), len(infrastructure_policies))
priority = "failure"


def combinations(
    solver_path : str,
    energy_enhancer_path : str,
    application_policies,
    infrastructure_policies
):
    failure = [False, True]
    solver = [None, solver_path]
    energy = [None, energy_enhancer_path]
    result = [
        (a, i, s, f, e)
        for a, i in zip(application_policies, infrastructure_policies)
        for s, f, e in itertools.product(solver, failure, energy)
    ]

    result = [
        (a, i, s, f, e)
        for (a, i, s, f, e) in result
        if (s is None and f == False and e is None) or (s is not None)
    ]

    return result

def simulation_name(solver, failure, energy):
    name = "priority" + priority.capitalize() + "_"
    name += ("yes" if solver else "no") + "solver_"
    name += ("yes" if failure else "no") + "failure_"
    name += ("yes" if energy else "no") + "energy"
    return name

def generate_final_plot(simulations):
    fig, axes = plt.subplots(
        nrows=len(simulations),
        ncols=3,
        figsize=(20, 30)
    )

    for (s, f, e, folder), ax_row in zip(simulations, axes):
        getKPIs(folder, fig, ax_row)

        conf = "Prioritizing " + priority + ", "
        conf += ("with" if s else "without") + " solver, "
        conf += ("with" if f else "without") + " failure, "
        conf += ("with" if e else "without") + " energy"

        pos = [ax.get_position() for ax in ax_row]

        left = min([p.x0 for p in pos]) - 0.01  # margine extra
        right = max([p.x1 for p in pos]) + 0.01
        bottom = min([p.y0 for p in pos]) - 0.01
        top = max([p.y1 for p in pos]) + 0.01

        fig.add_artist(patches.FancyBboxPatch(
            (left + 0.028, bottom + 0.06),
            right - left - 0.1,
            top - bottom - 0.115,
            boxstyle="round,pad=0.04",
            edgecolor='blue',
            facecolor='none',
            linewidth=1.5,
            zorder=2
        ))

        # Testo centrato dentro al riquadro
        fig.text(
            (left + right) / 2,
            top - 0.015,
            conf,
            ha='center',
            va='center',
            fontsize=16,
            fontweight='bold',
            color='blue',
            bbox=dict(facecolor='white', edgecolor='none', pad=3.0),
            zorder=3
        )

    # Lascia spazio attorno alla figura (margini extra)
    fig.subplots_adjust(left=0.08, right=0.92, top=0.95, bottom=0.07, hspace=1, wspace=0.3)
    fig.savefig(location / "general_plot")
    plt.close(fig)

def main(parser, energy, components, infrastructure, additional_resources):
    simulations = []
    for a, i, s, f, e in combinations(parser, energy, application_policies, infrastructure_policies):
        simulation_location = (location / simulation_name(s, f, e)).absolute()
        try:
            freeda(
                Path(simulation_location),
                Path(s) if s else None,
                Path(e) if e else None,
                f,
                Path(components),
                Path(infrastructure),
                priority,
                Path(additional_resources),
                a,
                i
            )

            simulations.append((s, f, e, simulation_location))
        except Exception as e:
            print(traceback.format_exc())

        # KPIs
        kpi_folder = simulation_location / "kpis"
        os.makedirs(kpi_folder, exist_ok=True)
        saveKPIs(simulation_location)

    generate_final_plot(simulations)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FREEDA validator over ECLYPSE simulator")
    parser.add_argument("parser", type=str, help="Parser's folder location")
    parser.add_argument("energy", type=str, help="EnergyEnhancer's folder location")
    parser.add_argument("components", type=str, help="Starting components YAML file")
    parser.add_argument("infrastructure", type=str, help="Starting infrastructure YAML file")
    parser.add_argument(
        "--additional-resources",
        "-r",
        metavar="resources",
        type=str,
        help="Resources YAML file path",
        default=None
    )
    args = parser.parse_args()

    main(args.parser, args.energy, args.components, args.infrastructure, args.additional_resources)
