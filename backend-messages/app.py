from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import uuid
from datetime import datetime, UTC
import re
from openai import OpenAI
import sys
import requests
sys.path.append('/app/shared')
from rabbitmq_client import RabbitMQ

app = Flask(__name__)
CORS(app)
app.config.from_pyfile('config.cfg')

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=True, engineio_logger=True)

rabbitmq_alert_consumer = RabbitMQ('messages-service', 'overconsumption_alerts', host='rabbitmq-service')

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = db.Column(db.String(36), nullable=False)
    receiver_id = db.Column(db.String(36), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    is_read = db.Column(db.Boolean, default=False)
    chat_session_id = db.Column(db.String(36), nullable=False)
    message_type = db.Column(db.String(20), default='user') 

class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), nullable=False)
    admin_id = db.Column(db.String(36), nullable=True)
    status = db.Column(db.String(20), default='active') 
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    last_activity = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

RULES = {
    r'(?i)help|support|assist': "I'm here to help! You can ask me about your energy consumption, billing, or any issues with your devices.",
    r'(?i)consumption|usage|energy': "I can help you understand your energy consumption. Check the monitoring dashboard for detailed insights about your device usage.",
    r'(?i)device|sensor|monitor': "Your devices are being monitored in real-time. If you have issues with a specific device, please provide the device ID.",
    r'(?i)billing|bill|cost|price': "For billing questions, your energy costs are calculated based on your actual consumption. Check your dashboard for detailed billing information.",
    r'(?i)alert|notification|warning': "You will receive alerts for unusual consumption patterns. These help you identify potential issues with your devices.",
    r'(?i)password|login|account': "For account-related issues, please contact your system administrator directly through this chat.",
    r'(?i)thank|thanks': "You're welcome! Is there anything else I can help you with?",
    r'(?i)hello|hi|hey': "Hello! How can I assist you with your energy monitoring today?",
    r'(?i)bye|goodbye|see you': "Goodbye! Feel free to reach out anytime if you need assistance.",
}

def get_rule_based_response(message):
    for pattern, response in RULES.items():
        if re.search(pattern, message):
            return response
    return None

def get_ai_response(message, context=""):
    try:
        api_key = os.environ.get("HF_TOKEN", "")
        if not api_key:
            return "HF_TOKEN not set."

        system_prompt = """You are a helpful customer support assistant for an energy monitoring system.
        Help users with questions about energy consumption, device monitoring, billing, and system features.
        Be friendly, professional, and provide accurate information about energy monitoring systems.
        If you don't know something specific, suggest contacting the system administrator."""

        prompt = system_prompt + f"\nUser: {message}"
        if context:
            prompt += f"\nContext: {context}"

        url = "https://router.huggingface.co/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {
            "model": "moonshotai/Kimi-K2-Instruct-0905",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            "max_tokens": 150,
            "temperature": 0.7
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            message_content = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
            return message_content or "AI response generated but empty."
        else:
            print(f"HF API Error: {response.status_code} {response.text}", flush=True)
            return "I'm sorry, I'm having trouble connecting to my knowledge base right now. Please try again later or contact support."
    except Exception as e:
        print(f"AI Error: {e}", flush=True)
        return "I'm sorry, I'm having trouble connecting to my knowledge base right now. Please try again later or contact support."

def handle_overconsumption_alert(message):
    print(f"[ALERT HANDLER] Received message: {message}", flush=True)
    message_type = message.get('type')
    data = message.get('data', {})
    
    if message_type == 'overconsumption_alert':
        with app.app_context():
            try:
                user_id = str(data.get('user_id'))
                device_id = data.get('device_id')
                consumption = data.get('consumption')
                threshold = data.get('threshold')
                
                alert_message = f"ALERT: Device {device_id} has exceeded its consumption limit! Current: {consumption:.2f} kWh, Maximum allowed: {threshold:.2f} kWh"
                
                print(f"[ALERT HANDLER] Processing overconsumption alert for user {user_id}, device {device_id}", flush=True)
                
                socketio.emit('overconsumption_notification', {
                    'user_id': user_id,
                    'device_id': device_id,
                    'consumption': consumption,
                    'threshold': threshold,
                    'message': alert_message,
                    'timestamp': datetime.now(UTC).isoformat()
                })
                
                print(f"[ALERT HANDLER] Overconsumption notification broadcast for user {user_id}", flush=True)
                
            except Exception as e:
                print(f"[ALERT HANDLER] Error handling overconsumption alert: {str(e)}", flush=True)
                import traceback
                traceback.print_exc()

