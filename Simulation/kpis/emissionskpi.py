import csv
import os
import sys
import re
import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt
from pathlib import Path

class EnergyKPI:
    def __init__(self, simulation_path, axs=None):
        self.simulation_path = Path(simulation_path)
        if axs is not None:
            self.plot_all = False
            self.axs0 = axs[0]
        else:
            self.plot_all = True
            self.axs0 = None

    def energykpi(self):
        """Calculates the energy KPI."""

        def plot_consumption(values, ax=None, title="Total Consumption", meas_unit="gCO2e"):
            fig, axes = plt.subplots(nrows=3, ncols=3, sharey=True, figsize=(10, 8))
            axes = axes.flatten()
            x = np.linspace(0, len(values)-1, num=len(values))
            labelservice = [element for element in values[0]]
            y = {}
            yfinal = []

            for i in sorted(values):
                entry = values[i]
                yfinalsum = 0
                for j, (_, stats) in enumerate(entry.items()):
                    avg = float(stats["sum"]) / float(stats["count"])
                    y.setdefault(j, []).append(avg)
                    yfinalsum += avg
                yfinal.append(yfinalsum)

            for i in range(len(values[0])):
                bars = axes[i].bar(x, y[i])
                axes[i].set_title(f"Graph {labelservice[i]}")
                axes[i].set_xlabel("Simulation")
                axes[i].set_xticks(x)
                axes[i].set_xticklabels([int(i) for i in x])
                axes[i].set_ylabel(f"Energy ({meas_unit})")
                shortened_label = [f"{bar.get_height():.2e}" for bar in bars]
                axes[i].bar_label(bars, labels=shortened_label, label_type='center', color='white')

            for i in range(len(values[0]), len(axes)):
                axes[i].axis('off')

            fig.tight_layout()

            if not self.plot_all and ax is not None:
                axes2 = ax
                fig2 = fig
            else:
                fig2, axes2 = plt.subplots()
            bars2 = axes2.bar(x, yfinal)
            axes2.set_title(title)
            axes2.set_xlabel("Simulation round")
            axes2.set_xticks(x)
            axes2.set_xticklabels([int(i) for i in x])
            axes2.set_ylabel(f"Energy ({meas_unit})")
            shortened_label = [f"{bar.get_height():.2e}" for bar in bars2]
            axes2.bar_label(bars2, labels=shortened_label, label_type='center', color='white')

            return fig, fig2

        def plot_movements(values):
            fig, ax = plt.subplots()
            ax.axis("off")
            fig.set_figheight(7)
            fig.set_figwidth(14)
            columns = [f"Iteration {i+1}" for i in range(len(values))]
            y = []
            for i in sorted(values):
                entry = values[i]
                for move in entry:
                    deploy = move["service"] + " → " + move["node"]
                    y.append(deploy)

            final_y = defaultdict(list)
            for entry in y:
                service = entry.split('→')[0].strip()
                final_y[service].append(entry)

            # Convert to list of lists
            result = list(final_y.values())

            table = ax.table(cellText=result, colLabels=columns, loc="center", cellLoc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 2)

            for row in range(len(result)):
                for col in range(1, len(columns)):
                    prev = result[row][col - 1]
                    curr = result[row][col]
                    if prev != curr:
                        table[(row + 1, col)].set_facecolor("#ffc5a1")

            fig.tight_layout()
            return fig

        subfolders = [p for p in self.simulation_path.iterdir() if p.is_dir()]
        conn_paths = {}
        service_paths = {}
        nodes_paths = {}
        conn_emissions = {}
        service_emissions = {}
        node_emissions = {}
        movements = {}

        for i in range(len(subfolders)):
            conn_paths[i] = self.simulation_path / str(i) / "stats" / "interaction.csv"
            service_paths[i] = self.simulation_path / str(i) / "stats" / "service.csv"
            nodes_paths[i] = self.simulation_path / str(i) / "stats" / "node.csv"

            conn_emissions[i] = defaultdict(lambda: {"sum": 0.0, "count": 0})
            with open(conn_paths[i], "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["callback_id"] == "interaction_emissions":
                        if float(row["value"]) > -1:
                            key = re.sub(r'_(large|medium|tiny)$', '', row["source"]) + "," + re.sub(r'_(large|medium|tiny)$', '', row["target"])
                            conn_emissions[i][key]["sum"] += float(row["value"])
                            conn_emissions[i][key]["count"] += 1

            service_emissions[i] = defaultdict(lambda: {"sum": 0.0, "count": 0})
            with open(service_paths[i], "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["callback_id"] == "service_emissions":
                        if float(row["value"]) > -1:
                            key = re.sub(r'_(large|medium|tiny)$', '', row["service_id"])
                            service_emissions[i][key]["sum"] += float(row["value"])
                            service_emissions[i][key]["count"] += 1

            node_emissions[i] = defaultdict(lambda: {"sum": 0.0, "count": 0})
            with open(nodes_paths[i], "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["callback_id"] == "featured_carbon":
                        if float(row["value"]) > -1:
                            key = row["node_id"]
                            node_emissions[i][key]["sum"] += float(row["value"])
                            node_emissions[i][key]["count"] += 1

            movements[i] = []
            with open(service_paths[i], "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["callback_id"] == "placement" and int(row["n_event"]) == 1:
                        placement =  {
                            "service": row["service_id"],
                            "node": row["value"]
                        }
                        movements[i].append(placement)
                movements[i] = sorted(movements[i], key=lambda x: x['service'])

        all_keys = set()
        for iteration in conn_emissions.values():
            all_keys.update(iteration.keys())
        for iteration_dict in conn_emissions.values():
            for key in all_keys:
                iteration_dict.setdefault(key, {'sum': 0.0, 'count': 1})
        for i in conn_emissions:
            conn_emissions[i] = dict(sorted(conn_emissions[i].items()))

        all_keys = set()
        for iteration in service_emissions.values():
            all_keys.update(iteration.keys())
        for iteration_dict in service_emissions.values():
            for key in all_keys:
                iteration_dict.setdefault(key, {'sum': 0.0, 'count': 1})
        for i in service_emissions:
            service_emissions[i] = dict(sorted(service_emissions[i].items()))

        all_keys = set()
        for iteration in node_emissions.values():
            all_keys.update(iteration.keys())
        for iteration_dict in node_emissions.values():
            for key in all_keys:
                iteration_dict.setdefault(key, {'sum': 0.0, 'count': 1})
        for i in node_emissions:
            node_emissions[i] = dict(sorted(node_emissions[i].items()))

        all_services = {entry["service"] for entries in movements.values() for entry in entries}
        for i in movements:
            all_keys = {entry["service"]: entry for entry in movements[i]}
            for service in all_services:
                if service not in all_keys:
                    all_keys[service] = {"service": service, "node": "-"}
            movements[i] = sorted(all_keys.values(), key=lambda x: x["service"])

        serive_fig, service_fig_final = plot_consumption(service_emissions, ax=self.axs0, title="Total service consumption")
        conn_fig, conn_fig_final = plot_consumption(conn_emissions)
        node_fig, node_fig_final = plot_consumption(node_emissions, meas_unit="gC02e/kWh")
        movements_fig = plot_movements(movements)

        return [
            serive_fig,
            service_fig_final,
            conn_fig,
            conn_fig_final,
            node_fig,
            node_fig_final,
            movements_fig
        ]

def emissions(path, axs=None):
    figs = EnergyKPI(path / "simulations", axs=axs).energykpi()

    titles = [
        "service_results",
        "service_results_final",
        "connection_results",
        "connection_results_final",
        "node_results",
        "node_results_final",
        "service_movements"
    ]

    return [
        (fig, path / "kpis" / (title + ".png"))
        for fig, title in list(zip(figs, titles))
    ]

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else input("Enter path: ")
    path = os.path.abspath(path)

    for fig, path in emissions(path):
        fig.savefig(path)
