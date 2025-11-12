from flask import Flask
import requests
import json
import time
import random
import threading
import os
from datetime import datetime, timedelta
import sys
sys.path.append('/app/shared')
from rabbitmq_client import RabbitMQ

app = Flask(__name__)

rabbitmq_producer = RabbitMQ('simulator-service', 'consumption_data', os.environ.get('RABBIT_HOST', 'collection-rabbitmq-service.default.svc.cluster.local'))
SIMULATION_INTERVAL = 5  

class ConsumptionSimulator:
    def __init__(self):
        self.devices = []
        self.base_loads = {} 
        self.last_update = {}
        
    def fetch_devices(self):
        try:
            response = requests.get("http://flask-device-service.default.svc.cluster.local/devices")
            if response.status_code == 200:
                data = response.json()
                self.devices = data.get('devices', [])
                print(f"Fetched {len(self.devices)} devices", flush=True)
                
                for device in self.devices:
                    device_id = device['device_id']
                    if device_id not in self.base_loads:
                        self.base_loads[device_id] = random.uniform(0.5, 2.0)
                        self.last_update[device_id] = datetime.now()
            else:
                print(f"Failed to fetch devices: {response.status_code}", flush=True)
        except Exception as e:
            print(f"Error fetching devices: {str(e)}", flush=True)
    
    def get_hourly_multiplier(self, hour):
        if 0 <= hour < 6: 
            return 0.3  
        elif 6 <= hour < 9:  
            return 0.6 
        elif 9 <= hour < 17:
            return 0.8  
        elif 17 <= hour < 21:  
            return 1.2  
        else:  
            return 0.5 
    
    def generate_consumption(self, device_id, base_load):
        now = datetime.now()
        hour = now.hour
        hourly_multiplier = self.get_hourly_multiplier(hour)
        variation = random.uniform(0.8, 1.2)
        consumption = base_load * hourly_multiplier * variation
        consumption = max(0.1, consumption)
        
        return round(consumption, 3)
    
    def simulate_and_send(self):
        while True:
            try:
                self.fetch_devices()
                
                for device in self.devices:
                    device_id = device['device_id']
                    auth_id = device['auth_id']
                    
                    if device_id in self.base_loads:
                        consumption = self.generate_consumption(device_id, self.base_loads[device_id])
                        
                        message_data = {
                            'device_id': device_id,
                            'auth_id': auth_id,
                            'consumption': consumption,
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        
                        rabbitmq_producer.sendMessage('consumption_reading', message_data)
                        print(f"Sent consumption for device {device_id}: {consumption} kWh", flush=True)
                
                time.sleep(SIMULATION_INTERVAL)
                
            except Exception as e:
                print(f"Error in simulation loop: {str(e)}", flush=True)
                time.sleep(60) 

simulator = ConsumptionSimulator()


if __name__ == '__main__':
    simulation_thread = threading.Thread(target=simulator.simulate_and_send, daemon=True)
    simulation_thread.start()
    
    print("Device Simulator starting...", flush=True)
    app.run(debug=False, host='0.0.0.0', port=5001)