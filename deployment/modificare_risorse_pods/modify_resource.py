#!/usr/bin/env python3
import argparse
import subprocess
import logging
import time 
import os
import json
import yaml
from typing import Dict, List

# Configurazione logging
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

    def run_command(self, command: List[str], check: bool = True, timeout_seconds: int = 300) -> subprocess.CompletedProcess: # Aggiunto timeout di default
        try:
            logger.info(f"Esecuzione comando: {' '.join(command)}")
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
                    logger.info(f"Output del comando (anteprima): {output_preview}")
            
            if result.returncode != 0 and result.stderr:
                logger.error(f"Errore standard del comando: {result.stderr.strip()}")
            return result
        except subprocess.TimeoutExpired as e:
            logger.error(f"Timeout ({timeout_seconds}s) scaduto per il comando: {' '.join(command)}")
            
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"Errore nell'esecuzione del comando {' '.join(command)}")
            if e.stdout: 
                logger.error(f"Output: {e.stdout.strip()}")
            if e.stderr:
                logger.error(f"Stderr: {e.stderr.strip()}")
            raise
        except FileNotFoundError:
            logger.error(f"Comando '{command[0]}' non trovato. Assicurati che sia installato e nel PATH.")
            raise

    def get_deployments(self) -> List[str]:
        self.run_command(["minikube", "-p", self.cluster_name, "profile", self.cluster_name], check=False)
        command = ["kubectl", "get", "deployments", "-n", self.namespace, "-o", "json"]
        result = self.run_command(command)
        deployments_data = json.loads(result.stdout)
        return [deployment["metadata"]["name"] for deployment in deployments_data.get("items", [])]

    def scale_deployment(self, deployment_name: str, replicas: int):
        logger.info(f"Scalo il deployment {deployment_name} a {replicas} repliche nel namespace {self.namespace}...")
        self.run_command(["minikube", "-p", self.cluster_name, "profile", self.cluster_name], check=False)
        command = [
            "kubectl", "scale", "deployment", deployment_name,
            "-n", self.namespace,
            "--replicas", str(replicas)
        ]
        self.run_command(command)
        
        if replicas > 0:
            logger.info(f"Attendo che il deployment {deployment_name} sia pronto dopo lo scaling a {replicas}...")
            rollout_command = [
                "kubectl", "rollout", "status", "deployment", deployment_name,
                "-n", self.namespace,
                "--timeout=5m" 
            ]
            try:
                self.run_command(rollout_command, timeout_seconds=310) 
            except subprocess.CalledProcessError as e: 
                logger.warning(f"Problema durante 'rollout status' per {deployment_name} (potrebbe essere un timeout o un fallimento del rollout): {e.stderr if e.stderr else 'Nessun stderr specifico.'}")
            except subprocess.TimeoutExpired: 
                 logger.warning(f"'rollout status' per {deployment_name} ha superato il timeout di subprocess.")


    def modify_deployment_resources(self, deployment_name: str, resources_config: Dict):
        logger.info(f"--- Inizio modifica risorse per il deployment: {deployment_name} ---")
        
        # --- INIZIO LOGICA DI SCALING 0-1 ---
        
        logger.info(f"Passo 1: Scalo {deployment_name} a 0 repliche...")
        self.scale_deployment(deployment_name, 0)
        
        logger.info(f"Passo 2: Attendo la terminazione di tutti i pod per {deployment_name}...")
        # --- ATTESA TERMINAZIONE POD ---
        label_selector = f"app={deployment_name}"
        max_wait_seconds = 120 # Attendi al massimo 2 minuti per la terminazione dei pod
        wait_interval = 5      # Controlla ogni 5 secondi
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
                    logger.info(f"Tutti i pod per {deployment_name} (con etichetta '{label_selector}') sono terminati.")
                    break
                else:
                    logger.info(f"In attesa della terminazione dei pod per {deployment_name} (trovati: {result.stdout.strip().replace('\n', ', ')}). Riprovo tra {wait_interval} secondi...")
                
                time.sleep(wait_interval)
                time_waited += wait_interval
            except subprocess.TimeoutExpired:
                logger.warning(f"Timeout durante il controllo dei pod per {deployment_name}. Procedo comunque con il patch.")
                break
            except Exception as e:
                logger.warning(f"Errore durante l'attesa della terminazione dei pod per {deployment_name}, procedo con il patch: {e}")
                break 
        
        if time_waited >= max_wait_seconds:
            logger.warning(f"Timeout massimo raggiunto ({max_wait_seconds}s) durante l'attesa della terminazione dei pod per {deployment_name}. Alcuni pod potrebbero essere ancora attivi.")
        # --- FINE ATTESA TERMINAZIONE POD ---

        logger.info(f"Passo 3: Applico il patch delle risorse a {deployment_name}...")
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
        logger.info(f"Risorse modificate (patch inviato) per {deployment_name}")
        
        logger.info(f"Passo 4: Scalo {deployment_name} a 1 replica dopo il patch...")
        self.scale_deployment(deployment_name, 1) 
        logger.info(f"--- Fine modifica risorse per il deployment: {deployment_name} ---")


    def verify_resources(self, deployment_name: str, expected_resources_config: Dict):
        logger.info(f"Verifico le risorse per il container '{deployment_name}' nel deployment '{deployment_name}'...")
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
                    error_message = f"Verifica risorse fallita per {deployment_name}: " + "; ".join(errors)
                    logger.error(error_message)
                    raise Exception(error_message)
                
                logger.info(f"Risorse verificate con successo per il container '{deployment_name}' in '{deployment_name}'")
                return
        
        if not container_found:
            
            raise Exception(f"Container con nome '{deployment_name}' non trovato nel deployment '{deployment_name}'. Verificare l'assunzione sul nome del container nel patch.")


    def modify_resources(self):
        try:
            existing_deployments = self.get_deployments()
            
            if "containers" not in self.cluster_config or not isinstance(self.cluster_config["containers"], dict):
                logger.error("La chiave 'containers' non è presente o non è un dizionario nella configurazione.")
                return

            for deployment_name, resources_config in self.cluster_config["containers"].items():
                if deployment_name in existing_deployments:
                    logger.info(f"Trovato deployment '{deployment_name}' da modificare.")
                    self.modify_deployment_resources(deployment_name, resources_config) 
                    self.verify_resources(deployment_name, resources_config)
                else:
                    logger.warning(f"Deployment '{deployment_name}' specificato nella configurazione ma non trovato nel namespace '{self.namespace}'. Sarà saltato.")
            
            logger.info(f"Modifica delle risorse completata con successo per i deployment definiti nel cluster {self.cluster_name}!")
            
        except Exception as e:
            logger.error(f"Errore generale durante la modifica delle risorse per il cluster {self.cluster_name}: {str(e)}")
            raise

