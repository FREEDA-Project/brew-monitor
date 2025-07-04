import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import yaml

importance_pattern = "App quality"
costs_pattern = "Total cost"
carbs_pattern = "Total carb"

def get_value_from_deployment_file(f, pattern, array):
    content = [l for l in f.readlines() if pattern in l][0]
    array.append(int(content.split(":")[-1]))
    f.seek(0)

def deployment(folder, fig=None, ax=None):
    xs = []
    importances = []
    costs = []
    carbs = []
    for name in sorted(folder.glob("solver/*/deployment.txt")):
        xs.append(int(str(name).split("/")[-2]))
        with open(name, "r") as f:
            get_value_from_deployment_file(f, importance_pattern, importances)
            if not fig:
                get_value_from_deployment_file(f, costs_pattern, costs)
                get_value_from_deployment_file(f, carbs_pattern, carbs)

    with open(folder / "solver" / "0" / "importances.yaml") as f:
        importances_dict = yaml.safe_load(f)
    m = sum(max(importances_dict[k].values()) for k in importances_dict)

    importances = [(y / m) * 100 for y in importances]

    if not fig:
        with open(folder / "solver" / "0" / "components.yaml") as f:
            reqs = yaml.safe_load(f)
        cost_budget = reqs["requirements"]["budget"]["cost"]
        carb_budget = reqs["requirements"]["budget"]["carbon"]

        fig, axes = plt.subplots(
            nrows=1,
            ncols=3,
            sharex=True,
            figsize = (15, 5)
        )

        axes[0].scatter(xs, importances)
        axes[0].plot(xs, importances, linestyle="dashed")
        axes[0].set_title("Importance of flavours over time")
        axes[0].set_xlabel("Time")
        axes[0].set_ylabel("Flavour importance percentage")
        axes[0].xaxis.set_major_locator(MaxNLocator(integer=True))
        axes[0].set_ylim(bottom=0, top=105)

        axes[1].scatter(xs, costs)
        axes[1].plot(xs, costs, linestyle="dashed")
        axes[1].plot(xs, [cost_budget] * len(xs), linestyle="dashed", color="red")
        axes[1].set_title("Cost of deployment over time")
        axes[1].set_xlabel("Time")
        axes[1].set_ylabel("Cost")
        #axes[1].xaxis.set_major_locator(MaxNLocator(integer=True))

        axes[2].scatter(xs, carbs)
        axes[2].plot(xs, carbs, linestyle="dashed")
        axes[2].plot(xs, [carb_budget] * len(xs), linestyle="dashed", color="red")
        axes[2].set_title("Carbon consumption of deployment over time")
        axes[2].set_xlabel("Time")
        axes[2].set_ylabel("Carb (gCO2e)")
        #axes[2].xaxis.set_major_locator(MaxNLocator(integer=True))

        fig.tight_layout()
    else:
        ax.scatter(xs, importances)
        ax.plot(xs, importances, linestyle="dashed")
        ax.set_ylim(bottom=0, top=105)
        ax.set_title("Importance of flavours over time")
        ax.set_xlabel("Simulation round")
        ax.set_ylabel("Flavour importance percentage")
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    output_name = (folder / "kpis" / "deployment_report").absolute()

    return fig, output_name

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FREEDA solver kpi calculator")
    parser.add_argument('simulation_folder', type=Path)
    args = parser.parse_args()

    fig, output_name = deployment(Path(args.simulation_folder).absolute())
    fig.savefig(output_name)
