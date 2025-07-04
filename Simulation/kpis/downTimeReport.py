import re
import matplotlib.pyplot as plt
import sys
from pathlib import Path

def parse_log(log_path):
    tick_pattern = re.compile(r"Simulation - Event Tick-(\d+) fired")
    placement_pattern = re.compile(r"PlacementManager - Placement of")

    try:
        with open(log_path, 'r', encoding='utf-8') as f: # Specify encoding
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: Log file not found at {log_path}")
        return [], set(), []

    current_tick = None
    placement_ticks = set()
    all_ticks = []

    for line in lines:
        tick_match = tick_pattern.search(line)
        placement_match = placement_pattern.search(line)
        if tick_match:
            current_tick = int(tick_match.group(1))
            all_ticks.append(current_tick)
        if placement_match and current_tick is not None:
            placement_ticks.add(current_tick)

    downtimes = []
    in_downtime = False
    start_tick = None

    for tick in sorted(all_ticks):
        if tick not in placement_ticks:
            if not in_downtime:
                in_downtime = True
                start_tick = tick
        else:
            if in_downtime:
                downtimes.append((start_tick, tick - 1))
                in_downtime = False
    if in_downtime:
        downtimes.append((start_tick, all_ticks[-1]))

    return all_ticks, placement_ticks, downtimes

def generate_comparison_plot(log_stats, fig=None, ax=None):
    if not log_stats:
        print("No log available to generate a plot.")
        return

    labels = [label for label, _, _ in log_stats]
    uptimes = [uptime for _, uptime, _ in log_stats]
    downtimes = [downtime for _, _, downtime in log_stats]

    num_labels = len(labels)
    x = range(len(labels))
    width = 0.35

    if num_labels == 1:
        fig_width = 3.5
    elif num_labels == 2:
        fig_width = 4.5
    else:
        fig_width = max(8.0, num_labels * 0.9)

    fig_height = 5

    if not fig:
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    ax.bar(x, uptimes, width, label='Uptime (%)', color='green')
    ax.bar(x, downtimes, width, bottom=uptimes, label='Downtime (%)', color='red')

    ax.set_ylabel("Downtime and uptime percentage")
    ax.set_title('Uptime and downtime over time')
    ax.set_xticks(x)
    ax.set_xticklabels([str(i) for i in x])
    ax.set_xlabel("Simulation round")
    ax.set_ylim(0, 105)

    for i in range(len(labels)):
        if uptimes[i] > 0:
            ax.text(i, uptimes[i] / 2, f"{uptimes[i]:.1f}%",
                    ha='center', va='center', color='white', fontsize=8, fontweight='bold')
        if downtimes[i] > 0:
            ax.text(i, uptimes[i] + downtimes[i] / 2, f"{downtimes[i]:.1f}%",
                    ha='center', va='center', color='white', fontsize=8, fontweight='bold')

    fig.tight_layout()
    return fig

def down_time(base_folder, fig=None, ax=None):
    simulations_folder = base_folder / "simulations"

    # Find all 'simulation.log' files
    log_files = sorted(simulations_folder.glob('*/simulation.log'))
    for log_file in log_files:
        print(f"Found log file: {log_file}")

    stats = []

    for log_file in log_files:
        if not log_file.is_file():
            print(f"Warning: Log file '{log_file}' not found or is not a file. Skipping.")
            continue

        label = log_file.stem
        all_sim_ticks, placement_ticks_set, _ = parse_log(log_file)

        total_unique_ticks_observed = len(all_sim_ticks)
        uptime_ticks_count = len(placement_ticks_set)
        uptime_percent = (uptime_ticks_count / total_unique_ticks_observed) * 100 if total_unique_ticks_observed > 0 else 0.0
        downtime_percent = 100.0 - uptime_percent
        stats.append((label, uptime_percent, downtime_percent))

    output_file = base_folder / "kpis" / "downtime_comparison"

    if stats:
        if fig:
            generate_comparison_plot(stats, fig, ax)
            return None, None
        else:
            return generate_comparison_plot(stats), output_file
    else:
        return None, None

if __name__ == "__main__":
    # Get base folder
    base_folder = Path(sys.argv[1])

    fig, output_file = down_time(base_folder)

    if fig:
        try:
            fig.savefig(output_file)
            print(f"Plot saved to {output_file}")
        except Exception as e:
            print(f"Error saving plot to {output_file}: {e}")
    else:
        print("No data processed to generate a plot.")
