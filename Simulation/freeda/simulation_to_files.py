import yaml
import networkx as nx

from eclypse.simulation import Simulation

def parse_components(data, changelog):
    for r in changelog:
        if r.startswith("service"):
            _, c, f, v = r.split(" ")
            data["components"][c]["flavours"][f]["energy"] = int(v)
        elif r.startswith("link"):
            _, c1, f, c2, v = r.split(" ")
            data["requirements"]["dependencies"][c1][f][c2]["energy"] = int(v)

    return data

def parse_infrastructure(data, infrastructure, changelog):
    # Do we still have each node? Remove nodes removed and the ones with
    # availability set to zero
    removed_nodes = set(data["nodes"]) - set(infrastructure.nodes)
    for n in removed_nodes:
        data["nodes"].pop(n)
    for n in infrastructure.nodes:
        if infrastructure.nodes[n]["availability"] == 0:
            data["nodes"].pop(n)
            removed_nodes.add(n)

    # Does each node have the same amount of resources?
    for n in data["nodes"]:
        for cap_name in data["nodes"][n]["capabilities"]:
            x = infrastructure.nodes[n][cap_name]
            if isinstance(x, float):
                x = round(infrastructure.nodes[n][cap_name])
            data["nodes"][n]["capabilities"][cap_name] = x

        for profile_name in data["nodes"][n]["profile"]:
            x = infrastructure.nodes[n][profile_name]
            if isinstance(x, float):
                x = round(infrastructure.nodes[n][profile_name])
            data["nodes"][n]["profile"][profile_name] = x

    # Do we still have each link? Remove links removed, the ones that do not
    # have both nodes and the ones with availability set to zero
    removed_links = set(
        (l["connected_nodes"][0], l["connected_nodes"][1])
        for l in data["links"]
    ) - set(infrastructure.edges)
    for rl in removed_links:
        for l in data["links"].copy():
            if (
                (
                    l["connected_nodes"][0] == rl[0]
                    and l["connected_nodes"][1] == rl[1]
                ) or (
                    l["connected_nodes"][0] in removed_nodes
                    or l["connected_nodes"][1] in removed_nodes
                )
            ):
                data["links"].remove(l)
    for s, t in infrastructure.edges:
        if infrastructure.edges[s, t]["availability"] == 0:
            for l in data["links"].copy():
                if l["connected_nodes"][0] == s and l["connected_nodes"][1] == t:
                    data["links"].remove(l)

    # Change carbon usage as in changelog
    for node in changelog:
        _, n, v = node.split(" ")
        data["nodes"][n]["profile"]["carbon"] = v

    return data

def parse(
    components_yaml_path: str,
    infrastructure_yaml_path: str,
    simulation: Simulation,
    components_yaml_new_location: str,
    infrastructure_yaml_new_location: str,
    energy_changelog: str
):
    # Parse energy changelog
    with open(energy_changelog, "r") as f:
        energy_changes = [l for l in f.readlines()]

    # Parse the old components YAML and update in-place the values
    with open(components_yaml_path, "r") as yaml_file:
        components_data = yaml.safe_load(yaml_file)
    updated_app_yaml = parse_components(
        components_data,
        [l for l in energy_changes if not l.startswith("node")]
    )

    # Create the new component file
    with open(components_yaml_new_location, "w") as f:
        yaml.dump(updated_app_yaml, f)

    # Parse the old infrastructure YAML and update in-place the values
    with open(infrastructure_yaml_path, "r") as yaml_file:
        infrastructure_data = yaml.safe_load(yaml_file)
    infrastructure = simulation.infrastructure
    updated_infrastructure_yaml = parse_infrastructure(
        infrastructure_data,
        infrastructure,
        [l for l in energy_changes if l.startswith("node")]
    )

    # Create the new infrastructure file
    with open(infrastructure_yaml_new_location, "w") as f:
        yaml.dump(updated_infrastructure_yaml, f)

def generate_solver_files(
    simulation_folder,
    lsco_t,
    components_yaml_path,
    infrastructure_yaml_path,
    sim
):
    # Get the deployment after the simulation run
    simulation_file = simulation_folder / "simulation.log"
    with open(simulation_file, "r") as f:
        for l in f:
            if "PlacementManager - {" in l:
                break

    eclypse_deployed_names = {}
    for e in l.split(" - ")[-1].strip()[1:-1].split(" | "):
        c, n = e.split(" -> ")
        eclypse_deployed_names[c.strip()] = n.strip()

    # Get the original component name and flavour
    with open(components_yaml_path, "r") as yaml_file:
        components_data = yaml.safe_load(yaml_file)
    with open(infrastructure_yaml_path, "r") as yaml_file:
        infrastructure_data = yaml.safe_load(yaml_file)
    deployed = {}
    for c in components_data["components"].keys():
        for e_c in eclypse_deployed_names.keys():
            if c in e_c:
                for f in components_data["components"][c]["flavours"].keys():
                    if f in e_c[len(c):]:
                        deployed[(c, f)] = eclypse_deployed_names[e_c]

    # Write the deployment file and get the total cost
    deployment_location = lsco_t / "deployment.txt"
    with open(deployment_location, "w") as file:
        total_cost = 0
        total_carb = 0
        # Create the first part of the deployment ...
        for (c, f), n in sorted(deployed.items()):
            file.write(f"Component {c} deployed in flavour {f} on node {n}.\n")

            # ... while computing cost ...
            profile_cost = infrastructure_data["nodes"][n]["profile"]["cost"]

            if f not in components_data["requirements"]["components"][c]["flavour-specific"]:
                cost = components_data["requirements"]["components"][c]["common"]
            else:
                cost = components_data["requirements"]["components"][c]["flavour-specific"][f]

            if isinstance(profile_cost, int):
                total_cost += cost["cpu"] * profile_cost
            else:
                total_cost += sum(
                    cost["cpu"] * profile_cost[k]
                    for k in profile_cost.keys()
                )

            # ... and carb ...
            energy_c = components_data["components"][c]["flavours"][f]["energy"]
            carb_n = infrastructure_data["nodes"][n]["profile"]["carbon"]
            total_carb_connections = 0
            for (c2, _), n2 in sorted(deployed.items()):
                if any(c2 in u["component"] for u in components_data["components"][c]["flavours"][f]["uses"]):
                    nodes = nx.shortest_path(sim.infrastructure, source=n, target=n2)
                    carbs = sum(int(infrastructure_data["nodes"][nd]["profile"]["carbon"]) for nd in nodes)
                    energy_dep = components_data["requirements"]["dependencies"][c][f][c2]["energy"]
                    total_carb_connections += energy_dep + round(carbs / len(nodes))
            total_carb += int(energy_c) * int(carb_n) + total_carb_connections

        # ... then write the last part of the file.
        file.write(f"Objective value: {len(deployed)}\n")
        file.write(f"\tApp quality: {len(deployed)}\n")
        file.write(f"\tTotal cost: {total_cost}\n")
        file.write(f"\tTotal carb: {total_carb}\n")

    # Create importance file
    importances = {}
    for c, f in deployed.keys():
        importances[c] = {}
        importances[c][f] = 1
    with open(lsco_t / "importances.yaml", "w") as f:
        yaml.safe_dump(importances, f)

    return lsco_t / "deployment.txt"