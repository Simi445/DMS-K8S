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

rabbitmq_consumer = RabbitMQ('user-service', 'user_events') 
rabbitmq_publisher = RabbitMQ('user-service', 'user_crud_events')  


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

def handle_message(message):
    message_type = message.get('type')
    data = message.get('data', {})
    
    if message_type == 'create_user':
        with app.app_context():
            try:
                auth_id = data.get("auth_id")
                username = data.get("username")
                email = data.get("email")
                role = data.get("role")
                
            
                existing_user_auth = db.session.execute(db.select(UserAuth).filter_by(auth_id=auth_id)).scalar()
                if existing_user_auth:
                    print(f"User with auth_id {auth_id} already exists, skipping duplicate creation", flush=True)
                    return
                
                user_record = User(username=username, email=email, role=role)
                db.session.add(user_record)
                db.session.flush()
                
                user_auth = UserAuth(auth_id=auth_id, user_id=user_record.user_id)
                db.session.add(user_auth)
                db.session.commit()
                
                print(f"User created successfully via message: {username}", flush=True)
            except Exception as e:
                db.session.rollback()
                print(f"Failed to create user via message: {str(e)}", flush=True)

rabbitmq_consumer.consumeMessage(handle_message)



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
            status=200,
            mimetype='application/json'
        )
    
    users_list = []
    for user in users:
        user_auth = db.session.execute(db.select(UserAuth).filter_by(user_id=user.user_id)).scalar()
        auth_id = user_auth.auth_id if user_auth else None
        
        users_list.append({
            "auth_id": auth_id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        })
    response = {'ok': 'Users fetched!', 'users': users_list}
    return app.response_class(
        response=json.dumps(response),
        status=200,
        mimetype='application/json'
    )


@app.route('/admins', methods=["GET"])
def get_admins():
    """Get all users with admin role"""
    admin_users = User.query.filter_by(role='admin').all()
    if not admin_users:
        response = {"ok": "No admin users found", "admins": []}
        return app.response_class(
            response=json.dumps(response),
            status=200,
            mimetype='application/json'
        )
    
    admins_list = []
    for user in admin_users:
        user_auth = db.session.execute(db.select(UserAuth).filter_by(user_id=user.user_id)).scalar()
        auth_id = user_auth.auth_id if user_auth else None
        
        admins_list.append({
            "id": str(auth_id) if auth_id else None,
            "username": user.username,
            "name": user.username,  
            "email": user.email,
            "role": user.role,
            "is_online": True 
        })
    
    response = {'ok': 'Admins fetched!', 'admins': admins_list}
    return app.response_class(
        response=json.dumps(response),
        status=200,
        mimetype='application/json'
    )


@app.route('/edit-user', methods=["PUT"])
def edit_user():
    data = request.get_json()
    auth_id = data.get("auth_id")
    username = data.get("username")
    email = data.get("email")
    role = data.get("role")

    if auth_id is None:
        response = {"error": "auth_id is required to edit a user"}
        return app.response_class(
            response=json.dumps(response),
            status=400,
            mimetype='application/json'
        )

    try:
        user_auth = db.session.execute(db.select(UserAuth).filter_by(auth_id=auth_id)).scalar()
        if not user_auth:
            response = {"error": "User auth mapping not found"}
            return app.response_class(
                response=json.dumps(response),
                status=404,
                mimetype='application/json'
            )
        
        user_id = user_auth.user_id
        account = db.session.execute(db.select(User).filter_by(user_id=user_id)).scalar()
        if not account:
            response = {"error": "User not found"}
            return app.response_class(
                response=json.dumps(response),
                status=404,
                mimetype='application/json'
            )

        if username and username != account.username:
            existing_user = db.session.execute(db.select(User).filter_by(username=username)).scalar()
            if existing_user:
                response = {"error": "Username already exists"}
                return app.response_class(
                    response=json.dumps(response),
                    status=400,
                    mimetype='application/json'
                )

        if email and email != account.email:
            existing_email = db.session.execute(db.select(User).filter_by(email=email)).scalar()
            if existing_email:
                response = {"error": "Email already exists"}
                return app.response_class(
                    response=json.dumps(response),
                    status=400,
                    mimetype='application/json'
                )

        account.username = username
        account.email = email
        account.role = role

        db.session.commit()
        
        auth_payload = {"auth_id": auth_id, "username": username, "email": email}
        rabbitmq_publisher.sendMessage('update_auth_profile', auth_payload)
        
        device_payload = {"auth_id": auth_id, "username": username, "email": email, "role": role}
        rabbitmq_publisher.sendMessage('update_user_in_devices', device_payload)
        
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

@app.route('/devices/<int:auth_id>', methods=["GET"])
def get_devices_of_user(auth_id):
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


@app.route('/delete-user', methods=["DELETE"])
def delete_user():
    data = request.get_json()
    auth_id = data.get("auth_id")

    if auth_id is None:
        response = {"error": "auth_id is required to delete a user"}
        return app.response_class(
            response=json.dumps(response),
            status=400,
            mimetype='application/json'
        )

    try:
        user_auth = db.session.execute(db.select(UserAuth).filter_by(auth_id=auth_id)).scalar()
        if not user_auth:
            response = {"error": "User auth mapping not found"}
            return app.response_class(
                response=json.dumps(response),
                status=404,
                mimetype='application/json'
            )
        
        user_id = user_auth.user_id
        account = db.session.execute(db.select(User).filter_by(user_id=user_id)).scalar()
        if not account:
            response = {"error": "User not found"}
            return app.response_class(
                response=json.dumps(response),
                status=404,
                mimetype='application/json'
            )

        auth_payload = {"auth_id": auth_id}
        rabbitmq_publisher.sendMessage('delete_auth', auth_payload)
        
        device_payload = {"auth_id": auth_id}
        rabbitmq_publisher.sendMessage('delete_device_user', device_payload)
        
        db.session.delete(user_auth)
        db.session.flush() 
        

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
       
      app.run(debug=False, host='0.0.0.0', port='5002')
