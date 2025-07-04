from networkx.classes.reportviews import NodeView
import math
import re
import yaml
from pathlib import Path

current_path = Path(__file__).parent
app_path = current_path.parent / "app_case_study.yaml"
infr_path = current_path.parent / "case_study_infra.yaml"
with open(app_path, "r") as file:
    myapp = yaml.safe_load(file)
with open(infr_path, "r") as file:
    myinfr = yaml.safe_load(file)

class noscenario:
    def __init__(self):
        self.tick = 0
    def __call__(self, nodes: NodeView):
        self.tick += 1

class epublic1:
    def __init__(self):
        self.tick = 0
        self.totalticks = 144
        self.amplitude = 0
    # We constantly reduce the node's carbon
    def __call__(self, nodes: NodeView):
        failing_node = nodes['public1']
        if self.tick == 0:
            self.amplitude = float(myinfr["nodes"]["public1"]["profile"]["carbon"]) / 2
        k = math.pi * self.tick / (self.totalticks)
        delta = self.amplitude * math.sin(k)
        failing_node['carbon'] = float(myinfr["nodes"]["public1"]["profile"]["carbon"]) + float(delta)
        self.tick += 1

class epublic2:
    def __init__(self):
        self.tick = 0
        self.totalticks = 144
        self.amplitude = 0
    # We constantly reduce the node's carbon
    def __call__(self, nodes: NodeView):
        failing_node = nodes['public2']
        if self.tick == 0:
            self.amplitude = float(myinfr["nodes"]["public2"]["profile"]["carbon"])
        k = math.pi * self.tick / (self.totalticks)
        delta = self.amplitude * math.sin(k)
        failing_node['carbon'] = float(myinfr["nodes"]["public2"]["profile"]["carbon"]) + float(delta)
        self.tick += 1

class eprivate1:
    def __init__(self):
        self.tick = 0
        self.totalticks = 144
        self.amplitude = 0
    # We constantly reduce the node's carbon
    def __call__(self, nodes: NodeView):
        failing_node = nodes['private1']
        if self.tick == 0:
            self.amplitude = float(myinfr["nodes"]["private1"]["profile"]["carbon"])
        k = math.pi * self.tick / (self.totalticks)
        delta = self.amplitude * math.sin(k)
        failing_node['carbon'] = float(myinfr["nodes"]["private1"]["profile"]["carbon"]) + float(delta)
        self.tick += 1

class eprivate2:
    def __init__(self):
        self.tick = 0
        self.totalticks = 144
        self.amplitude = 0
    # We constantly reduce the node's carbon
    def __call__(self, nodes: NodeView):
        failing_node = nodes['private2']
        if self.tick == 0:
            self.amplitude = float(myinfr["nodes"]["private2"]["profile"]["carbon"]) * 9
        k = math.pi * self.tick / (self.totalticks)
        delta = self.amplitude * math.sin(k)
        failing_node['carbon'] = float(myinfr["nodes"]["private2"]["profile"]["carbon"]) + float(delta)
        self.tick += 1

class eprivate3:
    def __init__(self):
        self.tick = 0
        self.totalticks = 144
        self.amplitude = 0
    # We constantly reduce the node's carbon
    def __call__(self, nodes: NodeView):
        failing_node = nodes['private3']
        if self.tick == 0:
            self.amplitude = float(myinfr["nodes"]["private3"]["profile"]["carbon"]) / 2
        k = math.pi * self.tick / (self.totalticks)
        delta = self.amplitude * math.sin(k)
        failing_node['carbon'] = float(myinfr["nodes"]["private3"]["profile"]["carbon"]) + float(delta)
        self.tick += 1

class eprivate4:
    def __init__(self):
        self.tick = 0
        self.totalticks = 144
        self.amplitude = 0
    # We constantly reduce the node's carbon
    def __call__(self, nodes: NodeView):
        failing_node = nodes['private4']
        if self.tick == 0:
            self.amplitude = float(myinfr["nodes"]["private4"]["profile"]["carbon"]) * 4
        k = math.pi * self.tick / (self.totalticks)
        delta = self.amplitude * math.sin(k)
        failing_node['carbon'] = float(myinfr["nodes"]["private4"]["profile"]["carbon"]) + float(delta)
        self.tick += 1

