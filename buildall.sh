#!/bin/bash

# Script per eseguire build_manifest.py, setupnodes.py, e build.sh in sequenza.

set -e


echo "--- Inizio del processo di build e setup ---"

# 1. Esegui build_manifest.py dentro la cartella deployment
echo ""
echo "Passo 1: Esecuzione di build_manifest.py..."
if [ -d "deployment" ]; then
    cd deployment
    if [ -f "build_manifest.py" ]; then
        python3 build_manifest.py --namespace brewery
        echo "build_manifest.py eseguito con successo."
        
    else
        echo "Errore: build_manifest.py non trovato in deployment2/"
        exit 1
    fi
else
    echo "Errore: La cartella deployment2/ non è stata trovata."
    exit 1
fi

# 2. Esegui setupnodes.py
echo ""
echo "Passo 2: Esecuzione di setupnodes.py..."

if [ -f "setup_nodes.py" ]; then
    python3 setup_nodes.py --config nodes_config.yaml
    echo "setup_nodes.py eseguito con successo."
else
    echo "Errore: setup_nodes.py non trovato."
    exit 1
fi


# 3. Esegui build.sh
echo ""
echo "Passo 3: Esecuzione di build.sh..."

if [ -f "build_image.sh" ]; then
    ./build_image.sh nodes_config.yaml
    echo "build.sh eseguito con successo."
else
    echo "Errore: build.sh non trovato."
    exit 1
fi

echo ""
echo "--- Processo completato con successo! ---"

kubectl apply -f k8s/deployment-brewery.yaml