print("[INIT] Registering RabbitMQ consumer for overconsumption_alerts...", flush=True)
rabbitmq_alert_consumer.consumeMessage(handle_overconsumption_alert)
print("[INIT] RabbitMQ consumer registered successfully", flush=True)

rabbitmq_alert_consumer.consumeMessage(handle_overconsumption_alert)


@socketio.on('connect')
def handle_connect():
    print(f"=== CLIENT CONNECTED: {request.sid}", flush=True)

@socketio.on('disconnect')
def handle_disconnect():
    print(f"=== CLIENT DISCONNECTED: {request.sid}", flush=True)

@socketio.on('join_chat')
def handle_join_chat(data):
    print(f"=== JOIN CHAT EVENT RECEIVED: {data}", flush=True)
    session_id = data.get('session_id')
    user_id = data.get('user_id')
    user_type = data.get('user_type', 'client')  

    join_room(session_id)
    print(f"User {user_id} joined room {session_id}", flush=True)

    session = ChatSession.query.filter_by(id=session_id).first()
    if session:
        session.last_activity = datetime.now(UTC)
        db.session.commit()

    emit('user_joined', {
        'user_id': user_id,
        'user_type': user_type,
        'timestamp': datetime.now(UTC).isoformat()
    }, room=session_id)

@socketio.on('leave_chat')
def handle_leave_chat(data):
    session_id = data.get('session_id')
    user_id = data.get('user_id')

    leave_room(session_id)
    emit('user_left', {'user_id': user_id}, room=session_id)

@socketio.on('send_message')
def handle_send_message(data):
    print(f"=== SEND MESSAGE EVENT RECEIVED: {data}", flush=True)
    try:
        session_id = data.get('session_id')
        sender_id = data.get('sender_id')
        content = data.get('content')
        sender_type = data.get('sender_type', 'client')

        print(f"Processing message: session={session_id}, sender={sender_id}, type={sender_type}", flush=True)

        message = Message(
            sender_id=sender_id,
            receiver_id='admin' if sender_type == 'client' else 'client',
            content=content,
            chat_session_id=session_id,
            message_type=sender_type
        )
        db.session.add(message)
        
        session = ChatSession.query.filter_by(id=session_id).first()
        if session:
            session.last_activity = datetime.now(UTC)
        
        db.session.commit()
        print(f"Message saved to database: {message.id}", flush=True)

        emit('new_message', {
            'id': message.id,
            'sender_id': sender_id,
            'content': content,
            'timestamp': message.timestamp.isoformat(),
            'message_type': sender_type
        }, room=session_id)
        
        print(f"Message broadcasted to room {session_id}", flush=True)

    except Exception as e:
        print(f"Error handling message: {e}", flush=True)
        import traceback
        traceback.print_exc()
        emit('error', {'message': 'Failed to send message'})

@socketio.on('typing_start')
def handle_typing_start(data):
    session_id = data.get('session_id')
    user_id = data.get('user_id')
    emit('typing_started', {'user_id': user_id}, room=session_id, skip_sid=True)

@socketio.on('typing_stop')
def handle_typing_stop(data):
    session_id = data.get('session_id')
    user_id = data.get('user_id')
    emit('typing_stopped', {'user_id': user_id}, room=session_id, skip_sid=True)

