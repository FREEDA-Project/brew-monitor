from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
)
from eclypse.graph.assets import Symbolic, Additive
from eclypse.graph import NodeGroup
from eclypse.report.metrics import metric, defaults
from eclypse_core.placement import Placement, PlacementView
from eclypse.graph import Infrastructure

if TYPE_CHECKING:
    from eclypse_core.placement import Placement, PlacementView
    from eclypse.graph import Infrastructure

def subnet(
    lower_bound: list = [],
    upper_bound: list = ["public","private"]
) -> Symbolic:
    default_init_spaces = {
        NodeGroup.CLOUD: lambda: ["private"],
        NodeGroup.FAR_EDGE: lambda: ["private"],
        NodeGroup.NEAR_EDGE: lambda: ["private"],
        NodeGroup.IOT: lambda: ["private"],
    }
    return Symbolic(lower_bound, upper_bound, default_init_spaces)

def security(
    lower_bound: list = [],
    upper_bound: list = ["ssl","firewall","encrypted_storage"]
) -> Symbolic:
    default_init_spaces = {
        NodeGroup.CLOUD: lambda: [],
        NodeGroup.FAR_EDGE: lambda: [],
        NodeGroup.NEAR_EDGE: lambda: [],
        NodeGroup.IOT: lambda: [],
    }
    return Symbolic(lower_bound, upper_bound, default_init_spaces)

def energy(
    lower_bound: float = 0.0,
    upper_bound: float = float("inf")
) -> Additive:
    default_init_spaces = {
        NodeGroup.CLOUD: lambda: 0.0,
        NodeGroup.FAR_EDGE: lambda: 0.0,
        NodeGroup.NEAR_EDGE: lambda: 0.0,
        NodeGroup.IOT: lambda: 0.0,
    }
    return Additive(lower_bound, upper_bound, default_init_spaces, functional=False)

@metric.service(aggregate_fn="mean", report=["csv"], name="service_energy")
def featured_service_energy(
    _: str,
    requirements: Dict[str, Any],
    __: Dict[str, Placement],
    ___: Infrastructure,
) -> float:
    return requirements.get("energy", 0)

@metric.service(aggregate_fn="mean", report=["csv"], name="service_emissions")
def featured_service_emissions(
    service_id: str,
    requirements: Dict[str, Any],
    placement: Placement,
    infr: Infrastructure,
) -> float:
    try:
        return requirements.get("energy", 0) * float(infr.nodes[placement.service_placement(service_id)]["carbon"])
    except KeyError:
        return -1

@metric.interaction(aggregate_fn="mean", report=["csv"], name="interaction_energy")
def featured_interaction_energy(
    _: str,
    __: str,
    requirements: Dict[str, Any],
    ___: Dict[str, Placement],
    ____: Infrastructure,
) -> float:
    return requirements.get("energy", 0)

@metric.interaction(aggregate_fn="mean", report=["csv"], name="interaction_emissions")
def featured_interaction_emissions(
    source_id: str,
    dest_id: str,
    requirements: Dict[str, Any],
    placement: Placement,
    infr: Infrastructure,
) -> float:
    try:
        return requirements.get("energy", 0) * (float(infr.nodes[placement.service_placement(source_id)]["carbon"]) + float(infr.nodes[placement.service_placement(dest_id)]["carbon"])) / 2
    except KeyError:
        return -1

@metric.node(aggregate_fn="mean", report=["csv"])
def featured_carbon(
    _: str,
    resources: Dict[str, Any],
    __: Dict[str, Placement],
    ___: Infrastructure,
    ____: PlacementView,
) -> float:
    return resources.get("carbon", 0)

def get_metrics():
    return [
        featured_service_energy,
        featured_service_emissions,
        featured_interaction_energy,
        featured_interaction_emissions,
        featured_carbon
    ]