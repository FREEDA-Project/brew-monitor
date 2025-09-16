import requests
import time
import argparse
import logging
from datetime import datetime
import random
import sys

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('load_test.log'),
        logging.StreamHandler()
    ]
)

class BreweryLoadTester:
    def __init__(self, base_url, test_high_gateway=False, request_interval=1.0):
        self.base_url = base_url
        self.test_high_gateway = test_high_gateway
        self.request_interval = request_interval
        self.endpoints = ['/api/aggregator/current']
        if test_high_gateway:
            self.endpoints.append('/api/analyzer/stats')

    def make_request(self, endpoint):
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}{endpoint}")
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                logging.info(f"SUCCESS - {endpoint} - Status: {response.status_code} - Time: {elapsed_time:.2f}s - Response: {response.text}")
            else:
                logging.error(f"ERROR - {endpoint} - Status: {response.status_code} - Time: {elapsed_time:.2f}s - Response: {response.text}")
            
            return response.status_code == 200
        except Exception as e:
            logging.error(f"EXCEPTION - {endpoint} - Error: {str(e)}")
            return False

    def run_load_test(self, duration_minutes):
        end_time = time.time() + (duration_minutes * 60)
        successful_requests = 0
        total_requests = 0

        logging.info(f"Starting load test for {duration_minutes} minutes")
        logging.info(f"Tested endpoints: {', '.join(self.endpoints)}")

        while time.time() < end_time:
            for endpoint in self.endpoints:
                if self.make_request(endpoint):
                    successful_requests += 1
                total_requests += 1
                time.sleep(self.request_interval)

        success_rate = (successful_requests / total_requests) * 100 if total_requests > 0 else 0
        logging.info(f"\nLoad test completed:")
        logging.info(f"Total requests: {total_requests}")
        logging.info(f"Successful requests: {successful_requests}")
        logging.info(f"Success rate: {success_rate:.2f}%")

def main():
    parser = argparse.ArgumentParser(description='Load testing script for the Brewery application')
    parser.add_argument('--url', required=True, help='Base URL of the gateway service (e.g., http://192.168.49.2:30000)')
    parser.add_argument('--high', action='store_true', help='Test the high gateway endpoints')
    parser.add_argument('--interval', type=float, default=1.0, help='Interval between requests in seconds')
    parser.add_argument('--duration', type=int, default=5, help='Test duration in minutes')
    
    args = parser.parse_args()
    
    tester = BreweryLoadTester(
        base_url=args.url,
        test_high_gateway=args.high,
        request_interval=args.interval
    )
    
    tester.run_load_test(args.duration)

if __name__ == "__main__":
    main()
