from eclypse.simulation import Simulation, SimulationConfig
from eclypse.placement.strategies import StaticStrategy, RandomStrategy, BestFitStrategy, FirstFitStrategy
from application import app as app
from infrastructure import get_infrastructure
from assets.freeda_assets import get_metrics

if __name__ == "__main__":
    seed =  10
    sim_config = SimulationConfig(
        seed=seed,
        tick_every_ms=10,
        max_ticks=144, # we can consider 1 tick = 10 minutes
        path="simulation-scenario-demo", # Folder name for the output
        callbacks=get_metrics()
    )

    sim = Simulation(
        get_infrastructure(seed=seed),
        simulation_config=sim_config,
    )

    initial_deployment = StaticStrategy({
        "load_balancer_large": "public1",
        "api_large": "private1",
        "frontend_large": "public1",
        "identity_provider_large": "private3",
        "redis_large": "private3",
        "database_large": "private5",
        "etcd_large": "private2",
    })

    scenario1_deployment = StaticStrategy({
        "load_balancer_large": "public1",
        "api_large": "private1",
        "frontend_large": "public1",
        "identity_provider_large": "private1",
        "redis_large": "private3",
        "database_large": "private5",
        "etcd_large": "private3",
    })

    scenario2_deployment = StaticStrategy({
        "load_balancer_large": "public1",
        "api_large": "private1",
        "frontend_large": "public1",
        "identity_provider_large": "private3",
        "redis_large": "private3",
        "database_large": "private5",
        "etcd_large": "private2",
    })

    scenario3_deployment = StaticStrategy({
        "load_balancer_large": "public1",
        "api_large": "private1",
        "frontend_large": "public1",
        "identity_provider_large": "private2",
        "redis_large": "private1",
        "database_large": "private5",
        "etcd_large": "private4",
    })

    sim.register(app,scenario3_deployment)
    sim.start()
    sim.wait()
