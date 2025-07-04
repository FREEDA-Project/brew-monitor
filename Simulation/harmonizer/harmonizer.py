# python harmonizer.py -f failures_constraints.pl -e energy_constraints.pl -o outputfile
# python harmonizer.py -f failures_constraints.pl -e energy_constraints.pl -p failure/energy -o outputfile

import argparse
import re
import yaml
from collections import defaultdict
import logging
from pathlib import Path

def get_constraints(filename, failure_format):
    constraints = []
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('%'):
                if failure_format:
                    line = re.sub(r"d\(([^,]+),([^)]+)\)", r"\1,\2", line)
                constraints.append(line)
    return constraints

def build_affinity_groups(constraints):
    parent = {}
    edges = {}

    def find(x):
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x, y, constraint):
        parent.setdefault(x, x)
        parent.setdefault(y, y)
        root_x, root_y = find(x), find(y)
        if root_x != root_y:
            parent[root_x] = root_y
        edges.setdefault(frozenset([x, y]), set()).add(constraint)

    for constraint in constraints:
        # r"affinity\(([^,]+),([^,]+),([^,]+),([^,]+)"
        # r"affinity\(([^,]+),([^,]+),([^,]+),([^,]+)(?:,[^)]+)?\)"
        # match = re.match(r"affinity\(([^,]+),([^,]+),([^,]+),([^,\)]+)\)", constraint, re.IGNORECASE)
        match = re.match(r"affinity\(([^,]+),([^,]+),([^,]+),([^,]+)(?:,[^)]+)?\)", constraint, re.IGNORECASE)
        if match:
            c1, flav1, c2, flav2 = map(str.strip, match.groups())
            comp1 = f"{c1},{flav1}"
            comp2 = f"{c2},{flav2}"
            union(comp1, comp2, constraint)

    return parent, edges

def find_conflicting_constraints(constraints):
    conflicts = set()
    groups, edges = build_affinity_groups(constraints)
    reverse_groups = defaultdict(set)

    for comp, root in groups.items():
        reverse_groups[root].add(comp)

    group_conflicts = defaultdict(set)

    for constraint in constraints:
        # r"anti-affinity\(([^,]+),([^,]+),([^,]+),([^,]+)(?:,[^)]+)?\)"
        # r"anti-affinity\(([^,]+),([^,]+),([^,]+),([^,]+)"
        match = re.match(r"anti-affinity\(([^,]+),([^,]+),([^,]+),([^,]+)(?:,[^)]+)?\)", constraint, re.IGNORECASE)
        if match:
            c1, flav1, c2, flav2 = map(str.strip, match.groups())
            comp1 = f"{c1},{flav1}"
            comp2 = f"{c2},{flav2}"
            r1, r2 = groups.get(comp1,comp1), groups.get(comp2,comp2)
            if r1 == r2:
                group_conflicts[r1].add(constraint)
                for edge, aff_set in edges.items():
                    if comp1 in edge or comp2 in edge:
                        group_conflicts[r1].update(aff_set)
    for group_set in group_conflicts.values():
        conflicts.update(group_set)

    return conflicts

def merge_requirements(failures, energy, priority):
    failure_set = set(failures)
    energy_set = set(energy)
    all_constraints = failures + energy
    conflicts = find_conflicting_constraints(all_constraints)
    merged = []

    for constraint in all_constraints:
        if constraint not in conflicts:
            merged.append(constraint)
            continue
        
        in_failure = constraint in failure_set
        in_energy = constraint in energy_set

        if (priority == "failure" and in_failure) or (priority == "energy" and in_energy):
            merged.append(constraint)
        #else:
            #logger.info(f"Dropping constraint: {constraint} due to priority: {priority}")

    return list(set(merged))

def write_output(constraints, filename):
    with open(filename, 'w') as file:
        for constraint in constraints:
            file.write(f"{constraint}\n")

# Write constraints to a YAML file
def write_yaml_output(constraints, filename, failures, energy):
    yaml_output = {"requirements": {"components": {}}}

    for constraint in constraints:
        match = re.match(r"([\w-]+)\((.+)\)", constraint)
        if not match:
            continue
        constraint_type, args = match.groups()
        args = args.replace(" ", "").split(',')
        component = args[0]
        flavour = args[1]

        if component not in yaml_output["requirements"]["components"]:
            yaml_output["requirements"]["components"][component] = {}
        if flavour not in yaml_output["requirements"]["components"][component]:
            yaml_output["requirements"]["components"][component][flavour] = []

        if constraint_type == "avoid":
            node = args[2]
            constraint_data = {
                "resilience_oriented": any(component in f and flavour in f and node in f for f in failures),
                "energy_oriented": any(component in e and flavour in e and node in e for e in energy),
                "soft": True
            }
        elif constraint_type == "anti-affinity":
            componentValue = args[2]
            flavourValue = args[3]
            constraint_data = {
                "resilience_oriented": any(constraint_type in f and component in f and flavour in f and componentValue in f and flavourValue in f for f in failures),
                "energy_oriented": any(constraint_type in e and component in e and flavour in e and componentValue in e and flavourValue in e for e in energy),
                "soft": True
            }
        else:
            componentValue = args[2]
            flavourValue = args[3]
            constraint_data = {
                "resilience_oriented": any("anti-affinity" not in f and component in f and flavour in f and componentValue in f and flavourValue in f for f in failures),
                "energy_oriented": any("anti-affinity" not in e and component in e and flavour in e and componentValue in e and flavourValue in e for e in energy),
                "soft": True
            }

        if constraint_type == "affinity" or constraint_type == "anti-affinity":
            constraint_data["value"] = [args[2], args[3]]
        elif constraint_type == "avoid":
            constraint_data["value"] = args[2]
        else:
            continue
        
        new_constraint = {constraint_type: constraint_data}
        component_constraints = yaml_output["requirements"]["components"][component][flavour]

        if new_constraint not in component_constraints:
            component_constraints.append(new_constraint)

        #yaml_output["requirements"]["components"][component][flavour].append({
        #    constraint_type: constraint_data
        #})

    with open(filename, 'w') as file:
        yaml.dump(yaml_output, file)


def main(
    failures_path,
    energy_path,
    priority: str,
    output,
    log_location
):
    # Set up logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s -- %(message)s',
        handlers=[
            logging.FileHandler(Path(log_location) / "harmonizer.log", mode='a'),
        ],
    )
    logger = logging.getLogger(__name__)

    failures = get_constraints(failures_path, failure_format=True)
    energy = get_constraints(energy_path, failure_format=True)

    merged_constraints = merge_requirements(failures, energy, priority)

    # Create output paths
    output_pl_path = f"{output}.pl"
    output_yaml_path = f"{output}.yaml"

    write_output(merged_constraints, output_pl_path)
    write_yaml_output(merged_constraints, output_yaml_path, failures, energy)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--failures", required=True, help="Path to failures constraints file")
    parser.add_argument("-e", "--energy", required=True, help="Path to energy constraints file")
    parser.add_argument("-p", "--priority", choices=["failure", "energy"], help="Priority in case of conflict")
    parser.add_argument("-o", "--output", required=True, help="Path for output files")
    parser.add_argument("-l", "--log", default=".", help="Path (folder) for log file")

    args = parser.parse_args()
    main(args.failures, args.energy, args.priority, args.output, args.log)