from update_policy import (
    scenarioDEMOinfrastructure
)
from eclypse.graph import Infrastructure, NodeGroup
from eclypse.graph.assets.defaults import cpu, ram, storage, availability, latency
from assets.freeda_assets import subnet, security, energy
from eclypse.utils import MAX_LATENCY

aggregators = {
    "latency": lambda x: sum(list(x)) if x else MAX_LATENCY,
    "energy": lambda x: 0.0
}

# Creating an instance of the Infrastructure class
def get_infrastructure(seed: int = 10) -> Infrastructure:
    infra = Infrastructure(
        "Infrastructure",
        node_update_policy=scenarioDEMOinfrastructure(),
        seed=seed,
        include_default_assets=False,
        node_assets={
            "cpu":cpu(),
            "ram":ram(),
            "storage":storage(),
            "availability":availability(),
            "subnet":subnet(),
            "security":security(),
            "energy":energy()
        },
        edge_assets={
            "latency":latency(),
            "energy":energy()
        },
        path_assets_aggregators=aggregators,
    )

    infra.add_node_by_group(
        NodeGroup.CLOUD,
        "public1",
        cpu=8,
        ram=16,
        storage=1024,
        availability=0.99,
        subnet=["public"],
        security=["ssl", "firewall"],
        cost=9,
        carbon=402,
        processing_time=0
    )

    infra.add_node_by_group(
        NodeGroup.CLOUD,
        "public2",
        cpu=2,
        ram=4,
        storage=250,
        availability=0.99,
        subnet=["public"],
        security=["ssl", "firewall"],
        cost=9,
        carbon=255,
        processing_time=0
    )

    infra.add_node_by_group(
        NodeGroup.CLOUD,
        "private1",
        cpu=3,
        ram=16,
        storage=512,
        availability=0.99,
        subnet=["private"],
        security=["ssl","firewall","encrypted_storage"],
        cost=7,
        carbon=346,
        processing_time=0
    )

    infra.add_node_by_group(
        NodeGroup.CLOUD,
        "private2",
        cpu=2,
        ram=4,
        storage=50,
        availability=0.99,
        subnet=["private"],
        security=["ssl","firewall"],
        cost=7,
        carbon=74,
        processing_time=0
    )

    infra.add_node_by_group(
        NodeGroup.CLOUD,
        "private3",
        cpu=2,
        ram=8,
        storage=250,
        availability=0.99,
        subnet=["private"],
        security=["ssl","firewall"],
        cost=7,
        carbon=620,
        processing_time=0
    )

    infra.add_node_by_group(
        NodeGroup.CLOUD,
        "private4",
        cpu=2,
        ram=4,
        storage=50,
        availability=0.99,
        subnet=["private"],
        security=["ssl","firewall"],
        cost=7,
        carbon=155,
        processing_time=0
    )

    infra.add_node_by_group(
        NodeGroup.CLOUD,
        "private5",
        cpu=4,
        ram=8,
        storage=600,
        availability=0.99,
        subnet=["private"],
        security=["ssl","firewall","encrypted_storage"],
        cost=7,
        carbon=290,
        processing_time=0
    )

    infra.add_symmetric_edge(
        "public1", "public2", latency=10, availability=0.99, bandwidth = float("inf")
    )
    infra.add_symmetric_edge(
        "private1", "private2", latency=10, availability=0.99, bandwidth = float("inf")
    )
    infra.add_symmetric_edge(
        "private1", "private3", latency=10, availability=0.99, bandwidth = float("inf")
    )
    infra.add_symmetric_edge(
        "private1", "private4", latency=10, availability=0.99, bandwidth = float("inf")
    )
    infra.add_symmetric_edge(
        "private1", "private5", latency=10, availability=0.99, bandwidth = float("inf")
    )
    infra.add_symmetric_edge(
        "private2", "private3", latency=10, availability=0.99, bandwidth = float("inf")
    )
    infra.add_symmetric_edge(
        "private2", "private4", latency=10, availability=0.99, bandwidth = float("inf")
    )
    infra.add_symmetric_edge(
        "private2", "private5", latency=10, availability=0.99, bandwidth = float("inf")
    )
    infra.add_symmetric_edge(
        "private3", "private4", latency=10, availability=0.99, bandwidth = float("inf")
    )
    infra.add_symmetric_edge(
        "private3", "private5", latency=10, availability=0.99, bandwidth = float("inf")
    )
    infra.add_symmetric_edge(
        "private4", "private5", latency=10, availability=0.99, bandwidth = float("inf")
    )
    infra.add_symmetric_edge(
        "public1", "private1", latency=10, availability=0.99, bandwidth = float("inf")
    )
    infra.add_symmetric_edge(
        "public1", "private3", latency=10, availability=0.99, bandwidth = float("inf")
    )
    infra.add_symmetric_edge(
        "public2", "private1", latency=10, availability=0.99, bandwidth = float("inf")
    )
    infra.add_symmetric_edge(
        "public2", "private3", latency=10, availability=0.99, bandwidth = float("inf")
    )

    return infra