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
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-for-development-only')
USER_SERVICE_URL = os.environ.get('USER_SERVICE_URL', 'http://localhost:5002')
DEVICE_SERVICE_URL = os.environ.get('DEVICE_SERVICE_URL', 'http://localhost:5001')
db = SQLAlchemy(app)

class Auth(db.Model):
    auth_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), unique=False, nullable=False)
    def __repr__(self):
        return f"Auth ID: {self.auth_id}, Username: {self.username}, Email: {self.email}, Password: [HIDDEN]"



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

        payload = {"auth_id": auth_record.auth_id, "username": username, "email": email, "role": role}
        user_response = requests.post(f'{USER_SERVICE_URL}/create-user', json=payload, timeout=5)
        
        if user_response.status_code != 201:
            db.session.delete(auth_record)
            db.session.commit()
            return app.response_class(
                response=user_response.text,
                status=user_response.status_code,
                mimetype='application/json'
            )

        device_payload = {"auth_id": auth_record.auth_id}
        try:
            device_response = requests.post(f'{DEVICE_SERVICE_URL}/add-user', json=device_payload, timeout=5)
            if device_response.status_code != 201:
                print(f"Warning: Device service call failed: {device_response.text}")
        except Exception as e:
            print(f"Warning: Failed to contact device service: {str(e)}")

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
        print(f'Exception: {e}')
        db.session.rollback()
        response = {"error": f"Failed to create account: {str(e)}"}
        return app.response_class(
            response=json.dumps(response),
            status=500,
            mimetype='application/json'
        )


@app.route('/edit-auth', methods=["PUT"])
def edit_auth():
    data = request.get_json() or {}
    auth_id = data.get("auth_id")
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if auth_id is None:
        response = {"error": "auth_id is required"}
        return app.response_class(
            response=json.dumps(response),
            status=400,
            mimetype='application/json'
        )

    if not username and not email and not password:
        response = {"error": "At least username, email, or password must be provided"}
        return app.response_class(
            response=json.dumps(response),
            status=400,
            mimetype='application/json'
        )

    try:
        account = db.session.execute(db.select(Auth).filter_by(auth_id=auth_id)).scalar()
        if not account:
            response = {"error": "Auth record not found"}
            return app.response_class(
                response=json.dumps(response),
                status=404,
                mimetype='application/json'
            )

        if username and username != account.username:
            existing_auth = db.session.execute(db.select(Auth).filter_by(username=username)).scalar()
            if existing_auth:
                response = {"error": "Username already exists"}
                return app.response_class(
                    response=json.dumps(response),
                    status=400,
                    mimetype='application/json'
                )
            account.username = username

        if email and email != account.email:
            existing_email = db.session.execute(db.select(Auth).filter_by(email=email)).scalar()
            if existing_email:
                response = {"error": "Email already exists"}
                return app.response_class(
                    response=json.dumps(response),
                    status=400,
                    mimetype='application/json'
                )
            account.email = email

        if password:
            account.password = generate_password_hash(password)

        db.session.commit()

        response = {"ok": "Auth record updated successfully"}
        return app.response_class(
            response=json.dumps(response),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        db.session.rollback()
        response = {"error": f"Failed to update auth record: {str(e)}"}
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


@app.route('/delete-auth', methods=["DELETE"])
def delete_auth():
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
        account = db.session.execute(db.select(Auth).filter_by(auth_id=auth_id)).scalar()
        if not account:
            response = {"error": "Auth record not found"}
            return app.response_class(
                response=json.dumps(response),
                status=404,
                mimetype='application/json'
            )

        db.session.delete(account)
        db.session.commit()

        response = {"ok": "Auth record deleted"}
        return app.response_class(
            response=json.dumps(response),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        db.session.rollback()
        response = {"error": f"Failed to delete auth record: {str(e)}"}
        return app.response_class(
            response=json.dumps(response),
            status=500,
            mimetype='application/json'
        )


if __name__ == '__main__':
      with app.app_context(): 
          db.create_all()
       
      app.run(debug=True, host='0.0.0.0', port=5000)
