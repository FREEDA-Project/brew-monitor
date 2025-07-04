import sys, re
from pathlib import Path
import matplotlib.pyplot as plt
from collections import defaultdict

def parse_failure_file(file_path):
    unreachable_count = defaultdict(int)
    overload_count = defaultdict(int)

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Match unreachable(component, tick).
            unreachable_match = re.match(r'unreachable\(([\w_]+),\s*(\d+)\)', line)
            if unreachable_match:
                component = unreachable_match.group(1)
                unreachable_count[component] += 1

            # Match overload(node, resource, start, end).
            overload_match = re.match(r'overload\(([\w_]+),\s*([\w_]+),\s*(\d+),\s*(\d+)\)', line)
            if overload_match:
                node = overload_match.group(1)
                resource = overload_match.group(2)
                start = int(overload_match.group(3))
                end = int(overload_match.group(4))
                duration = end - start + 1
                overload_count[f"{node}.{resource}"] += duration

    return unreachable_count, overload_count


def plot_combined_failures(all_unreachable, all_overloads):
    comp_labels = []
    comp_heights = []

    for file_idx, comp_counts in enumerate(all_unreachable):
        for comp in sorted(comp_counts.keys()):
            label = f"{file_idx}.{comp}"
            comp_labels.append(label)
            comp_heights.append(comp_counts[comp])

    node_labels = []
    node_heights = []

    for file_idx, node_counts in enumerate(all_overloads):
        for node in sorted(node_counts.keys()):
            label = f"{file_idx}.{node}"
            node_labels.append(label)
            node_heights.append(node_counts[node])


    fig, axs = plt.subplots(2, 1, figsize=(16, 8))

    # Component failures
    axs[0].bar(range(len(comp_labels)), comp_heights)
    axs[0].set_title("Component Failures")
    axs[0].set_ylabel("Ticks")
    axs[0].set_xticks(range(len(comp_labels)))
    axs[0].set_xticklabels(comp_labels, rotation=0, ha='center')
    axs[0].grid(axis = 'y', linestyle = '--', linewidth = 0.5)
    # Node failures
    axs[1].bar(range(len(node_labels)), node_heights, color='purple')
    axs[1].set_title("Node Failures")
    axs[1].set_ylabel("Ticks")
    axs[1].set_xticks(range(len(node_labels)))
    axs[1].set_xticklabels(node_labels, rotation=0, ha='center')
    axs[1].grid(axis = 'y', linestyle = '--', linewidth = 0.5)

    fig.tight_layout(rect=[0, 0, 1, 0.95])

    return fig

def failures(base_folder):
    failures_folder = base_folder / "FailureEnhancer"

    # Find all files needed
    failures_files = sorted(failures_folder.glob('*/deployment.pl'))
    for failures_file in failures_files:
        print(f"Found file: {failures_file}")

    all_unreachable = []
    all_overloads = []

    for failures_file in failures_files:
        unreachable, overload = parse_failure_file(failures_file)
        all_unreachable.append(unreachable)
        all_overloads.append(overload)

    fig = plot_combined_failures(all_unreachable, all_overloads)

    output_file = base_folder / "kpis" / "failures_report.png"

    return fig, output_file

if __name__ == "__main__":
    # Get base folder
    base_folder = Path(sys.argv[1])
    # Path to the script directory
    script_dir = Path(__file__).parent.resolve()

    fig, output_file = failures(base_folder)
    fig.savefig(output_file)
    print(f"Saved combined plot to {output_file}")
