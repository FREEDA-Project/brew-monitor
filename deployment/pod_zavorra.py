#!/usr/bin/env python3
import argparse
import yaml
import logging
import sys
import json
import subprocess
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define fixed buffers to reserve free resources
CPU_BUFFER = 0.8  # 0.8 CPU cores (equivalent to 800m)
RAM_BUFFER_GB = 800 / 1024  # 800MB converted to GiB

def parse_k8s_quantity(value: str) -> float:
    """
    Convert Kubernetes resource quantities (CPU and memory) to base units.
    CPU -> cores (e.g., 1.0, 0.5)
    Memory -> GiB (e.g., 8.0, 0.5)
    """
    value = str(value).lower()
    if value.endswith('gi'):
        return float(value[:-2])
    if value.endswith('mi'):
        return float(value[:-2]) / 1024
    if value.endswith('ki'):
        return float(value[:-2]) / 1024 / 1024
    if value.endswith('i'):  # Non-standard format
        return float(value[:-1]) / 1024
    
    if value.endswith('m'):  # CPU in millicores
        return float(value.rstrip('m')) / 1000
    
    try:
        return float(value)
    except ValueError:
        return 0.0

def get_true_available_resources(app_namespace: str) -> Dict[str, Dict[str, float]]:
    """
    Compute the truly available resources per node by subtracting
    pod consumption in 'kube-system' and in the application namespace.
    """
    try:
        # 1. Get total allocatable resources per node
        nodes_result = subprocess.run(["kubectl", "get", "nodes", "-o", "json"], check=True, capture_output=True, text=True)
        nodes_data = json.loads(nodes_result.stdout)
        
        allocatable_resources = {}
        for node in nodes_data.get('items', []):
            name = node['metadata']['name']
            allocatable = node['status']['allocatable']
            allocatable_resources[name] = {
                'cpu': parse_k8s_quantity(allocatable.get('cpu', '0')),
                'ram': parse_k8s_quantity(allocatable.get('memory', '0'))
            }

        # 2. Aggregate pod consumption (system + application)
        total_consumption = {node_name: {'cpu': 0.0, 'ram': 0.0} for node_name in allocatable_resources}
        
        for namespace in ["kube-system", app_namespace]:
            try:
                pods_result = subprocess.run(
                    ["kubectl", "get", "pods", "-n", namespace, "-o", "json"],
                    check=True, capture_output=True, text=True
                )
                pods_data = json.loads(pods_result.stdout)
            except subprocess.CalledProcessError as e:
                # Ignore if namespace does not exist
                if "NotFound" in e.stderr:
                    logger.warning(f"Namespace '{namespace}' not found, skipping.")
                    continue
                raise e

            for pod in pods_data.get('items', []):
                node_name = pod['spec'].get('nodeName')
                # Consider only pods actually running on a node
                if node_name and node_name in total_consumption:
                    for container in pod['spec'].get('containers', []):
                        requests = container.get('resources', {}).get('requests', {})
                        if 'cpu' in requests:
                            total_consumption[node_name]['cpu'] += parse_k8s_quantity(requests['cpu'])
                        if 'memory' in requests:
                            total_consumption[node_name]['ram'] += parse_k8s_quantity(requests['memory'])

        # 3. Compute final available resources
        available_resources = {
            name: {
                'cpu': res['cpu'] - total_consumption[name]['cpu'],
                'ram': res['ram'] - total_consumption[name]['ram']
            } for name, res in allocatable_resources.items()
        }
        
        logger.info(f"Actual available resources (after subtracting all pods): {available_resources}")
        return available_resources

    except Exception as e:
        logger.error(f"Unable to obtain resources from Kubernetes nodes. Error: {e}")
        sys.exit(1)

