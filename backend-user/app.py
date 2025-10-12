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
DEVICE_SERVICE_URL = os.environ.get('DEVICE_SERVICE_URL', 'http://localhost:5001')
AUTH_SERVICE_URL = os.environ.get('AUTH_SERVICE_URL', 'http://localhost:5000')

db = SQLAlchemy(app)


class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=False, nullable=False)
    email = db.Column(db.String(20), unique=False, nullable=False)
    role = db.Column(db.String(20), unique=False, nullable=False)
    def __repr__(self):
        return f"username : {self.username}, Email: {self.email}, role : {self.role}"

class UserAuth(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    auth_id = db.Column(db.Integer, nullable=False)


@app.route('/verify-login', methods=["POST"])
def verify_login():
    data = request.get_json()
    username = data.get("username")
    user = db.session.execute(db.select(User).filter_by(username=username)).scalar()
    
    if user:
        user_auth = db.session.execute(db.select(UserAuth).filter_by(user_id=user.user_id)).scalar()
        
        if user_auth:
            response = {"ok": "User exists successfully", "auth_id": user_auth.auth_id}
            return app.response_class(
                response=json.dumps(response),
                status=201,
                mimetype='application/json'
            )
        else:
            response = {"error": "User authentication record not found!"}
            return app.response_class(
                response=json.dumps(response),
                status=404,
                mimetype='application/json'
            )
    else:
        response = {"error": "User not found!"}
        return app.response_class(
            response=json.dumps(response),
            status=404,
            mimetype='application/json'
        )

@app.route('/verify-register', methods=["POST"])
def verify_register():
    data = request.get_json()
    auth_id = data.get("auth_id")
    username = data.get("username")
    email = data.get("email")
    role = data.get("role")

    account_username = db.session.execute(db.select(User).filter_by(username=username)).first()
    account_email = db.session.execute(db.select(User).filter_by(email=email)).first()

    if account_username:
        response = {"error": "Account Username exists!"}
        return app.response_class(
            response=json.dumps(response),
            status=400,
            mimetype='application/json'
        )

    if account_email:
        response = {"error": "Email in use!"}
        return app.response_class(
            response=json.dumps(response),
            status=400,
            mimetype='application/json'
        )

    response = {'ok': 'User does not exist, can be created'}
    return app.response_class(
            response=json.dumps(response),
            status=201,
            mimetype='application/json'
        )

@app.route('/create-user', methods=["POST"])
def create_user():
    data = request.get_json()
    auth_id = data.get("auth_id")
    username = data.get("username")
    email = data.get("email")
    role = data.get("role")

    try:
        user_record = User(username=username, email=email, role=role)
        db.session.add(user_record)
        db.session.flush()

        user_auth = UserAuth(auth_id=auth_id, user_id=user_record.user_id)
        db.session.add(user_auth)

        payload = {"user_id": user_record.user_id}
        user_response = requests.post(f'{DEVICE_SERVICE_URL}/add-user', json=payload)
        
        if user_response.status_code != 201:
            db.session.rollback()  
            return app.response_class(
                response=user_response.text,
                status=user_response.status_code,
                mimetype='application/json'
            )

        db.session.commit() 

        
        response = {"ok": "User created successfully"}
        return app.response_class(
            response=json.dumps(response),
            status=201,
            mimetype='application/json'
        )
        
    except Exception as e:
        db.session.rollback()
        response = {"error": f"Failed to create user: {str(e)}"}
        return app.response_class(
            response=json.dumps(response),
            status=500,
            mimetype='application/json'
        )

@app.route('/user/<int:auth_id>', methods=["GET"])
def get_user_by_auth_id(auth_id):
    user_auth = db.session.execute(db.select(UserAuth).filter_by(auth_id=auth_id)).scalar()
    if user_auth:
        user = db.session.execute(db.select(User).filter_by(user_id=user_auth.user_id)).scalar()
        if user:
            response = {
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
            return app.response_class(
                response=json.dumps(response),
                status=200,
                mimetype='application/json'
            )
    
    response = {"error": "User not found"}
    return app.response_class(
        response=json.dumps(response),
        status=404,
        mimetype='application/json'
    )

@app.route('/users', methods=["GET"])
def get_users():
    users = User.query.all()
    if not users:
        response = {"ok": "No users existent"}
        return app.response_class(
            response=json.dumps(response),
            status=204,
            mimetype='application/json'
        )
    
    users_list = []
    for user in users:
        users_list.append({
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        })
    response = {'ok': 'Users fetched!', 'users': users_list}
    return app.response_class(
        response=json.dumps(response),
        status=201,
        mimetype='application/json'
    )


@app.route('/edit-user', methods=["PUT"])
def edit_user():
    data = request.get_json()
    user_id = data.get("user_id")
    username = data.get("username")
    email = data.get("email")
    role = data.get("role")
    password = data.get("password")

    if user_id is None:
        response = {"error": "user_id is required to edit a user"}
        return app.response_class(
            response=json.dumps(response),
            status=400,
            mimetype='application/json'
        )

    try:
        account = db.session.execute(db.select(User).filter_by(user_id=user_id)).scalar()
        if not account:
            response = {"error": "User not found"}
            return app.response_class(
                response=json.dumps(response),
                status=404,
                mimetype='application/json'
            )


        account.username = username
        account.email = email
        account.role = role

        auth_entry = db.session.execute(db.select(UserAuth).filter_by(user_id=account.user_id)).scalar()
        if not auth_entry:
            response = {"error": "User authentication record not found"}
            return app.response_class(
                response=json.dumps(response),
                status=404,
                mimetype='application/json'
            )

        auth_payload = {"auth_id": auth_entry.auth_id, "password": password}
        user_response = requests.put(f'{AUTH_SERVICE_URL}/edit-auth', json=auth_payload, timeout=5)

        if user_response.status_code not in (200, 204):
            db.session.rollback()
            return app.response_class(
                response=user_response.text,
                status=user_response.status_code,
                mimetype='application/json'
            )

        db.session.commit()
        response = {'ok': 'User edited successfully'}
        return app.response_class(
            response=json.dumps(response),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        db.session.rollback()
        response = {"error": f"Failed to edit user: {str(e)}"}
        return app.response_class(
            response=json.dumps(response),
            status=500,
            mimetype='application/json'
        )

@app.route('/devices/<int:user_id>', methods=["GET"])
def get_devices_of_user(user_id):
    user = db.session.execute(db.select(User).filter_by(user_id=user_id)).scalar()
    if user:
        response = {
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
        return app.response_class(
            response=json.dumps(response),
            status=200,
            mimetype='application/json'
        )

    response = {"error": "User not found"}
    return app.response_class(
        response=json.dumps(response),
        status=404,
        mimetype='application/json'
    )


@app.route('/delete-user', methods=["DELETE"])
def delete_user():
    data = request.get_json()
    user_id = data.get("user_id")

    if user_id is None:
        response = {"error": "user_id is required to delete a user"}
        return app.response_class(
            response=json.dumps(response),
            status=400,
            mimetype='application/json'
        )

    try:
        account = db.session.execute(db.select(User).filter_by(user_id=user_id)).scalar()
        if not account:
            response = {"error": "User not found"}
            return app.response_class(
                response=json.dumps(response),
                status=404,
                mimetype='application/json'
            )

        auth_entry = db.session.execute(db.select(UserAuth).filter_by(user_id=account.user_id)).scalar()

        if auth_entry:
            auth_payload = {"auth_id": auth_entry.auth_id}
            try:
                auth_response = requests.delete(f'{AUTH_SERVICE_URL}/delete-auth', json=auth_payload, timeout=5)
            except Exception as e:
                response = {"error": f"Failed to contact auth service: {str(e)}"}
                return app.response_class(
                    response=json.dumps(response),
                    status=500,
                    mimetype='application/json'
                )

            if auth_response.status_code not in (200, 204):
                return app.response_class(
                    response=auth_response.text,
                    status=auth_response.status_code,
                    mimetype='application/json'
                )

        if auth_entry:
            db.session.delete(auth_entry)
        db.session.delete(account)
        db.session.commit()

        response = {"ok": "User and associated auth deleted"}
        return app.response_class(
            response=json.dumps(response),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        db.session.rollback()
        response = {"error": f"Failed to delete user: {str(e)}"}
        return app.response_class(
            response=json.dumps(response),
            status=500,
            mimetype='application/json'
        )

if __name__ == '__main__':
      with app.app_context(): 
          db.create_all()
       
      app.run(debug=True, host='0.0.0.0', port='5002')
