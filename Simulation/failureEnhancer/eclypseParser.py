import re
import argparse

PLACEMENT_PATTERN = re.compile(r'\{(.*?)\}')
FAILURE_PATTERN = re.compile(r'Node (\S+) not respected')
REQUIRED_RESOURCE_PATTERN = re.compile(r"Required: \{.*?'cpu': (\d+(?:\.\d+)?), 'ram': (\d+(?:\.\d+)?)")
AVAILABLE_RESOURCE_PATTERN = re.compile(r"Available: \{.*?'cpu': (\d+(?:\.\d+)?), 'ram': (\d+(?:\.\d+)?)")
TICK_PATTERN = re.compile(r'Event Tick-(\d+) fired')

def parse_log(log_file):
    deployments = {} 
    failures = set()
    overloads_cpu = {} 
    overloads_ram = {}
    current_tick = 0
    required_resources = {}
    
    with open(log_file, 'r') as f:
        for line in f:
            tick_match = TICK_PATTERN.search(line)
            if tick_match:
                current_tick = int(tick_match.group(1))
            
            # Extract deployments
            match = PLACEMENT_PATTERN.search(line)
            if match:
                pairs = match.group(1).split('|')
                for pair in pairs:
                    pair = pair.strip()
                    if '->' in pair:
                        try:
                            service, node = pair.split('->')
                            service = service.strip()
                            node = node.strip()
                            name, size = service.rsplit('_', 1)
                            deployments.setdefault(node, []).append((name, size))
                        except ValueError:
                            print(f"Malformed entry: {pair}")
            
            # Extract failures and map them to affected services
            match = FAILURE_PATTERN.search(line)
            if match:
                node = match.group(1)
                if node in deployments:
                    for service, size in deployments[node]:
                        failures.add(f"unreachable({service}, {current_tick}).")
                else:
                    failures.add(f"unreachable({node}, {current_tick}).")
            
            # Extract required resources
            req_match = REQUIRED_RESOURCE_PATTERN.search(line)
            if req_match:
                req_cpu, req_ram = map(float, req_match.groups())
                required_resources[current_tick] = (req_cpu, req_ram)
            
            avail_match = AVAILABLE_RESOURCE_PATTERN.search(line)
            if avail_match and current_tick in required_resources:
                avail_cpu, avail_ram = map(float, avail_match.groups())
                req_cpu, req_ram = required_resources[current_tick]
                
                if avail_cpu < req_cpu:
                    if node not in overloads_cpu:
                        overloads_cpu[node] = (current_tick, current_tick)
                    else:
                        overloads_cpu[node] = (overloads_cpu[node][0], current_tick)
                
                if avail_ram < req_ram:
                    if node not in overloads_ram:
                        overloads_ram[node] = (current_tick, current_tick)
                    else:
                        overloads_ram[node] = (overloads_ram[node][0], current_tick)
    
    # Prolog rules
    overload_cpu_rules = [f"overload({node}, cpu, {start}, {end})." for node, (start, end) in overloads_cpu.items()]
    overload_ram_rules = [f"overload({node}, ram, {start}, {end})." for node, (start, end) in overloads_ram.items()]
    deployment_rules = {f"deployedTo({name}, {size}, {node})." for node, services in deployments.items() for name, size in services}
    
    return sorted(deployment_rules), sorted(failures), sorted(overload_cpu_rules), sorted(overload_ram_rules)

def generate_prolog_rules(log_file, output_file):
    deployments, failures, overloads_cpu, overloads_ram = parse_log(log_file)
    
    with open(f"{output_file}.pl", 'w') as f:
        f.write("% Deployment\n")
        f.write("\n".join(deployments) + "\n\n")
        f.write("% Components failures\n")
        f.write("\n".join(failures) + "\n\n")
        f.write("% Nodes failures\n")
        f.write("\n".join(overloads_cpu) + "\n")
        f.write("\n".join(overloads_ram) + "\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="Path to simulation log")
    parser.add_argument("-o", "--output", required=True, help="Output path")
    args = parser.parse_args()

    generate_prolog_rules(args.input, args.output)

if __name__ == "__main__":
    main()