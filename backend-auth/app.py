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
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-for-development-only')
db = SQLAlchemy(app)

rabbitmq_producer = RabbitMQ('auth-service', 'user_events') 
rabbitmq_consumer = RabbitMQ('auth-service', 'user_crud_events')

class Auth(db.Model):
    auth_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), unique=False, nullable=False)
    def __repr__(self):
        return f"Auth ID: {self.auth_id}, Username: {self.username}, Email: {self.email}, Password: [HIDDEN]"

def handle_user_crud_message(message):
    message_type = message.get('type')
    data = message.get('data', {})
    
    with app.app_context():
        if message_type == 'update_auth_profile':
            try:
                auth_id = data.get("auth_id")
                username = data.get("username")
                email = data.get("email")
                password = data.get("password")
                
                if auth_id is None:
                    print("Error: auth_id is required for profile update", flush=True)
                    return
                
                auth_record = db.session.execute(db.select(Auth).filter_by(auth_id=auth_id)).scalar()
                if not auth_record:
                    print(f"Error: Auth record not found for auth_id: {auth_id}", flush=True)
                    return
                
                if username:
                    auth_record.username = username
                if email:
                    auth_record.email = email
                if password:
                    auth_record.password = generate_password_hash(password)
                
                db.session.commit()
                print(f"Auth profile updated successfully via message: {auth_record.username}", flush=True)
            except Exception as e:
                db.session.rollback()
                print(f"Failed to update auth profile via message: {str(e)}", flush=True)
        
        elif message_type == 'delete_auth':
            try:
                auth_id = data.get("auth_id")
                auth_record = db.session.execute(db.select(Auth).filter_by(auth_id=auth_id)).scalar()
                if auth_record:
                    db.session.delete(auth_record)
                    db.session.commit()
                    print(f"Auth record deleted successfully via message: {auth_id}", flush=True)
                else:
                    print(f"Auth record not found for deletion: {auth_id}", flush=True)
            except Exception as e:
                db.session.rollback()
                print(f"Failed to delete auth record via message: {str(e)}", flush=True)

rabbitmq_consumer.consumeMessage(handle_user_crud_message)



@app.route('/register', methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    role = data.get("role")
    password = data.get("password")
    
    if not all([username, email, role, password]):
        response = {"error": "All fields are required"}
        return app.response_class(
            response=json.dumps(response),
            status=400,
            mimetype='application/json'
        )
    
    existing_auth = db.session.execute(db.select(Auth).filter_by(username=username)).scalar()
    if existing_auth:
        response = {"error": "Username already exists"}
        return app.response_class(
            response=json.dumps(response),
            status=400,
            mimetype='application/json'
        )
    
    existing_email = db.session.execute(db.select(Auth).filter_by(email=email)).scalar()
    if existing_email:
        response = {"error": "Email already exists"}
        return app.response_class(
            response=json.dumps(response),
            status=400,
            mimetype='application/json'
        )
    
    password_hash = generate_password_hash(password)

    try:
        auth_record = Auth(username=username, email=email, password=password_hash)
        db.session.add(auth_record)
        db.session.commit()

        user_payload = {"auth_id": auth_record.auth_id, "username": username, "email": email, "role": role}
        rabbitmq_producer.sendMessage('create_user', user_payload)

        device_payload = {"auth_id": auth_record.auth_id}
        rabbitmq_producer.sendMessage('add_user', device_payload)

        token_payload = {
            'auth_id': auth_record.auth_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')
        
        response = {"ok": "Account created", "token": token}
        return app.response_class(
            response=json.dumps(response),
            status=201,
            mimetype='application/json'
        )
        
    except Exception as e:
        print(f'Exception: {e}', flush=True)
        db.session.rollback()
        response = {"error": f"Failed to create account: {str(e)}"}
        return app.response_class(
            response=json.dumps(response),
            status=500,
            mimetype='application/json'
        )


@app.route('/login', methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        response = {"error": "Username and password required"}
        return app.response_class(
            response=json.dumps(response),
            status=400,
            mimetype='application/json'
        )
    
    auth_record = db.session.execute(db.select(Auth).filter_by(username=username)).scalar()
    if not auth_record:
        response = {"error": "Invalid username or password"}
        return app.response_class(
            response=json.dumps(response),
            status=401,
            mimetype='application/json'
        )
    
    if check_password_hash(auth_record.password, password):
        token_payload = {
            'auth_id': auth_record.auth_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')
        
        response = {
            "success": "Login successful",
            "token": token
        }
        
        return app.response_class(
            response=json.dumps(response),
            status=200,
            mimetype='application/json'
        )
    else:
        response = {"error": "Invalid username or password"}
        return app.response_class(
            response=json.dumps(response),
            status=401,
            mimetype='application/json'
        )


if __name__ == '__main__':
      with app.app_context(): 
          db.create_all()
       
      app.run(debug=False, host='0.0.0.0', port=5000)