def create_ballast_manifest(config_path: str, output_path: str, namespace: str):
    real_available_resources = get_true_available_resources(namespace)
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    cluster_name = config.get('name')
    nodes_config = config.get('nodes', {})
    
    ballast_pods = []
    
    logical_to_physical = {}
    logical_node_names = list(nodes_config.keys())
    if logical_node_names:
        logical_to_physical[logical_node_names[0]] = cluster_name
        for i, logical_name in enumerate(logical_node_names[1:]):
            logical_to_physical[logical_name] = f"{cluster_name}-m{i + 2:02d}"

    for logical_name, actual_k8s_node_name in logical_to_physical.items():
        if actual_k8s_node_name not in real_available_resources:
            logger.warning(f"Node '{actual_k8s_node_name}' not found. Skipping.")
            continue
            
        real_cpu = real_available_resources[actual_k8s_node_name]['cpu']
        real_ram_gb = real_available_resources[actual_k8s_node_name]['ram']

        capabilities = nodes_config[logical_name].get('capabilities', {})
        desired_cpu = capabilities.get('cpu', real_cpu)
        desired_ram_gb = capabilities.get('ram', real_ram_gb)
        
        # Compute ballast to apply, subtracting buffers
        cpu_to_request = real_cpu - desired_cpu - CPU_BUFFER
        ram_to_request_gb = real_ram_gb - desired_ram_gb - RAM_BUFFER_GB

        # Ensure requests are not negative
        if cpu_to_request < 0:
            cpu_to_request = 0
        if ram_to_request_gb < 0:
            ram_to_request_gb = 0

        # Skip pod creation if almost nothing to request
        if cpu_to_request < 0.1 and ram_to_request_gb < 0.1:
            logger.info(f"Node '{actual_k8s_node_name}' does not require a ballast pod (insufficient space for buffer).")
            continue

        logger.info(f"   -> Node '{actual_k8s_node_name}': Calculated ballast: {cpu_to_request:.2f} CPU & {ram_to_request_gb:.2f} GB (including buffer of {CPU_BUFFER} CPU and {RAM_BUFFER_GB*1024:.0f} MB).")

        cpu_request_str = f"{int(cpu_to_request * 1000)}m"
        ram_request_str = f"{int(ram_to_request_gb * 1024)}Mi"

        pod_name = f"ballast-pod-{logical_name.replace('_', '-')}"
        pod_spec = {
            'apiVersion': 'v1', 'kind': 'Pod',
            'metadata': {
                'name': pod_name,
                'namespace': namespace,
                'labels': {'type': 'ballast'}
            },
            'spec': {
                'affinity': {'nodeAffinity': {'requiredDuringSchedulingIgnoredDuringExecution': {'nodeSelectorTerms': [{'matchExpressions': [{'key': 'kubernetes.io/hostname', 'operator': 'In', 'values': [actual_k8s_node_name]}]}]}}},
                'containers': [{'name': 'hog', 'image': 'busybox', 'command': ["sh", "-c", "sleep 3600"], 'resources': {'requests': {'cpu': cpu_request_str, 'memory': ram_request_str}}}]
            }
        }
        ballast_pods.append(pod_spec)
        
    with open(output_path, 'w') as f:
        # If no pods, file will be empty (handled by bash script)
        if ballast_pods:
            yaml.dump_all(ballast_pods, f, sort_keys=False, indent=2)
    logger.info(f"Manifest '{output_path}' generated successfully.")

def main():
    parser = argparse.ArgumentParser(description='Generate a "ballast" pod manifest based on real allocatable cluster resources.')
    parser.add_argument('--config', type=str, required=True, help='Path to node configuration file (nodes_config.yaml)')
    parser.add_argument('--output', type=str, required=True, help='Path of the output YAML file to generate (ballast.yaml)')
    parser.add_argument('--namespace', type=str, required=True, help='Namespace in which to create ballast pods.')
    args = parser.parse_args()
    create_ballast_manifest(args.config, args.output, args.namespace)

if __name__ == "__main__":
    main()
