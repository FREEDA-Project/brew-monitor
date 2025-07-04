# Set up
## Step 1: MiniZinc
### Step 1.1: download MiniZinc
Go to the [MiniZinc website](https://www.minizinc.org/resources/) and download
MiniZinc.

We currently use version 2.8.5 but newer versions *should* be fine

We currently use version 2.8.5 but newer versions *should* be fine

### Step 1.2: add MiniZinc to your PATH
```bash
export PATH=/minizinc/absolute/path:$PATH
```
NOTE: this is different on Windows machines. [Please look at this guide](https://docs.minizinc.dev/en/stable/installation.html).

## Step 2: SWI-Prolog
### Step 2.1: download SWI-Prolog
Go to the [SWI-Prolog website](https://www.swi-prolog.org/Download.html) and download
SWI-Prolog.

## Step 3: download the necessary repository
These are all repositories that needed to be cloned in order to make the loop
work.

### Step 3.1: download the parser
#### Step 3.1.1: clone the parser
Clone **in some other folder** the python parser and keep the location where you
put it.
```bash
git clone git@github.com:FREEDA-Project/Python-parser.git
```
We will call this location `python-parser-path`.

#### Step 3.1.2: create the environment for the parser
From the `python-parser-path` run
```bash
python -m venv .venv
source .venv/bin/activate
```
NOTE: Windows computer should run *activate.ps1*

### Step 3.1.3: install all parser's requirements
Only after the environment is activated (you should see a **.venv** appearing on the
left side of your terminal)
```bash
pip install -r requirements.txt
```

### Step 3.2: download the EnergyEnhancer
#### Step 3.2.1: clone the component
Clone **in some other folder** the python parser and keep the location where you
put it.
```bash
git clone git@github.com:FREEDA-Project/EnergyEnhancer.git
```
We will call this location `energy-enhancer-path`.

#### Step 3.2.2: create the environment for the component
From the `energy-enhancer-path` run
```bash
python -m venv .venv
source .venv/bin/activate
```
NOTE: Windows computer should run *activate.ps1*

### Step 3.2.3: install all component's requirements
Only after the environment is activated (you should see a **.venv** appearing on the
left side of your terminal)
```bash
pip install -r requirements.txt
```

## Step 4: environment
To set up the python enviroment, just run the following commands.

### Step 4.1: create the environment
To create the environment, from the *Simulation* folder, run
```bash
python -m venv .venv
source .venv/bin/activate
```
NOTE: Windows computer should run *activate.ps1*

### Step 4.2: install all requirements
Only after the environment is activated (you should see a **.venv** appearing on the
left side of your terminal)
```bash
pip install -r requirements.txt
```

# How to Run
## Flags

Required (positional) parameters:
- path to the python parser,
- path to the initial application yaml file,
- path to the intial infrastructure yaml file.

```bash
python parsers/loop.py python-parser-path energy-enhancer-path ../initial_app.yaml ../initial_infra.yaml
```

Optional parameters:
- **-e**: path to the energy enhancer
- **-f**: if present, enables the failure enhancer
- **-r**: additional resources yaml file (which format is specificied in the
  python parser). If missing, no additional resource will be added

## Example (with both enhancers)
```bash
python freeda/freeda.py python-parser-path ../app_case_study.yaml ../case_study_infra.yaml -f -e energy-enhancer-path -r ../../Python-parser/data/v0.3/resources_v0.3.yaml
```
