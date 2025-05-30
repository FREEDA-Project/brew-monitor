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
            logger.info(f"Esecuzione comando: {' '.join(command)}")
            result = subprocess.run(
                command,
                check=check,
                capture_output=True,
                text=True
            )
            if result.stdout:
                logger.info(f"Output del comando: {result.stdout}")
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Errore nell'esecuzione del comando {' '.join(command)}")
            logger.error(f"Output: {e.output}")
            logger.error(f"Stderr: {e.stderr}")
            raise

    def check_prerequisites(self):
        logger.info("Verifico i prerequisiti...")
        # Verifica minikube
        try:
            self.run_command(["minikube", "version"])
        except subprocess.CalledProcessError:
            logger.error("Minikube non installato. Installa minikube prima di procedere.")
            raise

        # Verifica driver
        if self.driver == "docker":
            try:
                self.run_command(["docker", "version"])
            except subprocess.CalledProcessError:
                logger.error("Docker non installato. Installa Docker prima di procedere.")
                raise

    def create_cluster(self):
        logger.info(f"Creo il cluster {self.cluster_name}...")
        
        # Get the first node's configuration for the control plane
        first_node = next(iter(self.cluster_config['nodes'].values()))
        memory = str(first_node['capabilities']['ram'] * 1024)  # Convert GB to MB
        cpus = str(first_node['capabilities']['cpu'])
        
        # Prima elimina il cluster se esiste
        try:
            logger.info(f"Elimino il cluster {self.cluster_name} se esiste...")
            self.run_command(["minikube", "delete", "-p", self.cluster_name], check=False)
        except Exception as e:
            logger.warning(f"Errore durante la pulizia del cluster esistente: {str(e)}")
        
        # Costruisci il comando base
        command = [
            "minikube", "start",
            "-p", self.cluster_name,
            "--cpus", cpus,
            "--memory", memory,
            "--nodes", str(self.num_nodes),
            "--driver", self.driver
        ]
        
        logger.info(f"Comando per creare il cluster: {' '.join(command)}")
        
        # Esegui il comando
        try:
            self.run_command(command)
            self.nodes.append(self.cluster_name)
        except subprocess.CalledProcessError as e:
            logger.error(f"Errore durante la creazione del cluster: {str(e)}")
            logger.error(f"Output completo: {e.output}")
            raise
        
        # Ottieni la lista dei nodi
        nodes = self.get_node_names()
        
        # Configura i nodi worker
        for i, node_name in enumerate(nodes[1:], 1):
            logger.info(f"Configurando il worker node {node_name}...")
            # Aggiungi l'etichetta worker
            self.label_worker_nodes(node_name)
            # Aggiungi il nome del nodo alla lista
            worker_name = list(self.cluster_config['nodes'].keys())[i]
            self.nodes.append(worker_name)

    def get_node_names(self) -> List[str]:
        command = ["kubectl", "get", "nodes", "-o", "json"]
        result = self.run_command(command)
        nodes = json.loads(result.stdout)
        
        if len(nodes["items"]) == 0:
            raise Exception("Nessun nodo trovato")
        
        return [node["metadata"]["name"] for node in nodes["items"]]

    def label_worker_nodes(self, node_name: str):
        logger.info(f"Assegno il ruolo 'worker' al nodo {node_name}...")
        
        command = [
            "kubectl", "label", "nodes", node_name, "node-role.kubernetes.io/worker=worker", "--overwrite"
        ]
    
        self.run_command(command)
        logger.info(f"Ruolo 'worker' assegnato a {node_name}")

    def verify_cluster(self):
        logger.info("Verifico lo stato del cluster...")
        
        # Verifica nodi
        command = ["kubectl", "get", "nodes", "-o", "json"]
        result = self.run_command(command)
        nodes = json.loads(result.stdout)
        
        if len(nodes["items"]) != self.num_nodes:
            raise Exception(f"Numero di nodi non corretto. Attesi: {self.num_nodes}, Trovati: {len(nodes['items'])}")
        
        # Verifica stato dei nodi
        for node in nodes["items"]:
            node_name = node["metadata"]["name"]
            conditions = {c["type"]: c["status"] for c in node["status"]["conditions"]}
            
            if conditions.get("Ready") != "True":
                raise Exception(f"Nodo {node_name} non pronto")
            
            # Get node resources
            capacity = node["status"]["capacity"]
            logger.info(f"Nodo {node_name} pronto - CPU: {capacity['cpu']}, Memoria: {capacity['memory']}")

    def setup(self):
        try:
            self.check_prerequisites()
            self.create_cluster()
            self.verify_cluster()
            
            logger.info(f"\nCluster {self.cluster_name} configurato con successo!")
            logger.info(f"Nodi creati: {', '.join(self.nodes)}")
            
            # Mostra informazioni utili
            logger.info("Informazioni sul cluster:")
            result = self.run_command(["kubectl", "cluster-info"])
            logger.info(result.stdout)

            logger.info("Nodi del cluster:")
            result = self.run_command(["kubectl", "get", "nodes", "--show-labels"])
            logger.info(result.stdout)
            
        except Exception as e:
            logger.error(f"Errore durante la configurazione del cluster: {str(e)}")
            self.cleanup()
            raise

    def cleanup(self): 
        logger.info("Pulizia del cluster...")
        try:
            self.run_command(["minikube", "delete", "-p", self.cluster_name], check=False)
        except Exception as e:
            logger.error(f"Errore durante la pulizia: {str(e)}")

class ClusterManager:
    def __init__(self, config_file: str):
        self.config = self._load_config(config_file)
        self.clusters = {}

    def _load_config(self, config_file: str) -> Dict:
        try:
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Errore nel caricamento del file di configurazione: {str(e)}")
            raise

    def setup_clusters(self):
        cluster_name=self.config['name']
        
        logger.info(f"\nConfigurazione del cluster {cluster_name}...")
        cluster = MinikubeCluster(
            cluster_name=cluster_name,
            cluster_config=self.config
            
        )
    
        cluster.setup()
        self.clusters[cluster_name] = cluster

    def cleanup_clusters(self):
        for cluster_name, cluster in self.clusters.items():
            logger.info(f"\nPulizia del cluster {cluster_name}...")
            cluster.cleanup()

def main():
    parser = argparse.ArgumentParser(description='Configura cluster Kubernetes multi-nodo con Minikube')
    parser.add_argument('--config', type=str, required=True, help='Percorso del file di configurazione YAML')
    parser.add_argument('--delete', action='store_true', help='Elimina i cluster esistenti')
    
    args = parser.parse_args()
    
    manager = ClusterManager(config_file=args.config)
    
    if args.delete:
        manager.cleanup_clusters()
    else:
        manager.setup_clusters()

if __name__ == "__main__":
    main() 