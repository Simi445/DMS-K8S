from flask import Flask, render_template, request, redirect
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

rabbitmq_auth_consumer = RabbitMQ('device-service', 'user_events')  
rabbitmq_user_consumer = RabbitMQ('device-service', 'user_crud_events')  
rabbitmq_monitoring_producer = RabbitMQ('device-service', 'device_crud')  

class Device(db.Model):
    device_id = db.Column(db.Integer, primary_key=True)
    auth_id = db.Column(db.Integer, db.ForeignKey('users.auth_id'), nullable=False)
    name = db.Column(db.String(20), unique=False, nullable=False)
    status = db.Column(db.String(20), unique=False, nullable=False)
    consumption = db.Column(db.String(20), unique=False, nullable=False)
    def __repr__(self):
        return f"Device ID: {self.device_id}, Name: {self.name}, Consumption: {self.consumption}"

class Users(db.Model):
    auth_id = db.Column(db.Integer, primary_key=True)

def handle_auth_message(message):
    message_type = message.get('type')
    data = message.get('data', {})
    
    if message_type == 'add_user':
        with app.app_context():
            try:
                auth_id = data.get("auth_id")
                
                existing_user = db.session.execute(db.select(Users).filter_by(auth_id=auth_id)).scalar()
                if existing_user:
                    print(f"User with auth_id {auth_id} already exists in device service, skipping duplicate creation", flush=True)
                    return
                
                user_record = Users(auth_id=auth_id)
                db.session.add(user_record)
                db.session.commit()
                print(f"User added to device service via auth message: {auth_id}", flush=True)
            except Exception as e:
                db.session.rollback()
                print(f"Failed to add user to device service via auth message: {str(e)}", flush=True)

def handle_user_crud_message(message):
    message_type = message.get('type')
    data = message.get('data', {})
    
    with app.app_context():
        if message_type == 'update_user_in_devices':
            try:
                auth_id = data.get("auth_id")
                print(f"User updated in device service via user message: {auth_id}", flush=True)
            except Exception as e:
                print(f"Failed to update user in device service via user message: {str(e)}", flush=True)
        
        elif message_type == 'delete_device_user':
            try:
                auth_id = data.get("auth_id")
                user_record = db.session.execute(db.select(Users).filter_by(auth_id=auth_id)).scalar()
                if user_record:
                    db.session.delete(user_record)
                    db.session.commit()
                    print(f"User and devices deleted from device service via user message: {auth_id}", flush=True)
            except Exception as e:
                db.session.rollback()
                print(f"Failed to delete user from device service via user message: {str(e)}", flush=True)


rabbitmq_auth_consumer.consumeMessage(handle_auth_message)
rabbitmq_user_consumer.consumeMessage(handle_user_crud_message)

@app.route('/add-user', methods=["POST"])
def add_user():
    data = request.get_json()
    try:
        p = Users(auth_id = data.get("auth_id"))
        db.session.add(p)
        db.session.commit()
        response = {'ok': 'User processed successfully'}
        return app.response_class(
                response=json.dumps(response),
                status=201,
                mimetype='application/json'
            )
    except Exception as e:
        db.session.rollback()
        response = {"error": f"Failed to create user in device db: {str(e)}"}
        return app.response_class(
            response=json.dumps(response),
            status=500,
            mimetype='application/json'
        )
        
@app.route('/devices', methods=["GET"])
def get_users():
    devices = Device.query.all()
    if not devices:
        response = {"ok": "No devices existent", "devices": []}
        return app.response_class(
            response=json.dumps(response),
            status=200,
            mimetype='application/json'
        )
    
    device_list = []
    for device in devices:
        device_list.append({
            "device_id": device.device_id,
            "auth_id": device.auth_id,
            "name": device.name,
            "status": device.status,
            "maxConsumption": device.consumption
        })
        print(device_list[-1], flush=True)
    response = {'ok': 'Devices fetched!', 'devices': device_list}
    return app.response_class(
        response=json.dumps(response),
        status=200,
        mimetype='application/json'
    )

@app.route('/devices/<int:auth_id>', methods=["GET"])
def get_devices_by_auth_id(auth_id):
    user = db.session.execute(db.select(Users).filter_by(auth_id=auth_id)).scalar()
    if not user:
        response = {"error": "User does not exist in the device db!"}
        return app.response_class(
            response=json.dumps(response),
            status=404,
            mimetype='application/json'
        )
    
    devices = Device.query.filter_by(auth_id=auth_id).all()
    
    if not devices:
        response = {"ok": "No devices found for this user", "devices": []}
        return app.response_class(
            response=json.dumps(response),
            status=200,
            mimetype='application/json'
        )
    
    device_list = []
    for device in devices:
        device_list.append({
            "device_id": device.device_id,
            "auth_id": device.auth_id,
            "name": device.name,
            "status": device.status,
            "maxConsumption": device.consumption
        })
    
    response = {'ok': 'Devices fetched successfully!', 'devices': device_list}
    return app.response_class(
        response=json.dumps(response),
        status=200,
        mimetype='application/json'
    )


