import csv
from jinja2 import Environment, FileSystemLoader
import os
import sys
import logging
import argparse

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Dictionary of services with their parameters
SERVICES = {
    "gateway": {"port": 5000, "type": "NodePort", "nodePort": 30000},
    "data-gather": {"port": 5001, "type": "ClusterIP"},
    "aggregator": {"port": 5002, "type": "ClusterIP"},
    "analyzer": {"port": 5003, "type": "ClusterIP"},
    "mongodb-history": {"port": 27017, "type": "ClusterIP"},
    "mongodb-batch": {"port": 27017, "type": "ClusterIP"}
}

TEMPLATE_FILE = "template_affinityhard.j2"
CSV_FILE = "services.csv"
OUTPUT_FILE = "k8s/deployment.yaml"

def validate_services(services):
    gateway = next((s for s in services if s['name'] == 'gateway'), None)
    aggregator = next((s for s in services if s['name'] == 'aggregator'), None)
    
    if gateway and aggregator and gateway['flavour'] == 'large' and aggregator['flavour'] != 'large':
        raise ValueError("If gateway is large, aggregator must also be large")

def main():
    parser = argparse.ArgumentParser(description="Generate Kubernetes manifests for a specific namespace.")
    parser.add_argument("--namespace", required=True, help="The Kubernetes namespace to use.")
    parser.add_argument("--csv-file", default=CSV_FILE, help=f"Path to the services CSV file (default: {CSV_FILE}).")
    parser.add_argument("--template-file", default=TEMPLATE_FILE, help=f"Path to the Jinja2 template file (default: {TEMPLATE_FILE}).")
    parser.add_argument("--name")

    args = parser.parse_args()
    
    target_namespace = args.namespace
    csv_input_file = args.csv_file
    template_input_file = args.template_file
    
    output_file_name = f"k8s/deployment-{target_namespace}-{args.name}.yaml"
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        env = Environment(loader=FileSystemLoader(current_dir))
        template = env.get_template(template_input_file)

        services = []
        with open(os.path.join(current_dir, csv_input_file), 'r') as f:
            for line in f:
                if not line.strip() or line.strip().startswith('#'):
                    continue
                parts = [part.strip() for part in line.split(',')]
                if len(parts) < 2:
                    continue
                
                service, flavour = parts[0], parts[1]
                node = parts[2] if len(parts) > 2 else None
                
                if service == 'service' and flavour == 'flavour':
                    continue
                
                if not service or not flavour:
                    raise ValueError("Service name and flavour cannot be empty")
            
                if flavour not in ['large', 'tiny', 'medium']:
                    raise ValueError(f"Invalid flavour for {service}: {flavour}. Must be 'large' or 'tiny'")
        
                if service.startswith('data-gather-'):
                    service_config = SERVICES['data-gather'].copy()
                    service_config['name'] = service
                    service_config['flavour'] = flavour
                    service_config['node'] = node
                    services.append(service_config)
                elif service.startswith('mongodb-batch-'):
                    service_config = SERVICES['mongodb-batch'].copy()
                    service_config['name'] = service
                    service_config['flavour'] = flavour
                    service_config['node'] = node
                    services.append(service_config)
                elif service in SERVICES:
                    service_config = SERVICES[service].copy()
                    service_config['name'] = service
                    service_config['flavour'] = flavour
                    service_config['node'] = node
                    services.append(service_config)
                else:
                    raise ValueError(f"Invalid service: {service}")
            
        validate_services(services)
        output = template.render(services=services, namespace_name=target_namespace)
        output_dir = os.path.dirname(os.path.join(current_dir, output_file_name))
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(os.path.join(current_dir, output_file_name), 'w') as f:
            f.write(output)
        logging.info(f"Manifest successfully generated for namespace '{target_namespace}' in {os.path.join(current_dir, output_file_name)}")
        logging.info(f"Configured services: {services}")

    except Exception as e:
        logging.error(f"Error generating manifest: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