class eprivate5:
    def __init__(self):
        self.tick = 0
        self.totalticks = 144
        self.amplitude = 0
    # We constantly reduce the node's carbon
    def __call__(self, nodes: NodeView):
        failing_node = nodes['private5']
        if self.tick == 0:
            self.amplitude = float(myinfr["nodes"]["private5"]["profile"]["carbon"])
        k = math.pi * self.tick / (self.totalticks)
        delta = self.amplitude * math.sin(k)
        failing_node['carbon'] = float(myinfr["nodes"]["private5"]["profile"]["carbon"]) + float(delta)
        self.tick += 1

class eloadbalancer:
    def __init__(self):
        self.tick = 0
        self.totalticks = 144
        self.amplitude = 0
    # We constantly raise the service's energy
    def __call__(self, nodes: NodeView):
        key = next((k for k in nodes if re.match(r'load_balancer(_.+)?$', k)), None)
        flavour = re.search(r'_(tiny|medium|large)$', key).group(1)
        failing_service = nodes[key]
        if self.tick == 0:
            self.amplitude = float(myapp["components"]["load_balancer"]["flavours"][flavour]["energy"])
        k = math.pi * self.tick / (self.totalticks)
        delta = self.amplitude * math.sin(k)
        failing_service['energy'] = float(myapp["components"]["load_balancer"]["flavours"][flavour]["energy"]) + float(delta)
        self.tick += 1

class efrontend:
    def __init__(self):
        self.tick = 0
        self.totalticks = 144
        self.amplitude = 0
    # We constantly raise the service's energy
    def __call__(self, nodes: NodeView):
        key = next((k for k in nodes if re.match(r'frontend(_.+)?$', k)), None)
        flavour = re.search(r'_(tiny|medium|large)$', key).group(1)
        failing_service = nodes[key]
        if self.tick == 0:
            self.amplitude = float(myapp["components"]["frontend"]["flavours"][flavour]["energy"]) * 2
        k = math.pi * self.tick / (self.totalticks)
        delta = self.amplitude * math.sin(k)
        failing_service['energy'] = float(myapp["components"]["frontend"]["flavours"][flavour]["energy"]) + float(delta)
        self.tick += 1

class eapi:
    def __init__(self):
        self.tick = 0
        self.totalticks = 144
        self.amplitude = 0
        
    # We constantly raise the service's energy
    def __call__(self, nodes: NodeView):
        key = next((k for k in nodes if re.match(r'api(_.+)?$', k)), None)
        flavour = re.search(r'_(tiny|medium|large)$', key).group(1)
        failing_service = nodes[key]
        if self.tick == 0:
            self.amplitude = float(myapp["components"]["api"]["flavours"][flavour]["energy"]) * 2
        k = math.pi * self.tick / (self.totalticks)
        delta = self.amplitude * math.sin(k)
        failing_service['energy'] = float(myapp["components"]["api"]["flavours"][flavour]["energy"]) + float(delta)
        self.tick += 1

class eidentityprovider:
    def __init__(self):
        self.tick = 0
        self.totalticks = 144
        self.amplitude = 0
    # We constantly raise the service's energy
    def __call__(self, nodes: NodeView):
        key = next((k for k in nodes if re.match(r'identity_provider(_.+)?$', k)), None)
        flavour = re.search(r'_(tiny|medium|large)$', key).group(1)
        failing_service = nodes[key]
        if self.tick == 0:
            self.amplitude = float(myapp["components"]["identity_provider"]["flavours"][flavour]["energy"])
        k = math.pi * self.tick / (self.totalticks)
        delta = self.amplitude * math.sin(k)
        failing_service['energy'] = float(myapp["components"]["identity_provider"]["flavours"][flavour]["energy"]) + float(delta)
        self.tick += 1

class edatabase:
    def __init__(self):
        self.tick = 0
        self.totalticks = 144
        self.amplitude = 0
    # We constantly raise the service's energy
    def __call__(self, nodes: NodeView):
        key = next((k for k in nodes if re.match(r'database(_.+)?$', k)), None)
        flavour = re.search(r'_(tiny|medium|large)$', key).group(1)
        failing_service = nodes[key]
        if self.tick == 0:
            self.amplitude = float(myapp["components"]["database"]["flavours"][flavour]["energy"]) / 2
        k = math.pi * self.tick / (self.totalticks)
        delta = self.amplitude * math.sin(k)
        failing_service['energy'] = float(myapp["components"]["database"]["flavours"][flavour]["energy"]) + float(delta)
        self.tick += 1

