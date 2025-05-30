# Brewery Application / Applicazione Brewery

[English](#english) | [Italiano](#italiano)

## English
### Overview
This is a microservices-based brewery monitoring application that runs on Kubernetes (Minikube). The application consists of several services that collect, aggregate, and analyze production data.

### Service Versions (High/Low)
Each service in the application has two versions:

#### High Version
- **Gateway**: Provides access to both aggregator and analyzer endpoints
  - `/api/aggregator/current`: Get current data
  - `/api/analyzer/stats`: Get statistical analysis
- **Data Gather**: Stores data in MongoDB and provides access to historical data
- **Aggregator**: Aggregates data from multiple data-gather instances
- **Analyzer**: Performs statistical analysis on historical data

#### Low Version
- **Gateway**: Provides access only to the aggregator endpoint
  - `/api/aggregator/current`: Get current data
- **Data Gather**: Simple in-memory storage without persistence
- **Aggregator**: Direct access to data from data-gather instances
- **Analyzer**: Not available in the low version

### Project Structure
The project is organized as follows (assuming the root is `src-prova/`):

.
├── buildall.sh              # Master script to automate cluster setup, image building, and deployment
│
├── deployment/              # Deployment, setup, and testing tools
│   ├── build_image.sh       # Script to build Docker images for a specific cluster configuration
│   ├── build_manifest.py    # Script to generate K8s manifests for a namespace
│   ├── setup_nodes.py       # Script to configure a Minikube cluster based on a node configuration file
│   ├── load_brewery.py      # Script for load testing
│   ├── servizi.csv          # Service configuration (service,flavour,node) for manifest generation
│   ├── nodes_config.yaml    # Cluster node configuration (name, nodes, capabilities)
│   ├── app_case_study.yaml  # Advanced: Configuration for application component study
│   ├── template.j2          # Jinja2 template for K8s manifests
│   ├── k8s/                 # Directory for generated Kubernetes manifests (e.g., deployment-.yaml)
│   └── modificare_risorse_pods/ # Tools to modify pod resources post-deployment
│       ├── modify_resource.py # Script to modify pod resources (CPU/memory)
│       └── pods_config_resource.yaml # Pod resource configuration (cluster, namespace, containers)
│
└── src/                     # Application source code (microservices)
├── aggregator/          # Aggregator service (high/low flavour)
├── analyzer/            # Analyzer service (high flavour)
├── data-gather/         # Data collection service (high/low flavour)
└── gateway/             # Gateway service (high/low flavour)


### Prerequisites
- Docker
- Minikube
- kubectl
- Python 3.x

### Setup Instructions

You have two main options for setting up and deploying the application:

#### Option 1: Automated Setup using `buildall.sh` (Recommended)
The `buildall.sh` script, located in the `src-prova/` directory, automates most of the setup process.

1.  **Navigate to the `src-prova/` directory.**
    ```bash
    cd /path/to/your/project/src-prova/
    ```
2.  **Configure the necessary files in the `deployment/` directory (Note: the user prompt said `deployment2/` but the structure shows `deployment/`. I will use `deployment/` as per the structure):**
    * **`deployment/nodes_config.yaml`**: Define your Minikube cluster structure (name, number of nodes, CPU/RAM per node).
        
    * **`deployment/servizi.csv`**: List the services, their flavours, and optionally the node they should be scheduled on. The `buildall.sh` script uses `brewery` as the namespace, and the node name should be taken from the `nodes_config.yaml` file. Example:
        ```csv
        service,flavour,node
        gateway,high,master-m02
        data-gather-pluto,high,master-m02
        data-gather-pino,low,master-m03
        aggregator,high,master-m02
        analyzer,high,master-m02
        mongodb-history,high,master 
        mongodb-batch-pluto,high,master
        mongodb-batch-pino,high,master
        ```
3.  **Make the `buildall.sh` script executable:**
    ```bash
    chmod +x buildall.sh
    ```
4.  **Run the script:**
    ```bash
    ./buildall.sh
    ```
    This script will do the following:
    * Change directory to `deployment/`.
    * Execute `python3 setup_nodes.py --config nodes_config.yaml` to create/configure your Minikube cluster.
    * Execute `python3 build_manifest.py --namespace brewery` to generate Kubernetes deployment files (e.g., `deployment/k8s/deployment-brewery.yaml`).
    * Execute `./build_image.sh nodes_config.yaml` to build all necessary Docker images in the Minikube environment.
    * Finally, execute `kubectl apply -f deployment/k8s/deployment-brewery.yaml` to deploy the application to the `brewery` namespace.

#### Option 2: Manual Step-by-Step Setup

1.  **Navigate to the `deployment/` directory:**
    ```bash
    cd /path/to/your/project/src-prova/deployment/
    ```
2.  **Configure Cluster Nodes:**
    * Create or modify `nodes_config.yaml`. This file defines your Minikube cluster/profile name and the specifications for each node (CPU, RAM).
    
3.  **Setup Minikube Cluster:**
    * Run the `setup_nodes.py` script, providing your node configuration:
        ```bash
        python3 setup_nodes.py --config nodes_config.yaml
        ```
4.  **Build Docker Images:**
    * The `build_image.sh` script builds all service images (high and low flavour) within your Minikube's Docker daemon. It uses the cluster name defined in your `nodes_config.yaml`.
    * Make it executable:
        ```bash
        chmod +x build_image.sh
        ```
    * Run the script:
        ```bash
        ./build_image.sh nodes_config.yaml
        ```
5.  **Configure Services for Kubernetes Manifests:**
    * Create or modify `servizi.csv`. This CSV file lists each microservice, its desired flavour (`high` or `low`), and an optional third column specifying the Kubernetes node name for scheduling (using `nodeAffinity`).
    
6.  **Generate Kubernetes Manifests:**
    * Run `build_manifest.py` to generate the `deployment-<namespace>.yaml` file in the `k8s/` subdirectory. You must specify a namespace.
        ```bash
        python3 build_manifest.py --namespace your-chosen-namespace
        ```
        For example, to use `brewery` as the namespace:
        ```bash
        python3 build_manifest.py --namespace brewery
        ```
        This will create `k8s/deployment-brewery.yaml`.

7.  **Deploy to Kubernetes:**
    * Apply the generated manifest file:
        ```bash
        kubectl apply -f k8s/deployment-your-chosen-namespace.yaml
        ```
        For example:
        ```bash
        kubectl apply -f k8s/deployment-brewery.yaml
        ```

### Modify Pod Resources (Optional)
After deployment, you can modify the CPU and memory resources allocated to your pods using the `modify_resource.py` script.

1.  **Navigate to the `deployment/` directory (if not already there).**
2.  **Configure `modificare_risorse_pods/pods_config_resource.yaml`:**
    * Specify the Minikube cluster profile name, the namespace, and the desired CPU/memory requests/limits for each container.
    
3.  **Run the script:**
    ```bash
    python3 modificare_risorse_pods/modify_resource.py --config modificare_risorse_pods/pods_config_resource.yaml
    ```

### Load Testing
To test the application, use the `load_brewery.py` script located in the `deployment/` directory.

1.  **Get the Gateway Service URL:**
    * Make sure to specify the correct namespace.
    ```bash
    minikube service gateway -n your-chosen-namespace --url
    ```
    (e.g., `minikube service gateway -n brewery --url`)

2.  **Run the Load Test:**
    * Replace the URL with the one obtained from the previous command.
    ```bash
    python3 deployment/load_brewery.py --url http://<minikube-ip>:<nodeport>
    ```
    * To test the high gateway endpoints (including `/api/analyzer/stats`):
    ```bash
    python3 deployment/load_brewery.py --url http://<minikube-ip>:<nodeport> --high
    ```
    * To customize the test duration (in minutes) and the interval between requests (in seconds):
    ```bash
    python3 deployment/load_brewery.py --url http://<minikube-ip>:<nodeport> --high --duration 10 --interval 0.5
    ```

### Load Test Parameters
- `--url`: Gateway service URL (required).
- `--high`: Test high gateway endpoints (optional, includes analyzer).
- `--interval`: Interval between requests in seconds (default: 1.0).
- `--duration`: Test duration in minutes (default: 5).

### Monitoring
Use `kubectl` with the correct namespace:
- Check logs: `kubectl logs -n your-chosen-namespace <pod-name>`
- View services: `kubectl get services -n your-chosen-namespace`
- View pods: `kubectl get pods -n your-chosen-namespace -o wide`
- Describe pods for detailed status: `kubectl describe pod -n your-chosen-namespace <pod-name>`

---

## Italiano

### Panoramica
Questa è un'applicazione di monitoraggio per birrifici basata su microservizi che gira su Kubernetes (Minikube). L'applicazione è composta da diversi servizi che raccolgono, aggregano e analizzano i dati della produzione.

### Versioni dei Servizi (High/Low)
Ogni servizio dell'applicazione ha due versioni:

#### Versione High
- **Gateway**: Fornisce accesso sia agli endpoint dell'aggregator che dell'analyzer
  - `/api/aggregator/current`: Ottieni i dati correnti
  - `/api/analyzer/stats`: Ottieni l'analisi statistica
- **Data Gather**: Memorizza i dati in MongoDB e fornisce accesso ai dati storici
- **Aggregator**: Aggrega i dati da più istanze data-gather
- **Analyzer**: Esegue analisi statistiche sui dati storici

#### Versione Low
- **Gateway**: Fornisce accesso solo all'endpoint dell'aggregator
  - `/api/aggregator/current`: Ottieni i dati correnti
- **Data Gather**: Memorizzazione semplice in memoria senza persistenza
- **Aggregator**: Accesso diretto ai dati dalle istanze data-gather
- **Analyzer**: Non disponibile nella versione low

### Struttura del Progetto
Il progetto è organizzato come segue (assumendo che la root sia `src-prova/`):
```
. 
├── buildall.sh              # Script master per automatizzare setup del cluster, build delle immagini e deploy
│
├── deployment/             # Strumenti di deployment, setup e testing
│   ├── build_image.sh       # Script per buildare le immagini Docker per una specifica configurazione di cluster
│   ├── build_manifest.py    # Script per generare i manifest K8s per un namespace
│   ├── setup_nodes.py       # Script per configurare un cluster Minikube basato su un file di configurazione dei nodi
│   ├── load_brewery.py      # Script per il test di carico
│   ├── servizi.csv          # Configurazione dei servizi (service,flavour,node) per la generazione dei manifest
│   ├── nodes_config.yaml    # Configurazione dei nodi del cluster (name, nodes, capabilities)
│   ├── app_case_study.yaml  # Avanzato: Configurazione per studio dei componenti applicativi
│   ├── template.j2          # Template Jinja2 per i manifest K8s
│   ├── k8s/                 # Directory per i manifest Kubernetes generati (es. deployment-<namespace>.yaml)
│   └── modificare_risorse_pods/ # Strumenti per modificare le risorse dei pod post-deployment
│       ├── modify_resource.py # Script per modificare le risorse dei pod (CPU/memoria)
│       └── pods_config_resource.yaml # Configurazione risorse pod (cluster, namespace, containers)
│
└── src/                     # Codice sorgente dell'applicazione (microservizi)
    ├── aggregator/        # Servizio aggregator (flavour high/low)
    ├── analyzer/          # Servizio analyzer (flavour high)
    ├── data-gather/       # Servizio di raccolta dati (flavour high/low)
    └── gateway/           # Servizio gateway (flavour high/low)
```

### Prerequisiti
- Docker
- Minikube
- kubectl
- Python 3.x


### Istruzioni di Setup

Hai due opzioni principali per configurare e deployare l'applicazione:

#### Opzione 1: Setup Automatizzato usando `buildall.sh` (Consigliato)
Lo script `buildall.sh`, situato nella directory `src-prova/`, automatizza la maggior parte del processo di setup.

1.  **Naviga nella directory `src-prova/`.**
    ```bash
    cd /percorso/al/tuo/progetto/src-prova/
    ```
2.  **Configura i file necessari nella directory `deployment2/`:**
    *   **`deployment2/nodes_config.yaml`**: Definisci la struttura del tuo cluster Minikube (nome, numero di nodi, CPU/RAM per nodo).
        
    *   **`deployment2/servizi.csv`**: Elenca i servizi, i loro flavour e opzionalmente il nodo su cui dovrebbero essere schedulati. Lo script `buildall.sh` usa `brewery` come namespace e come nome del node bisogna prendere quello nel file nodes_config.yaml. Esempio:
        ```csv
        service,flavour,node
        gateway,high,master-m02
        data-gather-pluto,high,master-m02
        data-gather-pino,low,master-m03
        aggregator,high,master-m02
        analyzer,high,master-m02
        mongodb-history,high,master 
        mongodb-batch-pluto,high,master
        mongodb-batch-pino,high,master
        ```
3.  **Rendi eseguibile lo script `buildall.sh`:**
    ```bash
    chmod +x buildall.sh
    ```
4.  **Esegui lo script:**
    ```bash
    ./buildall.sh
    ```
    Questo script farà quanto segue:
    *   Cambierà directory in `deployment2/`.
    *   Eseguirà `python3 setup_nodes.py --config nodes_config.yaml` per creare/configurare il tuo cluster Minikube.
    *   Eseguirà `python3 build_manifest.py --namespace brewery` per generare i file di deployment Kubernetes (es. `deployment2/k8s/deployment-brewery.yaml`).
    *   Eseguirà `./build_image.sh nodes_config.yaml` per buildare tutte le immagini Docker necessarie nell'ambiente Minikube.
    *   Infine, eseguirà `kubectl apply -f deployment2/k8s/deployment-brewery.yaml` per deployare l'applicazione nel namespace `brewery`.

#### Opzione 2: Setup Manuale Passo-Passo

1.  **Naviga nella directory `deployment2/`:**
    ```bash
    cd /percorso/al/tuo/progetto/src-prova/deployment2/
    ```
2.  **Configura Nodi del Cluster:**
    *   Crea o modifica `nodes_config.yaml`. Questo file definisce il nome del tuo cluster/profilo Minikube e le specifiche per ogni nodo (CPU, RAM).
   
3.  **Setup Cluster Minikube:**
    *   Esegui lo script `setup_nodes.py`, fornendo la tua configurazione dei nodi:
        ```bash
        python3 setup_nodes.py --config nodes_config.yaml
        ```
4.  **Build Immagini Docker:**
    *   Lo script `build_image.sh` builda tutte le immagini dei servizi (flavour high e low) all'interno del demone Docker del tuo Minikube. Utilizza il nome del cluster definito nel tuo `nodes_config.yaml`.
    *   Rendilo eseguibile:
        ```bash
        chmod +x build_image.sh
        ```
    *   Esegui lo script:
        ```bash
        ./build_image.sh nodes_config.yaml
        ```
5.  **Configura Servizi per Manifest Kubernetes:**
    *   Crea o modifica `servizi.csv`. Questo file CSV elenca ogni microservizio, il suo flavour desiderato (`high` o `low`), e una terza colonna opzionale che specifica il nome del nodo Kubernetes per lo scheduling (usando `nodeAffinity`).
    
6.  **Genera Manifest Kubernetes:**
    *   Esegui `build_manifest.py` per generare il file `deployment-<namespace>.yaml` nella sottodirectory `k8s/`. Devi specificare un namespace.
        ```bash
        python3 build_manifest.py --namespace tuo-namespace-scelto
        ```
        Ad esempio, per usare `brewery` come namespace:
        ```bash
        python3 build_manifest.py --namespace brewery
        ```
        Questo creerà `k8s/deployment-brewery.yaml`.

7.  **Deploy su Kubernetes:**
    *   Applica il file manifest generato:
        ```bash
        kubectl apply -f k8s/deployment-tuo-namespace-scelto.yaml
        ```
        Ad esempio:
        ```bash
        kubectl apply -f k8s/deployment-brewery.yaml
        ```

### Modifica Risorse Pod (Opzionale)
Dopo il deployment, puoi modificare le risorse CPU e memoria allocate ai tuoi pod usando lo script `modify_resource.py`.

1.  **Naviga nella directory `deployment2/` (se non ci sei già).**
2.  **Configura `modificare_risorse_pods/pods_config_resource.yaml`:**
    *   Specifica il nome del profilo cluster Minikube, il namespace, e le richieste/limiti CPU/memoria desiderati per ogni container.
    
3.  **Esegui lo script:**
    ```bash
    python3 modificare_risorse_pods/modify_resource.py --config modificare_risorse_pods/pods_config_resource.yaml
    ```

### Test di Carico
Per testare l'applicazione, usa lo script `load_brewery.py` situato nella directory `deployment2/`.

1.  **Ottieni l'URL del Servizio Gateway:**
    *   Assicurati di specificare il namespace corretto.
    ```bash
    minikube service gateway -n tuo-namespace-scelto --url
    ```
    (es. `minikube service gateway -n brewery --url`)

2.  **Esegui il Test di Carico:**
    *   Sostituisci l'URL con quello ottenuto dal comando precedente.
    ```bash
    python3 deployment2/load_brewery.py --url http://<minikube-ip>:<nodeport>
    ```
    *   Per testare gli endpoint del gateway high (incluso `/api/analyzer/stats`):
    ```bash
    python3 deployment2/load_brewery.py --url http://<minikube-ip>:<nodeport> --high
    ```
    *   Per personalizzare la durata del test (in minuti) e l'intervallo tra le richieste (in secondi):
    ```bash
    python3 deployment2/load_brewery.py --url http://<minikube-ip>:<nodeport> --high --duration 10 --interval 0.5
    ```

### Parametri del Test di Carico
- `--url`: URL del servizio gateway (obbligatorio).
- `--high`: Testa gli endpoint del gateway high (opzionale, include analyzer).
- `--interval`: Intervallo tra le richieste in secondi (default: 1.0).
- `--duration`: Durata del test in minuti (default: 5).

### Monitoraggio
Usa `kubectl` con il namespace corretto:
- Controlla i log: `kubectl logs -n tuo-namespace-scelto <pod-name>`
- Visualizza i servizi: `kubectl get services -n tuo-namespace-scelto`
- Visualizza i pod: `kubectl get pods -n tuo-namespace-scelto -o wide`
- Descrivi i pod per stato dettagliato: `kubectl describe pod -n tuo-namespace-scelto <pod-name>`