from update_policy import (
    scenarioDEMOapplication
)
from eclypse.graph import Application, NodeGroup
from eclypse.graph.assets.defaults import cpu, ram, storage, availability, latency
from assets.freeda_assets import subnet, security, energy

# Instance of the app
app = Application(
    "Application",
    node_update_policy=scenarioDEMOapplication(),
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
    }
)

app.add_node_by_group(
    NodeGroup.CLOUD,
    "load_balancer_large",
    cpu=2,
    ram=4,
    availability=0.99,
    storage=10,
    subnet=["public"],
    security=["firewall"],
    energy=747/6
)

app.add_node_by_group(
    NodeGroup.CLOUD,
    "frontend_large",
    cpu=2,
    ram=4,
    availability=0.99,
    storage=20,
    subnet=["public"],
    security=["firewall", "ssl"],
    energy=594/6
)

app.add_node_by_group(
    NodeGroup.CLOUD,
    "api_large",
    cpu=2,
    ram=6,
    availability=0.99,
    storage=15,
    subnet=["private"],
    security=["ssl"],
    energy=853/6
)

app.add_node_by_group(
    NodeGroup.CLOUD,
    "identity_provider_large",
    cpu=1,
    ram=4,
    availability=0.99,
    storage=10,
    subnet=["private"],
    security=["ssl"],
    energy=884/6
)

app.add_node_by_group(
    NodeGroup.CLOUD,
    "database_large",
    cpu=2,
    ram=4,
    availability=0.99,
    storage=512,
    subnet=["private"],
    security=["encrypted_storage"],
    energy=1361/6
)

app.add_node_by_group(
    NodeGroup.CLOUD,
    "redis_large",
    cpu=1,
    ram=4,
    availability=0.99,
    storage=10,
    subnet=["private"],
    security=["ssl"],
    energy=88/6
)

app.add_node_by_group(
    NodeGroup.CLOUD,
    "etcd_large",
    cpu=1,
    ram=4,
    availability=0.99,
    storage=10,
    subnet=["private"],
    security=["ssl"],
    energy=45/6
)

app.add_edge(
    "load_balancer_large",
    "frontend_large",
    latency=25,
    energy=5/6
)
app.add_edge(
    "frontend_large",
    "api_large",
    latency=25,
    energy=5/6
)
app.add_edge(
    "frontend_large",
    "redis_large",
    latency=25,
    energy=3/6
)
app.add_edge(
    "api_large",
    "identity_provider_large",
    latency=20,
    energy=3/6
)
app.add_edge(
    "api_large",
    "etcd_large",
    latency=20,
    energy=4/6
)
app.add_edge(
    "api_large",
    "database_large",
    latency=20,
    energy=11/6
)
app.add_edge(
    "api_large",
    "redis_large",
    latency=20,
    energy=1/6
)
app.add_edge(
    "identity_provider_large",
    "etcd_large",
    latency=20,
    energy=1/6
)