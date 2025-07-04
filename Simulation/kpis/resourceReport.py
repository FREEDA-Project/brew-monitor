import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys

def generate_resource_plot(csv_file):
    df = pd.read_csv(csv_file)

    # Filter data
    cpu_data = df[df['callback_id'] == 'featured_cpu']
    ram_data = df[df['callback_id'] == 'featured_ram']

    # Set style
    sns.set(style="whitegrid")

    # Create figure with subplots
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # Plot featured_cpu
    sns.lineplot(data=cpu_data, x='n_event', y='value', hue='node_id', marker='o', ax=axes[0])
    axes[0].set_ylabel('Featured CPU')
    axes[0].legend(title='Node ID', bbox_to_anchor=(1.05, 1), loc='upper left')

    # Plot featured_ram
    sns.lineplot(data=ram_data, x='n_event', y='value', hue='node_id', marker='o', ax=axes[1])
    axes[1].set_ylabel('Featured RAM')
    axes[1].set_xlabel('Simulation Tick')
    axes[1].legend(title='Node ID', bbox_to_anchor=(1.05, 1), loc='upper left')

    # Layout adjustment and save
    plt.tight_layout()
    return fig

def resource(base_folder):
    simulations_folder = base_folder / "simulations"
    # Get all subdirectories inside 'simulations'
    subfolders = [f for f in simulations_folder.iterdir() if f.is_dir()]
    # Optional: sort them
    subfolders = sorted(subfolders)
    # Find all csv files
    # Loop through subfolders and find node.csv files
    results = {}
    for subfolder in subfolders:
        csv_files = sorted(subfolder.glob('*/node.csv'))
        for csv_file in csv_files:
            print(f"Found csv file: {csv_file}")
            output = base_folder / "kpis" / f"featured_resources_{subfolder.name}.png"
            fig = generate_resource_plot(csv_file)
            results[output.absolute()] = fig

    return results

if __name__ == "__main__":
    # Get base folder
    base_folder = Path(sys.argv[1])
    resource(base_folder)