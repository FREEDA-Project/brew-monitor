import subprocess, shutil
from pathlib import Path
from pyswip import Prolog

##### This is super ugly, but it reserchers code :) ######
import os, sys
main_scripts_folder = Path(os.path.abspath(os.path.dirname(__file__))).parent
sys.path.append(main_scripts_folder)
from failureEnhancer.eclypseParser import generate_prolog_rules
from harmonizer.harmonizer import main as harmonizer
##########################################################

def run_energy_enhancer(
    energy_enhancer_location: Path,
    location_simulation: Path,
    old_deployment_location: Path,
    components_yaml_file: Path,
    infrastructure_yaml_file: Path,
    output_path: Path,
    kb_file_path: Path
):
    kb_name = "knowledgeBase.json"

    pl_constraint_file = output_path / "energyConstraints.pl"
    yaml_constraint_file = output_path / "EnergyEnhancerConstraints.yaml"
    changelog = output_path / "changelog.txt"
    if kb_file_path is None:
        new_kb_file_path = output_path / kb_name
        with open(new_kb_file_path, "w") as f:
            f.write("{}")
    else:
        new_kb_file_path = output_path / kb_name
        shutil.copy(kb_file_path, new_kb_file_path)

    try:
        subprocess.run([
            energy_enhancer_location / ".venv" / "bin" / "python",
            energy_enhancer_location / "main.py",
            energy_enhancer_location / "rules.pl",
            location_simulation / "stats" / "interaction.csv", # istio
            location_simulation / "stats" / "service.csv", # service
            location_simulation / "stats" / "node.csv",
            old_deployment_location,
            components_yaml_file,
            infrastructure_yaml_file,
            new_kb_file_path,
            output_path / "explanation.txt",
            output_path / "facts.pl",
            pl_constraint_file,
            yaml_constraint_file,
            changelog
        ], check=True)
    except Exception as e:
        print(e)
        exit()

    return pl_constraint_file, changelog, new_kb_file_path

def run_failure_enhancer(
    location_failure_enhancer: Path,
    location_simulation: Path,
):
    failureEnhancer_scripts_folder = main_scripts_folder / "failureEnhancer"

    log_file = location_simulation / "simulation.log"
    parsed_deployment_file = location_failure_enhancer / "deployment"
    pl_parsed_deployment = str(parsed_deployment_file) + ".pl"
    pl_rules = failureEnhancer_scripts_folder / "failureEnhancer.pl"
    placeholder = failureEnhancer_scripts_folder / "placeholder.pl"
    pl_generated_output = location_failure_enhancer / "output.pl"

    open(pl_generated_output, "w").close()

    generate_prolog_rules(log_file, parsed_deployment_file)

    p = Prolog()
    p.consult(placeholder)
    p.consult(pl_rules)
    p.consult(pl_parsed_deployment)
    # For some reason, to make it work, you have to consume this iterator,
    # here's why the list
    list(p.query(f"failuresConstraints('{pl_generated_output}')"))
    # For some reason, the library keeps an internal state that we have to clean
    p.retractall("deployedTo(_, _, _)")
    p.retractall("unreachable(_, _)")
    p.retractall("overload(_, _, _, _)")
    p.retractall("timeoutEvent(_, _, _)")
    p.retractall("internal(_, _)")
    p.retractall("highUsage(_, _, _, _, _)")
    p.retractall("disconnection(_, _, _)")
    p.retractall("congestion(_, _, _, _)")
    p.retractall("resourceIntensive(_, _, _, _, _)")

    return pl_generated_output

def run_harmonizer(
    failure_constraints_pl,
    energy_constraints_pl,
    priority,
    output_file_name,
    log_location
):
    harmonizer(
        failure_constraints_pl,
        energy_constraints_pl,
        priority,
        output_file_name,
        log_location
    )
    return Path(str(output_file_name) + ".yaml")
