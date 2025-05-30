#!/bin/bash


if [ -z "$1" ]; then
  echo "Errore: Devi specificare il percorso del file YAML come argomento." >&2
  echo "Uso: $0 <percorso_file_yaml>" >&2
  exit 1
fi

YAML_FILE="$1" 

CLUSTER_NAME=$(python3 -c "
import yaml
import sys

filename = sys.argv[1]

try:
    with open(filename, 'r') as f:
        config = yaml.safe_load(f)
        if config and isinstance(config, dict) and 'name' in config:
            cluster_name = config['name']
            print(cluster_name) # Stampa il nome del cluster su stdout
        else:
            print(f\"Errore: La chiave 'name' non è presente al livello principale nel file '{filename}' o il file è vuoto/malformato.\", file=sys.stderr)
            sys.exit(1) # Esce con errore
except FileNotFoundError:
    print(f\"Errore: File '{filename}' non trovato.\", file=sys.stderr)
    sys.exit(1)
except yaml.YAMLError as e:
    print(f\"Errore durante il parsing del file YAML '{filename}': {e}\", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f\"Errore Python imprevisto: {e}\", file=sys.stderr)
    sys.exit(1)
" "$YAML_FILE") 

# Controlla se python3 ha avuto successo e se CLUSTER_NAME è stato popolato
if [ $? -eq 0 ] && [ -n "$CLUSTER_NAME" ]; then
  echo "Nome del cluster letto: $CLUSTER_NAME"
  
else
  echo "Impossibile leggere il nome del cluster dal file YAML. Controllare i messaggi di errore."
  exit 1 
fi



echo "-----------------------------------------------------"
echo "Build delle immagini per il cluster: $CLUSTER_NAME"
echo "-----------------------------------------------------"

    # Build delle immagini
minikube image build -p "$CLUSTER_NAME" --all -t brewery-gateway:high ../src/gateway/high
minikube image build -p "$CLUSTER_NAME" --all -t brewery-aggregator:high ../src/aggregator/high
minikube image build -p "$CLUSTER_NAME" --all -t brewery-data-gather:high ../src/data-gather/high
minikube image build -p "$CLUSTER_NAME" --all -t brewery-analyzer:high ../src/analyzer/high

minikube image build -p "$CLUSTER_NAME" --all -t brewery-gateway:low ../src/gateway/low
minikube image build -p "$CLUSTER_NAME" --all -t brewery-aggregator:low ../src/aggregator/low
minikube image build -p "$CLUSTER_NAME" --all -t brewery-data-gather:low ../src/data-gather/low


echo "Immagini buildate con successo per il cluster $CLUSTER_NAME nell'ambiente Docker di minikube"


echo "-----------------------------------------------------"
echo "Tutte le build per tutti i cluster sono state completate."
echo "-----------------------------------------------------"