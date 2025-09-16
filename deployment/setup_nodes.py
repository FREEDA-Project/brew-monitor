#!/usr/bin/env python3
import argparse
import subprocess
import logging
import time
import os
import json
import yaml
from typing import Dict, List

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MinikubeCluster:
    def __init__(self, 
                 cluster_name: str,
                 cluster_config: dict,
                 driver: str = "docker"):
        self.cluster_name = cluster_name
        self.cluster_config = cluster_config
        self.driver = driver
        self.nodes: List[str] = []
        self.num_nodes = len(cluster_config['nodes'])

    def run_command(self, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        try:
            logger.info(f"Running command: {' '.join(command)}")
            result = subprocess.run(
                command,
                check=check,
                capture_output=True,
                text=True
            )
            if result.stdout:
                logger.info(f"Command output: {result.stdout}")
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running command {' '.join(command)}")
            logger.error(f"Output: {e.output}")
            logger.error(f"Stderr: {e.stderr}")
            raise

    def check_prerequisites(self):
        logger.info("Checking prerequisites...")
        # Check Minikube
        try:
            self.run_command(["minikube", "version"])
        except subprocess.CalledProcessError:
            logger.error("Minikube is not installed. Install Minikube before proceeding.")
            raise

        # Check driver
        if self.driver == "docker":
            try:
                self.run_command(["docker", "version"])
            except subprocess.CalledProcessError:
                logger.error("Docker is not installed. Install Docker before proceeding.")
                raise

    def create_cluster(self):
        logger.info(f"Creating cluster {self.cluster_name}...")
        
        # Take first node config for control plane resources
        first_node = next(iter(self.cluster_config['nodes'].values()))
        memory = str(first_node['capabilities']['ram'] * 1024)
        cpus = str(first_node['capabilities']['cpu'])
        
        # Delete cluster if it exists for a clean creation
        try:
            logger.info(f"Deleting cluster {self.cluster_name} if it exists...")
            self.run_command(["minikube", "delete", "-p", self.cluster_name], check=False)
        except Exception as e:
            logger.warning(f"Error cleaning existing cluster: {str(e)}")
        
        # Command to create cluster with all nodes
        command = [
            "minikube", "start",
            "-p", self.cluster_name,
            "--cpus", cpus,
            "--memory", f"{memory}mb",
            "--nodes", str(self.num_nodes),
            "--driver", self.driver
        ]
        
        logger.info(f"Executing command to create cluster: {' '.join(command)}")
        self.run_command(command)
        
        # Wait for cluster to stabilize
        logger.info("Waiting 60 seconds for cluster to stabilize before applying labels...")
        time.sleep(60)

        # --- BEGIN MODIFIED AND ADDED LOGIC ---
        logger.info("Applying labels to cluster nodes...")

        # Map logical YAML node names to actual Minikube node names
        defined_nodes_config = self.cluster_config.get('nodes', {})
        logical_node_names = list(defined_nodes_config.keys())

        for index, logical_name in enumerate(logical_node_names):
            # Determine actual node name created by Minikube
            if index == 0:
                actual_node_name = self.cluster_name # First node has same name as cluster profile
            else:
                # Subsequent nodes: <cluster>-m02, <cluster>-m03, etc.
                actual_node_name = f"{self.cluster_name}-m{index + 1:02d}"
            
            logger.info(f"Configuring node: {actual_node_name} (corresponding to '{logical_name}')")
            self.nodes.append(actual_node_name)

            # Add 'worker' label if not main node
            if index > 0:
                self.label_worker_nodes(actual_node_name)

            # Retrieve and apply custom labels from profile
            node_config = defined_nodes_config[logical_name]
            profile = node_config.get('profile', {})
            
            cost = profile.get('cost')
            carbon = profile.get('carbon')
            
            if cost is not None:
                logger.info(f"  -> Applying label cost={cost}")
                self.run_command([
                    "kubectl", "label", "node", actual_node_name,
                    f"cost={cost}", "--overwrite"
                ], check=False)
            
            if carbon is not None:
                logger.info(f"  -> Applying label carbon={carbon}")
                self.run_command([
                    "kubectl", "label", "node", actual_node_name,
                    f"carbon={carbon}", "--overwrite"
                ], check=False)

    def get_node_names(self) -> List[str]:
        command = ["kubectl", "get", "nodes", "-o", "json"]
        result = self.run_command(command)
        nodes = json.loads(result.stdout)
        
        if len(nodes["items"]) == 0:
            raise Exception("No nodes found")
        
        return [node["metadata"]["name"] for node in nodes["items"]]

    def label_worker_nodes(self, node_name: str):
        logger.info(f"Assigning 'worker' role to node {node_name}...")
        
        command = [
            "kubectl", "label", "nodes", node_name, "node-role.kubernetes.io/worker=worker", "--overwrite"
        ]
    
        self.run_command(command)
        logger.info(f"'worker' role assigned to {node_name}")

    def verify_cluster(self):
        logger.info("Verifying cluster status...")
        
        # Check nodes
        command = ["kubectl", "get", "nodes", "-o", "json"]
        result = self.run_command(command)
        nodes = json.loads(result.stdout)
        
        if len(nodes["items"]) != self.num_nodes:
            raise Exception(f"Incorrect number of nodes. Expected: {self.num_nodes}, Found: {len(nodes['items'])}")
        
        # Check node status
        for node in nodes["items"]:
            node_name = node["metadata"]["name"]
            conditions = {c["type"]: c["status"] for c in node["status"]["conditions"]}
            
            if conditions.get("Ready") != "True":
                raise Exception(f"Node {node_name} is not ready")
            
            # Get node resources
            capacity = node["status"]["capacity"]
            logger.info(f"Node {node_name} ready - CPU: {capacity['cpu']}, Memory: {capacity['memory']}")

    def setup(self):
        try:
            self.check_prerequisites()
            self.create_cluster()
            self.verify_cluster()
            
            logger.info(f"\nCluster {self.cluster_name} configured successfully!")
            logger.info(f"Nodes created: {', '.join(self.nodes)}")
            
            # Display useful info
            logger.info("Cluster info:")
            result = self.run_command(["kubectl", "cluster-info"])
            logger.info(result.stdout)

            logger.info("Cluster nodes:")
            result = self.run_command(["kubectl", "get", "nodes", "--show-labels"])
            logger.info(result.stdout)
            
        except Exception as e:
            logger.error(f"Error during cluster setup: {str(e)}")
            self.cleanup()
            raise

    def cleanup(self): 
        logger.info("Cleaning up cluster...")
        try:
            self.run_command(["minikube", "delete", "-p", self.cluster_name], check=False)
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

class ClusterManager:
    def __init__(self, config_file: str):
        self.config = self._load_config(config_file)
        self.clusters = {}

    def _load_config(self, config_file: str) -> Dict:
        try:
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading configuration file: {str(e)}")
            raise

    def setup_clusters(self):
        cluster_name=self.config['name']
        
        logger.info(f"\nSetting up cluster {cluster_name}...")
        cluster = MinikubeCluster(
            cluster_name=cluster_name,
            cluster_config=self.config
        )
    
        cluster.setup()
        self.clusters[cluster_name] = cluster

    def cleanup_clusters(self):
        for cluster_name, cluster in self.clusters.items():
            logger.info(f"\nCleaning up cluster {cluster_name}...")
            cluster.cleanup()

def main():
    parser = argparse.ArgumentParser(description='Set up multi-node Kubernetes cluster with Minikube')
    parser.add_argument('--config', type=str, required=True, help='Path to YAML configuration file')
    parser.add_argument('--delete', action='store_true', help='Delete existing clusters')
    
    args = parser.parse_args()
    
    manager = ClusterManager(config_file=args.config)
    
    if args.delete:
        manager.cleanup_clusters()
    else:
        manager.setup_clusters()

if __name__ == "__main__":
    main()