class eredis:
    def __init__(self):
        self.tick = 0
        self.totalticks = 144
        self.amplitude = 0
    # We constantly raise the service's energy
    def __call__(self, nodes: NodeView):
        key = next((k for k in nodes if re.match(r'redis(_.+)?$', k)), None)
        flavour = re.search(r'_(tiny|medium|large)$', key).group(1)
        failing_service = nodes[key]
        if self.tick == 0:
            self.amplitude = float(myapp["components"]["redis"]["flavours"][flavour]["energy"]) * 24
        k = math.pi * self.tick / (self.totalticks)
        delta = self.amplitude * math.sin(k)
        failing_service['energy'] = float(myapp["components"]["redis"]["flavours"][flavour]["energy"]) + float(delta)
        self.tick += 1

class eetcd:
    def __init__(self):
        self.tick = 0
        self.totalticks = 144
        self.amplitude = 0
    # We constantly raise the service's energy
    def __call__(self, nodes: NodeView):
        key = next((k for k in nodes if re.match(r'etcd(_.+)?$', k)), None)
        flavour = re.search(r'_(tiny|medium|large)$', key).group(1)
        failing_service = nodes[key]
        if self.tick == 0:
            self.amplitude = float(myapp["components"]["etcd"]["flavours"][flavour]["energy"]) * 39
        k = math.pi * self.tick / (self.totalticks)
        delta = self.amplitude * math.sin(k)
        failing_service['energy'] = float(myapp["components"]["etcd"]["flavours"][flavour]["energy"]) + float(delta)
        self.tick += 1

# Scenario 2: Scenario 1 + Overloading node Public1
class scenario2:
    def __init__(self):
        self.tick = 0
        self.factor = 0.991
    # We constantly reduce the node's CPU and RAM
    def __call__(self, nodes: NodeView):
        if self.tick > 49:
            failing_node = nodes['public1']
            failing_node['cpu'] *= self.factor
            failing_node['ram'] *= self.factor
        self.tick += 1

# Scenario 2energy: Scenario 1 + Failing node Public 1
class scenario2energy:
    def __init__(self):
        self.tick = 0

    # We constantly raise the node's energy
    def __call__(self, nodes: NodeView):
        if self.tick > 49:
            failing_node = nodes['private5']
            #greener_node = nodes['private3']
            factor = 0.98
            failing_node['carbon'] /= factor
            #greener_node['carbon'] *= factor
        self.tick += 1

# Scenarion 3energy: Scenario 2 + Failing servce
class scenario3energy:
    def __init__(self):
        self.tick = 0

    # We constantly raise the service's energy
    def __call__(self, nodes: NodeView):
        if self.tick > 49:
            failing_node = nodes['api_large']
            factor = 0.99
            failing_node['energy'] /= factor
        self.tick += 1

class scenarioDEMOinfrastructure:
    def __init__(self):
        self.tick = 0
        self.initial_cpu = 8
        self.initial_ram = 16

    # We constantly reduce node public1 cpu and ram
    def __call__(self, nodes: NodeView):
        if self.tick > 49 and self.tick < 140:
            failing_node = nodes['public1']
            factor = 0.991
            failing_node['cpu'] *= factor
            failing_node['ram'] *= factor
        if self.tick > 140:
            failing_node = nodes['public1']
            failing_node['cpu'] = self.initial_cpu
            failing_node['ram'] = self.initial_ram
        self.tick += 1

class scenarioDEMOapplication:
    def __init__(self):
        self.tick = 0

    # We constantly raise the service's energy
    def __call__(self, nodes: NodeView):
        if self.tick > 49:
            failing_service = next((nodes[key] for key in nodes if key.startswith('api_')))
            service_factor = 0.99
            failing_service['energy'] /= service_factor
        self.tick += 1

class scenarioDEMOapplication2:
    def __init__(self):
        self.tick = 0

    # We constantly raise the service's energy
    def __call__(self, nodes: NodeView):
        if self.tick > 49:
            failing_service = next((nodes[key] for key in nodes if key.startswith('api_')))
            service_factor = 0.99
            failing_service['energy'] /= service_factor
        self.tick += 1