@socketio.on('mark_read')
def handle_mark_read(data):
    try:
        message_ids = data.get('message_ids', [])
        user_id = data.get('user_id')

        Message.query.filter(
            Message.id.in_(message_ids),
            Message.receiver_id == user_id
        ).update({'is_read': True})
        db.session.commit()

        emit('messages_read', {'message_ids': message_ids})
    except Exception as e:
        print(f"Error marking messages as read: {e}")

@app.route('/chat/api/sessions', methods=['POST'])
def create_session():
    try:
        data = request.get_json()
        client_id = data.get('client_id')
        admin_id = data.get('admin_id')

        session = ChatSession(client_id=client_id, admin_id=admin_id)
        db.session.add(session)
        db.session.commit()

        return jsonify({
            'session_id': session.id,
            'status': 'created',
            'created_at': session.created_at.isoformat()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/chat/api/sessions/<session_id>/messages', methods=['GET'])
def get_session_messages(session_id):
    try:
        messages = Message.query.filter_by(chat_session_id=session_id).order_by(Message.timestamp).all()
        return jsonify([{
            'id': msg.id,
            'sender_id': msg.sender_id,
            'receiver_id': msg.receiver_id,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat(),
            'is_read': msg.is_read,
            'message_type': msg.message_type
        } for msg in messages])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat/api/sessions/active', methods=['GET'])
def get_active_sessions():
    try:
        sessions = ChatSession.query.filter_by(status='active').all()
        return jsonify([{
            'id': session.id,
            'client_id': session.client_id,
            'admin_id': session.admin_id,
            'created_at': session.created_at.isoformat(),
            'last_activity': session.last_activity.isoformat()
        } for session in sessions])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat/api/notify/overconsumption', methods=['POST'])
def notify_overconsumption():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        device_id = data.get('device_id')
        consumption = data.get('consumption')
        threshold = data.get('threshold')

        message = f"Alert: Device {device_id} has exceeded consumption threshold. Current: {consumption}kWh, Threshold: {threshold}kWh"

        session = ChatSession.query.filter_by(client_id=user_id, status='active').first()
        if session:
            notification = Message(
                sender_id='system',
                receiver_id=user_id,
                content=message,
                chat_session_id=session.id,
                message_type='notification'
            )
            db.session.add(notification)
            db.session.commit()

            socketio.emit('new_message', {
                'id': notification.id,
                'sender_id': 'system',
                'content': message,
                'timestamp': notification.timestamp.isoformat(),
                'message_type': 'notification'
            }, room=session.id)

        return jsonify({'status': 'notification_sent'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/chat/api/ai-assist', methods=['POST'])
def ai_assist():
    try:
        data = request.get_json()
        message = data.get('message')
        session_id = data.get('session_id')
        
        context = ""
        if session_id:
            recent_messages = Message.query.filter_by(
                chat_session_id=session_id
            ).order_by(Message.timestamp.desc()).limit(5).all()
            context = "\n".join([f"{msg.sender_id}: {msg.content}" for msg in reversed(recent_messages)])
        

        rule_response = get_rule_based_response(message)
        if rule_response:
            return jsonify({
                'suggestion': rule_response,
                'type': 'rule_based'
            })
        

        ai_response = get_ai_response(message, context)
        return jsonify({
            'suggestion': ai_response,
            'type': 'ai'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat/api/ai-chat', methods=['POST'])
def ai_chat():
    try:
        data = request.get_json()
        message = data.get('message')
        user_id = data.get('user_id')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        rule_response = get_rule_based_response(message)
        if rule_response:
            return jsonify({
                'response': rule_response,
                'type': 'rule_based'
            })
        
        ai_response = get_ai_response(message, "")
        return jsonify({
            'response': ai_response,
            'type': 'ai'
        })
        
    except Exception as e:
        print(f"AI Chat Error: {e}", flush=True)
        return jsonify({'error': str(e)}), 500

def init_db():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    init_db()
    socketio.run(app, host='0.0.0.0', port=5005, debug=True, allow_unsafe_werkzeug=True)