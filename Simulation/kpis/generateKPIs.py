import os
from pathlib import Path

import matplotlib.pyplot as plt

from .deploymentkpi import deployment
from .downTimeReport import down_time
from .emissionskpi import emissions
from .failuresReport import failures
from .resourceReport import resource

# Meant to be run only from validation.py

def getKPIs(base_folder: Path, fig = None, axs = None):
    functions = [deployment, down_time, failures]
    figures = {}

    if fig:
        deployment(base_folder, fig, axs[0])
        down_time(base_folder, fig, axs[1])
    else:
        for f in functions:
            print(f"Running {f.__name__} report...")
            fig_generated, output_path = f(base_folder)
            figures[output_path] = fig_generated
            print()

    figures = figures | resource(base_folder)

    if fig:
        emissions(base_folder, axs[2:])
    else:
        print(f"Running emissions report...")
        for emission_fig, path in emissions(base_folder):
            emission_fig.savefig(path)

            filename = os.path.basename(Path(path).absolute())
            if "final" in filename and "connection" not in filename:
                figures[path] = emission_fig
        print()

    return figures

def saveKPIs(base_folder: Path):
    figures = getKPIs(base_folder)

    for path, fig in figures.items():
        fig.savefig(path)
        plt.close(fig)
