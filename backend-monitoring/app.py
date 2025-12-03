from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json
import jwt
import os
from datetime import datetime, timedelta
import pika
import requests
import psycopg2
import sys
sys.path.append('/app/shared')
from rabbitmq_client import RabbitMQ

app = Flask(__name__)
app.config.from_pyfile('config.cfg')
db = SQLAlchemy(app)

rabbitmq_monitoring_consumer = RabbitMQ('monitoring-service', 'device_crud')  
pod_name = os.environ.get('HOSTNAME', 'flask-monitoring-0')
replica_id = int(pod_name.split('-')[-1]) + 1
rabbitmq_consumption_consumer = RabbitMQ('monitoring-service', 'monitoring_ingest', os.environ.get('COLLECTION_RABBIT_HOST', 'collection-rabbitmq-service.default.svc.cluster.local'), exchange_type='direct', routing_key=f'replica{replica_id}')
rabbitmq_alert_producer = RabbitMQ('monitoring-service', 'overconsumption_alerts')  

class DeviceConsumption(db.Model):
    __tablename__ = 'deviceConsumption'
    id = db.Column(db.Integer, primary_key=True)
    mapping_id = db.Column(db.Integer, db.ForeignKey('deviceMapping.mapping_key'), nullable=False)
    consumption = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    def __repr__(self):
        return f"Consumption: {self.consumption} kWh at {self.timestamp}"

class DeviceMapping(db.Model):
    __tablename__ = 'deviceMapping'
    mapping_key = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.Integer, unique=True, nullable=False)
    auth_id = db.Column(db.Integer, nullable=False)
    def __repr__(self):
        return f"Device ID: {self.device_id}, Auth: {self.auth_id}"

def handle_device_creation_message(message):
    message_type = message.get('type')
    data = message.get('data', {})
    
    if message_type == 'add_device':
        with app.app_context():
            try:
                device_id = data.get('device_id')
                auth_id = data.get('auth_id')
                
                device_mapping = DeviceMapping(device_id=device_id, auth_id=auth_id)
                db.session.add(device_mapping)
                db.session.commit()
                
                print(f"Device added to monitoring: {device_id}", flush=True)
            except Exception as e:
                db.session.rollback()
                print(f"Failed to add device to monitoring: {str(e)}", flush=True)
    
    elif message_type == 'delete_device':
        with app.app_context():
            try:
                device_id = data.get('device_id')
                
                mapping = db.session.execute(db.select(DeviceMapping).filter_by(device_id=device_id)).scalar()
                if mapping:
                    consumption = db.session.execute(db.select(DeviceConsumption).filter_by(mapping_id=mapping.mapping_key)).scalar()
                    if consumption:
                        db.session.delete(consumption)
                    
                    db.session.delete(mapping)
                
                db.session.commit()
                print(f"Device deleted from monitoring: {device_id}", flush=True)
            except Exception as e:
                db.session.rollback()
                print(f"Failed to delete device from monitoring: {str(e)}", flush=True)


def handle_consumption_message(message):
    message_type = message.get('type')
    data = message.get('data', {})
    
    if message_type == 'consumption_reading':
        with app.app_context():
            try:
                device_id = data.get('device_id')
                auth_id = data.get('auth_id')
                consumption = data.get('consumption')
                timestamp_str = data.get('timestamp')
                
                mapping = db.session.execute(db.select(DeviceMapping).filter_by(device_id=device_id)).scalar()
                if mapping:
                    if timestamp_str:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        timestamp = datetime.utcnow()
                    
                    try:
                        device_response = requests.get(
                            f"http://flask-device-service.default.svc.cluster.local/devices",
                            timeout=5
                        )
                        if device_response.status_code == 200:
                            devices = device_response.json().get('devices', [])
                            device_info = next((d for d in devices if d['device_id'] == device_id), None)
                            
                            if device_info:
                                max_consumption = float(device_info.get('maxConsumption', 0))
                                
                                if float(consumption) > max_consumption:
                                    print(f"⚠️  OVERCONSUMPTION DETECTED: Device {device_id}, Consumption: {consumption} kWh, Max: {max_consumption} kWh", flush=True)
                                    
                                    rabbitmq_alert_producer.sendMessage('overconsumption_alert', {
                                        'user_id': str(auth_id),
                                        'device_id': device_id,
                                        'consumption': float(consumption),
                                        'threshold': max_consumption,
                                        'timestamp': timestamp.isoformat()
                                    })
                                    print(f"Overconsumption alert sent for device {device_id}", flush=True)
                    except Exception as e:
                        print(f"Error fetching device info or sending alert: {str(e)}", flush=True)
                    
                    device_consumption = DeviceConsumption(
                        mapping_id=mapping.mapping_key,
                        consumption=float(consumption),
                        timestamp=timestamp
                    )
                    db.session.add(device_consumption)
                    db.session.commit()
                    
                    print(f"Stored consumption for device {device_id}: {consumption} kWh at {timestamp}", flush=True)
                else:
                    print(f"No mapping found for device {device_id}", flush=True)
                    
            except Exception as e:
                db.session.rollback()
                print(f"Failed to store consumption data: {str(e)}", flush=True)


rabbitmq_monitoring_consumer.consumeMessage(handle_device_creation_message)
rabbitmq_consumption_consumer.consumeMessage(handle_consumption_message)

@app.route('/consumptions', methods=["GET"])
def get_consumptions():
    user_id = request.args.get('user_id')
    date_str = request.args.get('date')
    
    query = DeviceConsumption.query
    
    if user_id:
        user_id_int = int(user_id)
        mapping_subquery = db.select(DeviceMapping.mapping_key).filter_by(auth_id=user_id_int)
        query = query.filter(DeviceConsumption.mapping_id.in_(mapping_subquery))
    
    if date_str:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            start_of_day = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            query = query.filter(DeviceConsumption.timestamp >= start_of_day, DeviceConsumption.timestamp < end_of_day)
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    consumptions = query.all()
    if not consumptions:
        return jsonify({"consumptions": []}), 200
    
    consumption_list = []
    for consumption in consumptions:
        mapping = db.session.execute(db.select(DeviceMapping).filter_by(mapping_key=consumption.mapping_id)).scalar()
        if mapping:
            consumption_list.append({
                "device_id": mapping.device_id,
                "auth_id": mapping.auth_id,
                "consumption": str(consumption.consumption),
                "timestamp": consumption.timestamp.isoformat()
            })
    
    return jsonify({"consumptions": consumption_list}), 200

if __name__ == '__main__':
      with app.app_context(): 
          db.create_all()
       
      app.run(debug=False, host='0.0.0.0', port=5001)
