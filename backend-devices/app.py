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

app = Flask(__name__)
app.config.from_pyfile('config.cfg')
db = SQLAlchemy(app)

class Device(db.Model):
    device_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    name = db.Column(db.String(20), unique=False, nullable=False)
    status = db.Column(db.String(20), unique=False, nullable=False)
    consumption = db.Column(db.String(20), unique=False, nullable=False)
    def __repr__(self):
        return f"Device ID: {self.device_id}, Name: {self.name}, Consumption: {self.consumption}"

class Users(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)

@app.route('/add-user', methods=["POST"])
def add_user():
    data = request.get_json()
    try:
        p = Users(user_id = data.get("user_id"))
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
        response = {"ok": "No devices existent"}
        return app.response_class(
            response=json.dumps(response),
            status=204,
            mimetype='application/json'
        )
    
    device_list = []
    for device in devices:
        device_list.append({
            "device_id": device.device_id,
            "user_id": device.user_id,
            "name": device.name,
            "status": device.status,
            "maxConsumption": device.consumption
        })
        print(device_list[-1])
    response = {'ok': 'Devices fetched!', 'devices': device_list}
    return app.response_class(
        response=json.dumps(response),
        status=201,
        mimetype='application/json'
    )

@app.route('/devices/<int:user_id>', methods=["GET"])
def get_devices_by_user_id(user_id):
    user = db.session.execute(db.select(Users).filter_by(user_id=user_id)).scalar()
    if not user:
        response = {"error": "User does not exist in the device db!"}
        return app.response_class(
            response=json.dumps(response),
            status=404,
            mimetype='application/json'
        )
    
    devices = Device.query.filter_by(user_id=user_id).all()
    
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
            "user_id": device.user_id,
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

    user = db.session.execute(db.select(Users).filter_by(user_id=assigned_to)).scalar()
    if not user:
        response = {"error": "User does not exist in the device db!"}
        return app.response_class(
                response=json.dumps(response),
                status=500,
                mimetype='application/json'
            )

    try:
        device = Device(name=name, consumption=str(consumption), status=status, user_id=user.user_id)
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

        device.name = name
        device.consumption = str(consumption)
        device.status = status
        
        if assigned_to and assigned_to != 'no_user':
            user = db.session.execute(db.select(Users).filter_by(user_id=int(assigned_to))).scalar()
            if not user:
                response = {"error": "Assigned user does not exist in the device db!"}
                return app.response_class(
                    response=json.dumps(response),
                    status=400,
                    mimetype='application/json'
                )
            device.user_id = int(assigned_to)

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

if __name__ == '__main__':
      with app.app_context(): 
          db.create_all()
       
      app.run(debug=True, host='0.0.0.0', port='5001')