# Scenario 3:
# Delete the link between private1 and private3.
# Overload node private1.
class scenario3:
    def __init__(self):
        self.tick = 0
        self.initial_cpu = 3
        self.initial_ram = 16
        self.cpuFactor = 0.993
        self.ramFactor = 0.98
    # We reduce private1 CPU and RAM
    def __call__(self, nodes: NodeView):
        failing_node = nodes['private1']
        if self.tick > 47 and self.tick < 99:
            failing_node['cpu'] *= self.cpuFactor
            failing_node['ram'] *= self.ramFactor
        else:
            failing_node['cpu'] = self.initial_cpu
            failing_node['ram'] = self.initial_ram
        self.tick += 1

class ebestfit:
    def __init__(self):
        self.tick = 0
        self.public2_cpu = float(myinfr["nodes"]["public2"]["capabilities"]["cpu"])
        self.public2_ram = float(myinfr["nodes"]["public2"]["capabilities"]["ram"])
        self.public1_cpu = float(myinfr["nodes"]["public1"]["capabilities"]["cpu"])
        self.public1_ram = float(myinfr["nodes"]["public1"]["capabilities"]["ram"])
    def __call__(self, nodes: NodeView):
        public2 = nodes['public2']
        public1 = nodes['public1']
        if self.tick > 30 and self.tick < 99:
            public2['cpu'] = 2
            public2['ram'] = 4
            public1['cpu'] = 2
            public1['ram'] = 3
        else:
            public2['cpu'] = self.public2_cpu
            public2['ram'] = self.public2_ram
            public1['cpu'] = self.public1_cpu
            public1['ram'] = self.public1_ram
        self.tick += 1
            
class energyapp1:
    def __init__(self):
        self.tick = 0

    # We constantly raise the service's energy
    def __call__(self, nodes: NodeView):
        if self.tick > 49:
            service_factor = 0.99
            failing_service = next((nodes[key] for key in nodes if key.startswith('api_')))
            failing_service['energy'] = float(failing_service['energy']) / service_factor
        self.tick += 1

class energyapp2:
    def __init__(self):
        self.tick = 0

    # We constantly raise the service's energy
    def __call__(self, nodes: NodeView):
        if self.tick > 49:
            service_factor = 0.99
            # failing_service = next((nodes[key] for key in nodes if key.startswith('api_')))
            # failing_service['energy'] = float(failing_service['energy']) / service_factor
            failing_service2 = next((nodes[key] for key in nodes if key.startswith('database_')))
            failing_service2['energy'] = float(failing_service2['energy']) / service_factor
        self.tick += 1

class energyapp3:
    def __init__(self):
        self.tick = 0

    # We constantly raise the service's energy
    def __call__(self, nodes: NodeView):
        if self.tick > 49:
            service_factor = 0.99
            # failing_service = next((nodes[key] for key in nodes if key.startswith('api_')))
            # failing_service['energy'] = float(failing_service['energy']) / service_factor
            # failing_service2 = next((nodes[key] for key in nodes if key.startswith('database_')))
            # failing_service2['energy'] = float(failing_service2['energy']) / service_factor
            failing_service3 = next((nodes[key] for key in nodes if key.startswith('identity_provider_')))
            failing_service3['energy'] = float(failing_service3['energy']) / service_factor
        self.tick += 1

class energyinfr1:
    def __init__(self):
        self.tick = 0

    # We constantly raise the node's energy
    def __call__(self, nodes: NodeView):
        if self.tick > 49:
            factor = 0.99
            failing_node = nodes['private5']
            failing_node['carbon'] = float(failing_node['carbon']) / factor
        self.tick += 1

class energyinfr2:
    def __init__(self):
        self.tick = 0

    # We constantly raise the node's energy
    def __call__(self, nodes: NodeView):
        if self.tick > 49:
            factor = 0.99
            # failing_node = nodes['private5']
            # failing_node['carbon'] = float(failing_node['carbon']) / factor
            failing_node2 = nodes['private1']
            failing_node2['carbon'] = float(failing_node2['carbon']) / factor
        self.tick += 1

class energyinfr3:
    def __init__(self):
        self.tick = 0

    # We constantly raise the node's energy
    def __call__(self, nodes: NodeView):
        if self.tick > 49:
            factor = 0.99
            # failing_node = nodes['private5']
            # failing_node['carbon'] = float(failing_node['carbon']) / factor
            # failing_node2 = nodes['private1']
            # failing_node2['carbon'] = float(failing_node2['carbon']) / factor
            failing_node3 = nodes['private2']
            failing_node3['carbon'] = float(failing_node3['carbon']) / factor
        self.tick += 1