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


class ResourceModifier:
    def __init__(self, cluster_name: str, cluster_config: Dict):
        self.cluster_name = cluster_name
        self.cluster_config = cluster_config 
        self.namespace = cluster_config.get('namespace', 'brewery') 

    def run_command(self, command: List[str], check: bool = True, timeout_seconds: int = 300) -> subprocess.CompletedProcess: # Added default timeout
        try:
            logger.info(f"Executing command: {' '.join(command)}")
            result = subprocess.run(
                command,
                check=check,
                capture_output=True,
                text=True,
                timeout=timeout_seconds 
            )
            if result.stdout:
                output_preview = result.stdout.strip()
                if len(output_preview) > 200:
                    output_preview = output_preview[:200] + "..."
                if output_preview:
                    logger.info(f"Command output (preview): {output_preview}")
            
            if result.returncode != 0 and result.stderr:
                logger.error(f"Command standard error: {result.stderr.strip()}")
            return result
        except subprocess.TimeoutExpired as e:
            logger.error(f"Timeout ({timeout_seconds}s) expired for command: {' '.join(command)}")
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"Error executing command {' '.join(command)}")
            if e.stdout: 
                logger.error(f"Output: {e.stdout.strip()}")
            if e.stderr:
                logger.error(f"Stderr: {e.stderr.strip()}")
            raise
        except FileNotFoundError:
            logger.error(f"Command '{command[0]}' not found. Make sure it is installed and in PATH.")
            raise


    def get_deployments(self) -> List[str]:
        self.run_command(["minikube", "-p", self.cluster_name, "profile", self.cluster_name], check=False)
        command = ["kubectl", "get", "deployments", "-n", self.namespace, "-o", "json"]
        result = self.run_command(command)
        deployments_data = json.loads(result.stdout)
        return [deployment["metadata"]["name"] for deployment in deployments_data.get("items", [])]


    def scale_deployment(self, deployment_name: str, replicas: int):
        logger.info(f"Scaling deployment {deployment_name} to {replicas} replicas in namespace {self.namespace}...")
        self.run_command(["minikube", "-p", self.cluster_name, "profile", self.cluster_name], check=False)
        command = [
            "kubectl", "scale", "deployment", deployment_name,
            "-n", self.namespace,
            "--replicas", str(replicas)
        ]
        self.run_command(command)
        
        if replicas > 0:
            logger.info(f"Waiting for deployment {deployment_name} to be ready after scaling to {replicas}...")
            rollout_command = [
                "kubectl", "rollout", "status", "deployment", deployment_name,
                "-n", self.namespace,
                "--timeout=1m" 
            ]
            try:
                self.run_command(rollout_command, timeout_seconds=310) 
            except subprocess.CalledProcessError as e: 
                logger.warning(f"Problem during 'rollout status' for {deployment_name} (might be timeout or rollout failure): {e.stderr if e.stderr else 'No specific stderr.'}")
            except subprocess.TimeoutExpired: 
                 logger.warning(f"'rollout status' for {deployment_name} exceeded subprocess timeout.")


    def modify_deployment_resources(self, deployment_name: str, resources_config: Dict):
        logger.info(f"--- Starting resource modification for deployment: {deployment_name} ---")
        
        # --- START SCALING 0-1 LOGIC ---
        
        logger.info(f"Step 1: Scaling {deployment_name} to 0 replicas...")
        self.scale_deployment(deployment_name, 0)
        
        logger.info(f"Step 2: Waiting for all pods to terminate for {deployment_name}...")
        # --- WAIT FOR POD TERMINATION ---
        label_selector = f"app={deployment_name}"
        max_wait_seconds = 120 # Wait at most 2 minutes for pod termination
        wait_interval = 5      # Check every 5 seconds
        time_waited = 0

        while time_waited < max_wait_seconds:
            try:
                self.run_command(["minikube", "-p", self.cluster_name, "profile", self.cluster_name], check=False)
                get_pods_cmd = [
                    "kubectl", "get", "pods", "-n", self.namespace,
                    "-l", label_selector,
                    "--no-headers", 
                    "-o", "custom-columns=NAME:.metadata.name"
                ]
                
                result = self.run_command(get_pods_cmd, check=False, timeout_seconds=30) 
                
                if not result.stdout.strip(): 
                    logger.info(f"All pods for {deployment_name} (with label '{label_selector}') have terminated.")
                    break
                else:
                    logger.info(f"Waiting for pods termination for {deployment_name} (found: {result.stdout.strip().replace('\n', ', ')}). Retrying in {wait_interval} seconds...")
                
                time.sleep(wait_interval)
                time_waited += wait_interval
            except subprocess.TimeoutExpired:
                logger.warning(f"Timeout while checking pods for {deployment_name}. Proceeding with patch anyway.")
                break
            except Exception as e:
                logger.warning(f"Error while waiting for pod termination for {deployment_name}, proceeding with patch: {e}")
                break 
        
        if time_waited >= max_wait_seconds:
            logger.warning(f"Maximum wait time reached ({max_wait_seconds}s) while waiting for pod termination for {deployment_name}. Some pods may still be active.")
        # --- END WAIT FOR POD TERMINATION ---

        logger.info(f"Step 3: Applying resource patch to {deployment_name}...")
        patch_payload = {
            "spec": {
                "template": {
                    "spec": {
                        "containers": [{
                            "name": deployment_name, 
                            "resources": {
                                "requests": {
                                    "cpu": resources_config["cpu"],
                                    "memory": resources_config["memory"]
                                },
                                "limits": { 
                                    "cpu": resources_config.get("limit_cpu", resources_config["cpu"]),
                                    "memory": resources_config.get("limit_memory", resources_config["memory"])
                                }
                            }
                        }]
                    }
                }
            }
        }
        patch_json = json.dumps(patch_payload)
        
        self.run_command(["minikube", "-p", self.cluster_name, "profile", self.cluster_name], check=False)
        patch_command = [
            "kubectl", "patch", "deployment", deployment_name,
            "-n", self.namespace,
            "--type=strategic",
            "--patch", patch_json
        ]
        
        self.run_command(patch_command)
        logger.info(f"Resources modified (patch sent) for {deployment_name}")
        
        logger.info(f"Step 4: Scaling {deployment_name} to 1 replica after patch...")
        self.scale_deployment(deployment_name, 1) 
        logger.info(f"--- Finished resource modification for deployment: {deployment_name} ---")


    def verify_resources(self, deployment_name: str, expected_resources_config: Dict):
        logger.info(f"Verifying resources for container '{deployment_name}' in deployment '{deployment_name}'...")
        self.run_command(["minikube", "-p", self.cluster_name, "profile", self.cluster_name], check=False)
        
        get_deployment_command = ["kubectl", "get", "deployment", deployment_name, "-n", self.namespace, "-o", "json"]
        result = self.run_command(get_deployment_command)
        deployment = json.loads(result.stdout)
        
        containers = deployment.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
        container_found = False
        for container in containers:
            
            if container.get("name") == deployment_name:
                container_found = True
                resources = container.get("resources", {})
                requests = resources.get("requests", {})
                limits = resources.get("limits", {})
                
                expected_cpu_req = expected_resources_config["cpu"]
                expected_mem_req = expected_resources_config["memory"]
                expected_cpu_lim = expected_resources_config.get("limit_cpu", expected_cpu_req)
                expected_mem_lim = expected_resources_config.get("limit_memory", expected_mem_req)

                current_cpu_req = requests.get("cpu")
                current_mem_req = requests.get("memory")
                current_cpu_lim = limits.get("cpu")
                current_mem_lim = limits.get("memory")

                errors = []
                if current_cpu_req != expected_cpu_req:
                    errors.append(f"CPU request: got '{current_cpu_req}', expected '{expected_cpu_req}'")
                if current_mem_req != expected_mem_req:
                    errors.append(f"Memory request: got '{current_mem_req}', expected '{expected_mem_req}'")
                if current_cpu_lim != expected_cpu_lim:
                    errors.append(f"CPU limit: got '{current_cpu_lim}', expected '{expected_cpu_lim}'")
                if current_mem_lim != expected_mem_lim:
                    errors.append(f"Memory limit: got '{current_mem_lim}', expected '{expected_mem_lim}'")
                
                if errors:
                    error_message = f"Resource verification failed for {deployment_name}: " + "; ".join(errors)
                    logger.error(error_message)
                    raise Exception(error_message)
                
                logger.info(f"Resources successfully verified for container '{deployment_name}' in '{deployment_name}'")
                return
        
        if not container_found:
            raise Exception(f"Container named '{deployment_name}' not found in deployment '{deployment_name}'. Verify assumptions on container name in patch.")


    def modify_resources(self):
        try:
            existing_deployments = self.get_deployments()
            
            if "containers" not in self.cluster_config or not isinstance(self.cluster_config["containers"], list):
                logger.error("The key 'containers' is missing or is not a LIST in the configuration.")
                return

            logger.info("Sorting services by priority: 'analyzer' will be processed last.")
            
            services_from_yaml = self.cluster_config["containers"]
            
            high_priority_services = []
            analyzer_service_config = None

            # Separate 'analyzer' from all other services
            for service_config in services_from_yaml:
                if service_config.get("name") == "analyzer":
                    analyzer_service_config = service_config
                else:
                    high_priority_services.append(service_config)

            # Build the final ordered list
            ordered_services = high_priority_services
            if analyzer_service_config:
                ordered_services.append(analyzer_service_config) # Add analyzer at the end
                logger.info("Found 'analyzer'. It will be processed after all other services.")
            
            logger.info("Starting resource modification process in the established priority order...")
            
            # Iterate over the ordered list
            for service_config in ordered_services:
                deployment_name = service_config.get("name")
                
                if not deployment_name:
                    logger.warning("Found an entry in 'containers' without the 'name' key. Skipping it.")
                    continue
                
                if deployment_name in existing_deployments:
                    logger.info(f"--- Starting modification for deployment '{deployment_name}' ---")
                    try:
                        self.modify_deployment_resources(deployment_name, service_config)
                        self.verify_resources(deployment_name, service_config)
                        logger.info(f"SUCCESS: Modification and rollout for '{deployment_name}' completed.")
                    except Exception as e:
                        logger.error(f"FAILURE during modification of '{deployment_name}'. This may be normal if resources are unavailable.")
                        logger.info("Continuing with the next service in the list...")
                        continue
                else:
                    logger.warning(f"Deployment '{deployment_name}' specified in configuration not found in namespace '{self.namespace}'. It will be skipped.")
            
            logger.info(f"Resource modification process completed for all services defined in cluster {self.cluster_name}!")
            
        except Exception as e:
            logger.error(f"General error during resource modification process for cluster {self.cluster_name}: {str(e)}")
            raise


