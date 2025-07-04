#!/usr/bin/env python
import argparse, os, shutil
from pathlib import Path

from files_to_simulation import parse as files_to_simulation
from simulation_to_files import parse as simulation_to_files, generate_solver_files
from model import parse_and_run, try_until_sucess
from analyzers import run_energy_enhancer, run_failure_enhancer, run_harmonizer

##### This is super ugly, but it reserchers code :) ######
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from update_policy import (scenarioDEMOinfrastructure, 
                           scenarioDEMOapplication, 
                           scenarioDEMOapplication2, 
                           scenario3,
                           energyapp1, energyapp2, energyapp3,
                           energyinfr1, energyinfr2, energyinfr3, ebestfit)
##########################################################

def check_stop(old_deployment: Path) -> bool:
    if old_deployment is None:
        return False

def main(
    location,
    parser_location,
    energyEnhancer,
    failure_enhancer,
    components,
    infrastructure,
    priority,
    additional_resources,
    application_update_policy,
    infrastructure_update_policy
):
    deployment_location = None
    constraints_location = None

    location_solver_component_output = location / "solver"
    location_simulation_output = location / "simulations"
    location_FailureEnhancer = location / "FailureEnhancer"
    location_EnergyEnhancer = location / "EnergyEnhancer"
    location_Harmonizer = location / "Harmonizer"
    kb_file_path = None

    components_yaml_file = components
    infrastructure_yaml_file = infrastructure

    for t in range(min(len(application_update_policy), len(infrastructure_update_policy))):
        if check_stop(deployment_location):
            break

        # Declare some paths
        lsco_t = location_solver_component_output / str(t)
        location_simulation_t = location_simulation_output / str(t)
        lee_t = location_EnergyEnhancer / str(t)
        lfe_t = location_FailureEnhancer / str(t)
        lh_t = location_Harmonizer / str(t)

        os.makedirs(lsco_t, exist_ok=True)
        os.makedirs(lee_t, exist_ok=True)
        os.makedirs(lfe_t, exist_ok=True)
        os.makedirs(lh_t, exist_ok=True)

        if parser_location is not None:
            if constraints_location is not None:
                # Try to run the model until you get a feasible deployment or the
                # current constraints does not provide any
                deployment_location = try_until_sucess(
                    parser_location,
                    lsco_t,
                    components_yaml_file,
                    infrastructure_yaml_file,
                    additional_resources,
                    constraints_location,
                    lsco_t,
                    deployment_location
                )
            else:
                # Step 1 (run the parser) and Step 2 (run the model)
                deployment_location = parse_and_run(
                    parser_location,
                    lsco_t,
                    components_yaml_file,
                    infrastructure_yaml_file,
                    additional_resources,
                    deployment_location,
                    constraints_location
                )

            if os.path.exists(location_simulation_t):
                shutil.rmtree(location_simulation_t)

        # Step 3: convert deployment and YAMLs to an ECLYPSE simulation
        sim = files_to_simulation(
            components_yaml_file,
            infrastructure_yaml_file,
            deployment_location,
            solver=True if parser_location is not None else False,
            path=location_simulation_t,
            update_policy_infrastructure=infrastructure_update_policy[t],
            update_policy_application=application_update_policy[t]
        )

        # Step 4: run the simulation until it stops
        sim.start()
        sim.wait()

        # Create and retrieve files if the parser was not called
        if parser_location is None:
            deployment_location = generate_solver_files(
                location_simulation_t,
                lsco_t,
                components_yaml_file,
                infrastructure_yaml_file,
                sim
            )

        # Step 5: call the analyzers
        if energyEnhancer is not None:
            energy_constraint_file, energy_changelog, kb_file_path = run_energy_enhancer(
                energyEnhancer,
                location_simulation_t,
                deployment_location,
                components_yaml_file,
                infrastructure_yaml_file,
                lee_t,
                kb_file_path
            )
        else:
            # If the energy enhancer won't run, create everything that the loop
            # needs to continue
            energy_changelog = lee_t / "changelog.txt"
            energy_constraint_file = lee_t / "energyConstraints.pl"
            open(energy_changelog, "w").close()
            open(energy_constraint_file, "w").close()

        if failure_enhancer:
            failure_constraint_file = run_failure_enhancer(
                lfe_t,
                location_simulation_t
            )
        else:
            failure_constraint_file = lfe_t / "output.pl"
            open(failure_constraint_file, "w").close()

        # Step 6: call the harmonizer on the result of the analyzers
        if energyEnhancer is not None or failure_enhancer:
            constraints_location = run_harmonizer(
                failure_constraint_file,
                energy_constraint_file,
                priority,
                lh_t / "constraints",
                lh_t
            )

        # Step 7: generate YAMLs from ECLYPSE simulation
        new_components_yaml_file = lsco_t / f"components.yaml"
        new_infrastructure_yaml_file = lsco_t / f"infrastructure.yaml"
        simulation_to_files(
            components_yaml_file,
            infrastructure_yaml_file,
            sim,
            new_components_yaml_file,
            new_infrastructure_yaml_file,
            energy_changelog
        )
        components_yaml_file = new_components_yaml_file
        infrastructure_yaml_file = new_infrastructure_yaml_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FREEDA main loop over ECLYPSE simulator")
    parser.add_argument("components", type=str, help="Starting components YAML file")
    parser.add_argument("infrastructure", type=str, help="Starting infrastructure YAML file")
    parser.add_argument(
        "-p",
        "--parser",
        metavar="parser",
        type=Path,
        help="Parser's folder location",
        default=None
    )
    parser.add_argument(
        "--failure-enhancer",
        "-f",
        metavar="failureEnhancer",
        help="Run the FailureEnhancer?",
        action=argparse.BooleanOptionalAction
    )
    parser.add_argument(
        "--energy-enhancer",
        "-e",
        metavar="energyEnhancer",
        type=Path,
        help="EnergyEnhancer's folder location",
        default=None
    )
    parser.add_argument(
        "--additional-resources",
        "-r",
        metavar="resources",
        type=str,
        help="Resources YAML file path"
    )
    parser.add_argument(
        "--location",
        "-l",
        metavar="location",
        type=Path,
        help="Location where to store files",
        default="./FREEDA-ECLYPSE-loop"
    )
    args = parser.parse_args()


    location = args.location.resolve()
    if not location.exists():
        os.makedirs(location, exist_ok=True)

    if args.energy_enhancer is not None:
        energyEnhancer = args.energy_enhancer.resolve()
    else:
        energyEnhancer = None

    if args.parser is not None:
        parser_location = args.parser.resolve()
    else:
        parser_location = None

    main(
        location,
        parser_location,
        energyEnhancer,
        args.failure_enhancer,
        args.components,
        args.infrastructure,
        "failure",
        args.additional_resources,
        [energyapp1, energyapp2, energyapp3],
        [energyinfr1, energyinfr2, energyinfr3]
    )