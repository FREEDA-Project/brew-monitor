import json, subprocess, glob, os, itertools, copy, math
from pathlib import Path

import yaml

def minizinc_in_path():
    path_list = os.environ.get("PATH", "").split(os.pathsep)
    return any([
        True if len(glob.glob(str(Path(p) / "*minizinc*"))) > 0 else False
        for p in path_list
    ])

def save_file(location, content: str):
    with open(location, "w") as f:
        f.write(content)

def run_parser(
    parser_location,
    model_location,
    components_yaml_file,
    infrastructure_yaml_file,
    additional_resources,
    old_deployment_location,
    constraints,
    model_name_prefix=None
):
    command = [
        parser_location / ".venv" / "bin" / "python",
        parser_location / "main.py",
        components_yaml_file,
        infrastructure_yaml_file,
        "--dump-importances", model_location / "importances.yaml",
        "-f", "mzn"
    ]
    if additional_resources is not None:
        command.extend(["-r", additional_resources])
    if old_deployment_location is not None:
        command.extend(["-d", old_deployment_location])
    if constraints is not None:
        command.extend(["-c", constraints])
    try:
        completed_parsing = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
    except Exception as e:
        print(e.stderr)
        exit()

    model_file_path = model_location / (
        (str(model_name_prefix) + "_" if model_name_prefix is not None else "") + "model.mzn"
    )
    save_file(model_file_path, completed_parsing.stdout)

    return model_file_path


def run_model(model_file_path, deployment_output_file_path):
    command = [
        "minizinc",
        "--compiler-statistics",
        "--output-mode", "json",
        "--output-objective",
        "--no-output-ozn",
        "--json-stream",
        "--time-limit", "600",
        str(model_file_path.resolve())
    ]
    try:
        completed_run = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
    except Exception as e:
        print(e)
        exit()

    json_results = [
        json.loads(x.strip())
        for x in completed_run.stdout.split("\n")
        if len(x) > 0 and x != "{}"
    ]

    last_status = [j for j in json_results if j["type"] == "status"][-1]["status"]
    if last_status not in ["SATISFIABLE", "OPTIMAL_SOLUTION"]:
        raise SystemError("The solver could not find a proper solution:", json_results)

    # Step 3: get the deployment
    old_deployment = [j for j in json_results if j["type"] == "solution"][-1]["output"]["default"]
    old_deployment_location = deployment_output_file_path / "deployment.txt"

    save_file(old_deployment_location, old_deployment)

    return old_deployment_location


def parse_and_run(
    parser_location,
    lsco_t,
    components_yaml_file,
    infrastructure_yaml_file,
    additional_resources,
    deployment_location,
    constraints_location,
    model_name_prefix=None
):
    # Step 1: call the parser and get the model mzn
    model_file_path = run_parser(
        parser_location,
        lsco_t,
        components_yaml_file,
        infrastructure_yaml_file,
        additional_resources,
        deployment_location,
        constraints_location,
        model_name_prefix
    )

    # Step 2: run the mzn
    if not minizinc_in_path():
        raise AssertionError("Please add MiniZinc to your PATH variable")

    deployment_location = run_model(model_file_path, lsco_t)

    return deployment_location


def try_until_sucess(
    parser_location,
    lsco_t,
    components_yaml_file,
    infrastructure_yaml_file,
    additional_resources,
    constraints_location,
    new_constraints_location,
    deployment_location
):
    with open(constraints_location, "r") as f:
        constraints = yaml.safe_load(f)
    cs = [
        (c, f, idx)
        for c, fs in constraints["requirements"]["components"].items()
        for f in fs.keys()
        for idx, _ in enumerate(constraints["requirements"]["components"][c][f])
    ]
    i = 0

    if len(cs) == 0:
        return parse_and_run(
            parser_location,
            lsco_t,
            components_yaml_file,
            infrastructure_yaml_file,
            additional_resources,
            deployment_location,
            constraints_location
        )

    for amount in range(len(cs)):
        for to_remove in itertools.combinations(cs, amount):
            if to_remove:
                print("SOLVER - removed constraints: " + str(to_remove))
            new_constraints = copy.deepcopy(constraints)
            # Remove the constraint selected
            for rs in to_remove:
                c, f, idx = rs
                del new_constraints["requirements"]["components"][c][f][idx]

                # Clean it up a bit if needed
                if len(new_constraints["requirements"]["components"][c][f]) == 0:
                    del new_constraints["requirements"]["components"][c][f]
                if len(new_constraints["requirements"]["components"][c].values()) == 0:
                    del new_constraints["requirements"]["components"][c]

            try:
                zfilled = str(i).zfill(int(math.log10(2 ** len(cs))) + 1)
                constraints_location = new_constraints_location / (zfilled + "_constraints.yaml")
                with open(constraints_location, "w") as f:
                    yaml.safe_dump(new_constraints, f)

                deployment_location = parse_and_run(
                    parser_location,
                    lsco_t,
                    components_yaml_file,
                    infrastructure_yaml_file,
                    additional_resources,
                    deployment_location,
                    constraints_location,
                    model_name_prefix=zfilled
                )

                # As the first feasible deployment is found, return immediately
                return deployment_location

            except SystemError as e:
                print(f"Attempt {zfilled} failed. Retrying")
            i += 1

    # No feasible deployment was found. Fail.
    raise Exception("No feasible deployment was found. Failing.")
