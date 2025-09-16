# Brewery Application / Applicazione Brewery

[English](#english) | [Italiano](#italiano)

## English

### Overview
This is a microservices-based brewery monitoring application running on Kubernetes (Minikube). The application consists of multiple services that collect, aggregate, and analyze brewing data.

### Service Versions (High/Low)
Each service in the application has two versions:

#### High Version
- **Gateway**: Provides access to both aggregator and analyzer endpoints
  - `/api/aggregator/current`: Get current data
  - `/api/analyzer/stats`: Get statistical analysis
- **Data Gather**: Stores data in MongoDB and provides historical data access
- **Aggregator**: Aggregates data from multiple data-gather instances
- **Analyzer**: Performs statistical analysis on historical data

#### Low Version
- **Gateway**: Provides access only to aggregator endpoint
  - `/api/aggregator/current`: Get current data
- **Data Gather**: Simple in-memory storage with no persistence
- **Aggregator**: Direct data access from data-gather instances
- **Analyzer**: Not available in low version

### Project Structure
```
.
├── deployment/              # Deployment and testing tools
│   ├── build_image.sh      # Script to build Docker images
│   ├── build_k8s_manifest.py # Script to generate K8s manifests
│   ├── load_brewery.py     # Load testing script
│   ├── servizi.csv         # Service configuration
│   └── k8s/               # Generated Kubernetes manifests
│       └── deployment.yaml
│
└── src/                    # Application source code
    ├── aggregator/        # Aggregator service
    │   ├── high/
    │   └── low/
    ├── analyzer/         # Analyzer service
    │   ├── high/
    │   └── low/
    ├── data-gather/      # Data gathering service
    │   ├── high/
    │   └── low/
    └── gateway/          # Gateway service
        ├── high/
        └── low/
```



### Prerequisites
- Docker
- Minikube
- kubectl
- Python 3.x


### Setup Instructions

1. **Build Images**
```bash
# Navigate to the deployment directory
cd deployment

# Make the build script executable
chmod +x build_image.sh

# Build all images
./build_image.sh
```

2. **Configure Services**
Create a `servizi.csv` file with the following structure:
```csv
service,flavour
gateway,high
data-gather-pluto,high
data-gather-pippo,high
aggregator,high
analyzer,high
mongodb-history,high
mongodb-batch,high
```

3. **Generate Kubernetes Manifests**
```bash
python3 build_k8s_manifest.py
```
This will generate the `k8s/deployment.yaml` file based on your CSV configuration.

4. **Deploy to Kubernetes**
```bash
kubectl apply -f k8s/deployment.yaml
```

5. **Load Testing**
To test the application, use the load testing script:

```bash
# Get the service URL
minikube service gateway -n brewery --url

# Run load test (replace URL with the one from previous command)
python load_brewery.py --url http://192.168.49.2:30000

# Test high gateway endpoints
python load_brewery.py --url http://192.168.49.2:30000 --high

# Customize test duration and interval
python load_brewery.py --url http://192.168.49.2:30000 --high --duration 10 --interval 0.5
```

### Load Testing Parameters
- `--url`: Gateway service URL (required)
- `--high`: Test high gateway endpoints (optional)
- `--interval`: Time between requests in seconds (default: 1.0)
- `--duration`: Test duration in minutes (default: 5)

### Monitoring
- Check logs: `kubectl logs -n brewery <pod-name>`
- View services: `kubectl get services -n brewery`
- View pods: `kubectl get pods -n brewery`

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
```
.
├── deployment/              # Strumenti di deployment e testing
│   ├── build_image.sh      # Script per buildare le immagini Docker
│   ├── build_k8s_manifest.py # Script per generare i manifest K8s
│   ├── load_brewery.py     # Script per il test di carico
│   ├── servizi.csv         # Configurazione dei servizi
│   └── k8s/               # Manifest Kubernetes generati
│       └── deployment.yaml
│
└── src/                    # Codice sorgente dell'applicazione
    ├── aggregator/        # Servizio aggregator
    │   ├── high/
    │   └── low/
    ├── analyzer/         # Servizio analyzer
    │   ├── high/
    │   └── low/
    ├── data-gather/      # Servizio di raccolta dati
    │   ├── high/
    │   └── low/
    └── gateway/          # Servizio gateway
        ├── high/
        └── low/
```


### Prerequisiti
- Docker
- Minikube
- kubectl
- Python 3.x
- pip

### Istruzioni di Setup

1. **Build delle Immagini**
```bash
# Naviga nella cartella deployment
cd deployment

# Rendi eseguibile lo script di build
chmod +x build_image.sh

# Build di tutte le immagini
./build_image.sh
```

2. **Configurazione dei Servizi**
Crea un file `servizi.csv` con la seguente struttura:
```csv
service,flavour
gateway,high
data-gather-pluto,high
data-gather-pippo,high
aggregator,high
analyzer,high
mongodb-history,high
mongodb-batch,high
```

3. **Generazione dei Manifest Kubernetes**
```bash
python3 build_k8s_manifest.py
```
Questo genererà il file `k8s/deployment.yaml` basato sulla tua configurazione CSV che si troverà nella cartella deployment.

4. **Deploy su Kubernetes**
```bash
kubectl apply -f deployment/k8s/deployment.yaml
```

5. **Test di Carico**
Per testare l'applicazione, usa lo script di load testing:

```bash
# Ottieni l'URL del servizio
minikube service gateway -n brewery --url

# Esegui il test di carico (sostituisci URL con quello ottenuto dal comando precedente)
python load_brewery.py --url http://192.168.49.2:30000

# Testa gli endpoint del gateway high
python load_brewery.py --url http://192.168.49.2:30000 --high

# Personalizza durata e intervallo del test
python load_brewery.py --url http://192.168.49.2:30000 --high --duration 10 --interval 0.5
```

### Parametri del Test di Carico
- `--url`: URL del servizio gateway (obbligatorio)
- `--high`: Testa gli endpoint del gateway high (opzionale)
- `--interval`: Intervallo tra le richieste in secondi (default: 1.0)
- `--duration`: Durata del test in minuti (default: 5)

### Monitoraggio
- Controlla i log: `kubectl logs -n brewery <pod-name>`
- Visualizza i servizi: `kubectl get services -n brewery`
- Visualizza i pod: `kubectl get pods -n brewery` 