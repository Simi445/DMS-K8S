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
db = SQLAlchemy(app)

class Auth(db.Model):
    auth_id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(255), unique=False, nullable=False)
    def __repr__(self):
        return f"Auth ID: {self.auth_id}, Password: [HIDDEN]"



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
    
    password_hash = generate_password_hash(password)

    try:
        verify_response = requests.post(f'{USER_SERVICE_URL}/verify-register', json=data, timeout=5)
        if verify_response.status_code != 201:
            return app.response_class(
                response=verify_response.text,
                status=verify_response.status_code,
                mimetype='application/json'
            )
    except Exception as e:
        response = {"error": f"Failed to verify user at register: {str(e)}"}
        return app.response_class(
            response=json.dumps(response),
            status=500,
            mimetype='application/json'
        )

    try:
        auth_record = Auth(password=password_hash)
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

        token_payload = {
            'auth_id': auth_record.auth_id,
            'username': username,
            'email': email,
            'role': role,
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
    password = data.get("password")

    if auth_id is None or not password:
        response = {"error": "auth_id and password are required"}
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

        account.password = generate_password_hash(password)
        db.session.commit()

        response = {"ok": "Password updated"}
        return app.response_class(
            response=json.dumps(response),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        db.session.rollback()
        response = {"error": f"Failed to update password in auth db: {str(e)}"}
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
    
    verify_response = None
    payload = {"username":username}
    try:
        verify_response = requests.post(f'{USER_SERVICE_URL}/verify-login', json=payload, timeout=5)
        if verify_response.status_code != 201:
            return app.response_class(
                response=verify_response.text,
                status=verify_response.status_code,
                mimetype='application/json'
            )
    except Exception as e:
        response = {"error": f"Failed to verify user at login: {str(e)}"}
        return app.response_class(
            response=json.dumps(response),
            status=500,
            mimetype='application/json'
        )

    verify_data = verify_response.json()
    auth_id = verify_data.get('auth_id')
    passwordSearch = db.session.execute(db.select(Auth).filter_by(auth_id=auth_id)).scalar()
    

    if passwordSearch and check_password_hash(passwordSearch.password, password):
        user_details_response = requests.get(f'{USER_SERVICE_URL}/user/{auth_id}', timeout=5)
        if user_details_response.status_code == 200:
            user_data = user_details_response.json()
            
            token_payload = {
                'auth_id': auth_id,
                'username': user_data.get('username', username),
                'email': user_data.get('email'),
                'role': user_data.get('role'),
                'exp': datetime.utcnow() + timedelta(hours=24)
            }
            token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')
            
            response = {
                "success": "Login successful",
                "token": token
            }
        else:
            response = {
                "success": "Login successful"
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

@app.route('/health', methods=["GET"])
def health():
    response = {"ok": f"App healthy!"}
    return app.response_class(
            response=json.dumps(response),
            status=200,
            mimetype='application/json'
        )

if __name__ == '__main__':
      with app.app_context(): 
          db.create_all()
       
      app.run(debug=True, host='0.0.0.0', port=5000)