class ClusterManager:
    def __init__(self, config_file: str):
        self.config = self._load_config(config_file)
        if not self.config:
            raise ValueError("Impossibile caricare la configurazione iniziale.")
        self.modifiers: Dict[str, ResourceModifier] = {}

    def _load_config(self, config_file: str) -> Dict:
        try:
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"File di configurazione '{config_file}' non trovato.")
            raise 
        except yaml.YAMLError as ye:
            logger.error(f"Errore nel parsing del file YAML '{config_file}': {ye}")
            raise
        except Exception as e:
            logger.error(f"Errore imprevisto nel caricamento del file di configurazione: {str(e)}")
            raise

    def get_target_cluster_name_from_config(self) -> str:
        if not self.config or 'cluster' not in self.config:
            logger.error("La chiave 'cluster' (con il nome del cluster Minikube) non è presente nel file di configurazione o il file non è stato caricato.")
            return None
        
        cluster_name = self.config.get('cluster')
        if not cluster_name or not isinstance(cluster_name, str):
            logger.error("Il valore per 'cluster' nel file di configurazione è mancante o non è una stringa.")
            return None
        
        try:
            result = subprocess.run(
                ["minikube", "profile", "list", "-o", "json"],
                capture_output=True, text=True, check=True, timeout=30
            )
            profiles_data = json.loads(result.stdout)
            valid_profiles = [p.get('Name') for p in profiles_data.get('valid', []) if p.get('Name')]
            
            if cluster_name in valid_profiles:
                logger.info(f"Il cluster target '{cluster_name}' dal file di configurazione è un profilo Minikube valido.")
                return cluster_name
            else:
                logger.error(f"Il cluster target '{cluster_name}' specificato nel file di configurazione non è un profilo Minikube valido/esistente.")
                logger.info(f"Profili Minikube validi trovati: {valid_profiles if valid_profiles else 'Nessuno'}")
                return None
        except FileNotFoundError:
            logger.error("Comando 'minikube' non trovato. Assicurati che Minikube sia installato e nel PATH.")
            return None
        except subprocess.TimeoutExpired:
            logger.error("Timeout durante l'esecuzione di 'minikube profile list'. Minikube potrebbe essere bloccato.")
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"Errore durante l'esecuzione di 'minikube profile list': {e.stderr.strip() if e.stderr else 'Nessun output di errore specifico.'}")
            return None
        except json.JSONDecodeError:
            logger.error("Errore nel decodificare l'output JSON da 'minikube profile list'.")
            return None
        except Exception as e:
            logger.error(f"Errore imprevisto in get_target_cluster_name_from_config: {type(e).__name__} - {str(e)}")
            return None

    def modify_clusters_resources(self):
        target_cluster_name = self.get_target_cluster_name_from_config()
        
        if not target_cluster_name:
            logger.error("Nessun cluster target valido trovato o specificato nella configurazione. Impossibile procedere con la modifica delle risorse.")
            return

        logger.info(f"\nInizio modifica delle risorse per il cluster: {target_cluster_name}")
        
        modifier = ResourceModifier(cluster_name=target_cluster_name, cluster_config=self.config)
        modifier.modify_resources()
        self.modifiers[target_cluster_name] = modifier 
        logger.info(f"ClusterManager: Modifica risorse completata per il cluster {target_cluster_name}.")

def main():
    parser = argparse.ArgumentParser(description='Modifica le risorse dei container in un cluster Kubernetes specificato via YAML.')
    parser.add_argument('--config', type=str, required=True, help='Percorso del file di configurazione YAML.')
    
    args = parser.parse_args()
    
    try:
        manager = ClusterManager(config_file=args.config)
        manager.modify_clusters_resources()
        logger.info("Operazione di modifica risorse terminata.")
    except FileNotFoundError:
        logger.error(f"Errore critico: File di configurazione '{args.config}' non trovato.")
        sys.exit(1)
    except ValueError as ve: 
        logger.error(f"Errore critico di configurazione o dati: {ve}")
        sys.exit(1)
    except subprocess.CalledProcessError as cpe:
        logger.error(f"Un comando kubectl o minikube ha fallito in modo critico: {cpe}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Si è verificato un errore non gestito nel processo principale: {type(e).__name__} - {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
