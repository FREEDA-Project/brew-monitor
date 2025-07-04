from networkx.classes.reportviews import NodeView
import math
import re
import yaml
from pathlib import Path

current_path = Path(__file__).parent
app_path = current_path.parent / "app_case_study.yaml"
infr_path = current_path.parent / "case_study_infra_Brew.yaml"
with open(app_path, "r") as file:
    myapp = yaml.safe_load(file)
with open(infr_path, "r") as file:
    myinfr = yaml.safe_load(file)

class noscenario:
    def __init__(self):
        self.tick = 0
    def __call__(self, nodes: NodeView):
        self.tick += 1

class brewBestFit:
    def __init__(self):
        self.tick = 0
        self.main_cpu = float(myinfr["nodes"]["main"]["capabilities"]["cpu"])
        self.main_ram = float(myinfr["nodes"]["main"]["capabilities"]["ram"])
    def __call__(self, nodes: NodeView):
        main = nodes['main']
        if self.tick > 30 and self.tick < 99:
            main['cpu'] = 1
            main['ram'] = 1
        else:
            main['cpu'] = self.main_cpu
            main['ram'] = self.main_ram
        self.tick += 1