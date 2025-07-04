import yaml
from eclypse.placement.strategies import StaticStrategy, BestFitStrategy, FirstFitStrategy, RandomStrategy
from eclypse.simulation import Simulation, SimulationConfig
from eclypse.graph import Infrastructure, Application, NodeGroup
from eclypse.graph.assets.defaults import cpu, ram, storage, availability, latency
from eclypse.utils import MAX_LATENCY

from utils import combine_comp_flav

##### This is super ugly, but it reserchers code :) ######
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from assets.freeda_assets import subnet, security, energy, get_metrics
from update_policy import scenarioDEMOapplication, scenarioDEMOinfrastructure, noscenario
##########################################################

SEED = 42

def parse_deployment(data):
    # Parse deployment text
    result = {}
    for l in data.split("\n")[:-3]:
        if l.startswith("Component") and not l.endswith("not deployed."):
            words = l.split(" ")
            component = words[1]
            flavour = words[5]
            node = words[8][:-1]

            result.update({(component, flavour) : node})

    return result

def get_app(
    data,
    deployment: dict[tuple[str, str] : str],
    node_assets = {
        "cpu" : cpu(),
        "ram" : ram(),
        "storage" : storage(),
        "availability" : availability(),
        "subnet" : subnet(),
        "security" : security(),
        "energy" : energy()
    },
    edge_assets = {
        "latency" : latency(),
        "energy" : energy()
    },
    node_update_policy_fn=noscenario
):
    # Initialize app object
    app = Application(
        data["name"],
        node_update_policy=node_update_policy_fn(),
        include_default_assets=False,
        node_assets=node_assets,
        edge_assets=edge_assets
    )

    # Create app nodes and their requirements
    for c, f in deployment.keys():
        common_requirements = data["requirements"]["components"][c]["common"]
        flavour_requirements = data["requirements"]["components"][c]["flavour-specific"][f]
        requirements = common_requirements | flavour_requirements | {"energy" : data["components"][c]["flavours"][f]["energy"]}

        if "storage" not in requirements:
            requirements["storage"] = 0

        app.add_node_by_group(
            NodeGroup.CLOUD,
            combine_comp_flav(c, f),
            processing_time=0,
            **requirements
        )

    # Create connections between components
    for c1, f1 in deployment.keys():
        for c2, f2 in deployment.keys():
            if (
                c1 in data["requirements"]["dependencies"]
                and f1 in data["requirements"]["dependencies"][c1]
                and c2 in data["requirements"]["dependencies"][c1][f1]
            ):
                depencency_resource = data["requirements"]["dependencies"][c1][f1][c2]["requirements"].copy()
                depencency_resource.pop("availability")
                depencency_resource["energy"] = data["requirements"]["dependencies"][c1][f1][c2]["energy"]

                app.add_edge(
                    combine_comp_flav(c1, f1),
                    combine_comp_flav(c2, f2),
                    **depencency_resource
                )

    return app

def get_infrastructure(
    data,
    seed: int,
    solver: bool,
    node_update_policy_fn = noscenario,
    node_assets = {
        "cpu" : cpu(),
        "ram" : ram(),
        "storage" : storage(),
        "availability" : availability(),
        "subnet" : subnet(),
        "security" : security(),
        "energy" : energy()
    },
    edge_assets = {
        "latency" : latency(),
        "energy" : energy()
    }
):
    # Due a ECLYPSE bug, we have to add these lines ---
    if solver:
        from eclypse.graph.assets import Additive
        def gpu(
            lower_bound: int = 0,
            upper_bound: int = 1
        ) -> Additive:
            default_init_spaces = {
                NodeGroup.CLOUD: lambda: 0,
                NodeGroup.FAR_EDGE: lambda: 0,
                NodeGroup.NEAR_EDGE: lambda: 0,
                NodeGroup.IOT: lambda: 0,
            }
            return Additive(lower_bound, upper_bound, default_init_spaces, functional=False)
        if "gpu" not in node_assets:
            node_assets = node_assets | {"gpu" : gpu()}
    # ---

    # Instantiate the infrastruture
    infra = Infrastructure(
        data["name"],
        node_update_policy=node_update_policy_fn(),
        seed=seed,
        include_default_assets=False,
        node_assets=node_assets,
        edge_assets=edge_assets,
        path_assets_aggregators={
            "latency": lambda x: sum(list(x)) if x else MAX_LATENCY,
            "energy": lambda _ : 0.0
        },
    )

    # For each node in the YAML create a node in the simulator
    for node_name, node_data in data["nodes"].items():
        capabilities = node_data["capabilities"]
        carb_cost = node_data["profile"]
        feature = capabilities | carb_cost
        if not solver and "gpu" not in feature:
            feature = feature | {"gpu" : 0}

        infra.add_node_by_group(
            NodeGroup.CLOUD,
            node_name,
            processing_time=0,
            **feature
        )

    # Create links
    for link in data["links"]:
        ls = link["connected_nodes"][0]
        ld = link["connected_nodes"][1]
        lcap = link["capabilities"]
        infra.add_symmetric_edge(ls, ld, bandwidth = float("inf"), **lcap)

    return infra

def parse(
    components_yaml_path: str,
    infrastructure_yaml_path: str,
    deployment_txt_path: str,
    solver: bool,
    seed: int = SEED,
    path: str = "cs-simulation",
    update_policy_application=noscenario,
    update_policy_infrastructure=noscenario,
):
    # Parse the infrastructure to get the object
    with open(infrastructure_yaml_path, "r") as yaml_file:
        infrastructure_data = yaml.safe_load(yaml_file)
    infrastructure = get_infrastructure(
        infrastructure_data,
        SEED,
        solver,
        node_update_policy_fn=update_policy_infrastructure
    )

    # Parse the components to get an app
    with open(components_yaml_path, "r") as yaml_file:
        components_data = yaml.safe_load(yaml_file)

    if solver:
        # Parse the depoyment if parser and solver was invoked
        with open(deployment_txt_path, "r") as f:
            deployment_data = f.read()
        deployment = parse_deployment(deployment_data)
        deployment_simulation = {
            combine_comp_flav(c, f): n
            for (c, f), n in deployment.items()
        }
    else:
        # When not using the parser, nodes of the deployment are None (since it
        # will be Eclypse that chooses values) and we will deploy all components
        # with their most important flavour
        deployment = {
            (c, components_data["components"][c]["importance_order"][-1]) : None
            for c in components_data["components"].keys()
        }

    app = get_app(
        components_data,
        deployment,
        node_update_policy_fn=update_policy_application
    )

    sim = Simulation(
        infrastructure,
        simulation_config=SimulationConfig(
            seed=seed,
            tick_every_ms=10,
            max_ticks=144,
            path=path,
            log_to_file=True,
            callbacks=get_metrics()
        ),
    )
    sim.register(
        app,
        StaticStrategy(deployment_simulation) if solver else BestFitStrategy()
    )

    return sim

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="FREEDA YAML parser to ECLYPSE configuration")
    parser.add_argument("components", type=str, help="Components YAML file path")
    parser.add_argument("infrastructure", type=str, help="Infrastructure YAML file path")
    parser.add_argument("deployment", type=str, help="Deployment txt file path")
    args = parser.parse_args()

    sim = parse(args.components, args.infrastructure, args.deployment)
    sim.start()
    sim.wait()