class ClusterManager:
    def __init__(self, config_file: str):
        self.config = self._load_config(config_file)
        if not self.config:
            raise ValueError("Unable to load initial configuration.")
        self.modifiers: Dict[str, ResourceModifier] = {}

    def _load_config(self, config_file: str) -> Dict:
        try:
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file '{config_file}' not found.")
            raise 
        except yaml.YAMLError as ye:
            logger.error(f"Error parsing YAML file '{config_file}': {ye}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading configuration file: {str(e)}")
            raise


    def get_target_cluster_name_from_config(self) -> str:
        if not self.config or 'cluster' not in self.config:
            logger.error("The key 'cluster' (with Minikube cluster name) is missing in the configuration file or the file was not loaded.")
            return None
        
        cluster_name = self.config.get('cluster')
        if not cluster_name or not isinstance(cluster_name, str):
            logger.error("The value for 'cluster' in the configuration file is missing or not a string.")
            return None
        
        try:
            result = subprocess.run(
                ["minikube", "profile", "list", "-o", "json"],
                capture_output=True, text=True, check=True, timeout=30
            )
            profiles_data = json.loads(result.stdout)
            valid_profiles = [p.get('Name') for p in profiles_data.get('valid', []) if p.get('Name')]
            
            if cluster_name in valid_profiles:
                logger.info(f"The target cluster '{cluster_name}' from the configuration file is a valid Minikube profile.")
                return cluster_name
            else:
                logger.error(f"The target cluster '{cluster_name}' specified in the configuration file is not a valid/existing Minikube profile.")
                logger.info(f"Valid Minikube profiles found: {valid_profiles if valid_profiles else 'None'}")
                return None
        except FileNotFoundError:
            logger.error("Command 'minikube' not found. Make sure Minikube is installed and in PATH.")
            return None
        except subprocess.TimeoutExpired:
            logger.error("Timeout during execution of 'minikube profile list'. Minikube may be stuck.")
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"Error executing 'minikube profile list': {e.stderr.strip() if e.stderr else 'No specific error output.'}")
            return None
        except json.JSONDecodeError:
            logger.error("Error decoding JSON output from 'minikube profile list'.")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_target_cluster_name_from_config: {type(e).__name__} - {str(e)}")
            return None


    def modify_clusters_resources(self):
        target_cluster_name = self.get_target_cluster_name_from_config()
        
        if not target_cluster_name:
            logger.error("No valid target cluster found or specified in configuration. Cannot proceed with resource modification.")
            return

        logger.info(f"\nStarting resource modification for cluster: {target_cluster_name}")
        
        modifier = ResourceModifier(cluster_name=target_cluster_name, cluster_config=self.config)
        modifier.modify_resources()
        self.modifiers[target_cluster_name] = modifier 
        logger.info(f"ClusterManager: Resource modification completed for cluster {target_cluster_name}.")


def main():
    parser = argparse.ArgumentParser(description='Modify container resources in a Kubernetes cluster specified via YAML.')
    parser.add_argument('--config', type=str, required=True, help='Path to YAML configuration file.')
    
    args = parser.parse_args()
    
    try:
        manager = ClusterManager(config_file=args.config)
        manager.modify_clusters_resources()
        logger.info("Resource modification operation completed.")
    except FileNotFoundError:
        logger.error(f"Critical error: Configuration file '{args.config}' not found.")
        sys.exit(1)
    except ValueError as ve: 
        logger.error(f"Critical configuration or data error: {ve}")
        sys.exit(1)
    except subprocess.CalledProcessError as cpe:
        logger.error(f"A kubectl or minikube command failed critically: {cpe}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unhandled error occurred in main process: {type(e).__name__} - {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