@app.route('/add-device', methods=["POST"])
def add_device():
    data = request.get_json()
    name = data.get('name')
    consumption = data.get('maxConsumption')
    status = data.get('status')
    assigned_to = int(data.get('assignedTo'))

    user = db.session.execute(db.select(Users).filter_by(auth_id=assigned_to)).scalar()
    if not user:
        response = {"error": "User does not exist in the device db!"}
        return app.response_class(
                response=json.dumps(response),
                status=500,
                mimetype='application/json'
            )

    try:
        device = Device(name=name, consumption=str(consumption), status=status, auth_id=user.auth_id)
        db.session.add(device)
    except Exception as e:
        db.session.rollback()
        response = {"error": f"Failed to create device: {str(e)}"}
        return app.response_class(
            response=json.dumps(response),
            status=500,
            mimetype='application/json'
        )
    db.session.commit()
    rabbitmq_monitoring_producer.sendMessage('add_device', {
        'device_id': device.device_id,
        'auth_id': device.auth_id,
    })
    response = {"ok": "Device created"}
    return app.response_class(
            response=json.dumps(response),
            status=201,
            mimetype='application/json'
        )
        
@app.route('/edit-device', methods=["PUT"])
def edit_device():
    data = request.get_json()
    device_id = data.get("device_id")
    name = data.get('name')
    consumption = data.get('maxConsumption')
    status = data.get('status')
    assigned_to = data.get('assignedTo')

    if device_id is None:
        response = {"error": "device_id is required to edit a device"}
        return app.response_class(
            response=json.dumps(response),
            status=400,
            mimetype='application/json'
        )

    try:
        device = db.session.execute(db.select(Device).filter_by(device_id=device_id)).scalar()
        if not device:
            response = {"error": "Device not found"}
            return app.response_class(
                response=json.dumps(response),
                status=404,
                mimetype='application/json'
            )

        device.name = name if name is not None else device.name
        device.consumption = str(consumption) if consumption is not None else device.consumption
        device.status = status if status is not None else device.status
        
        if assigned_to and assigned_to != 'no_user':
            user = db.session.execute(db.select(Users).filter_by(auth_id=int(assigned_to))).scalar()
            if not user:
                response = {"error": "Assigned user does not exist in the device db!"}
                return app.response_class(
                    response=json.dumps(response),
                    status=400,
                    mimetype='application/json'
                )
            device.auth_id = int(assigned_to)

        db.session.commit()

        response = {"ok": "Device updated successfully"}
        return app.response_class(
            response=json.dumps(response),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        db.session.rollback()
        response = {"error": f"Failed to update device: {str(e)}"}
        return app.response_class(
            response=json.dumps(response),
            status=500,
            mimetype='application/json'
        )

@app.route('/delete-device', methods=["DELETE"])
def delete_device():
    data = request.get_json()
    device_id = data.get("device_id")

    if device_id is None:
        response = {"error": "device_id is required to delete a device"}
        return app.response_class(
            response=json.dumps(response),
            status=400,
            mimetype='application/json'
        )

    try:
        device = db.session.execute(db.select(Device).filter_by(device_id=device_id)).scalar()
        if not device:
            response = {"error": "Device not found"}
            return app.response_class(
                response=json.dumps(response),
                status=404,
                mimetype='application/json'
            )

        db.session.delete(device)
        db.session.commit()
        rabbitmq_monitoring_producer.sendMessage('delete_device', {
            'device_id': device_id
        })

        response = {"ok": "Device successfully deleted"}
        return app.response_class(
            response=json.dumps(response),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        db.session.rollback()
        response = {"error": f"Failed to delete device: {str(e)}"}
        return app.response_class(
            response=json.dumps(response),
            status=500,
            mimetype='application/json'
        )

@app.route('/remove-user', methods=["DELETE"])
def remove_user():
    data = request.get_json()
    auth_id = data.get("auth_id")

    if auth_id is None:
        response = {"error": "auth_id is required"}
        return app.response_class(
            response=json.dumps(response),
            status=400,
            mimetype='application/json'
        )

    try:
        unassigned_user = db.session.execute(db.select(Users).filter_by(auth_id=-1)).scalar()
        if not unassigned_user:
            unassigned_user = Users(auth_id=-1)
            db.session.add(unassigned_user)
            db.session.flush()

        user = db.session.execute(db.select(Users).filter_by(auth_id=auth_id)).scalar()
        if user:
            db.session.delete(user)

        devices = Device.query.filter_by(auth_id=auth_id).all()
        for device in devices:
            device.auth_id = -1  
        
        db.session.commit()

        response = {"ok": f"User {auth_id} removed and devices unassigned"}
        return app.response_class(
            response=json.dumps(response),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        db.session.rollback()
        response = {"error": f"Failed to remove user: {str(e)}"}
        return app.response_class(
            response=json.dumps(response),
            status=500,
            mimetype='application/json'
        )

if __name__ == '__main__':
      with app.app_context(): 
          db.create_all()
       
      app.run(debug=False, host='0.0.0.0', port=5001)
