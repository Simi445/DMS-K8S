from flask import Flask, request, jsonify
import jwt, os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-for-development-only') 


@app.route('/verify', methods=['GET', 'POST', 'PUT', 'DELETE'])
def validate_jwt_token():
    headers = request.headers
    auth = headers.get("Authorization")

    if not auth:
        response = {'error': 'Missing token in request body'}
        return app.response_class(
            response=json.dumps(response),
            status=400,
            mimetype='application/json'
        )

    token_to_validate = auth.split(' ')[1]
    secret_key = app.config['SECRET_KEY']
    algorithm = 'HS256'

    try:
        decoded_payload = jwt.decode(token_to_validate, secret_key, algorithms=[algorithm])
        response = {'payload': decoded_payload}
        return app.response_class(
            response=json.dumps(response),
            status=200,
            mimetype='application/json'
        )
    except jwt.ExpiredSignatureError:
        response = {'error': 'Token has expired. Please log in again.'}
        return app.response_class(
            response=json.dumps(response),
            status=401,
            mimetype='application/json'
        )
    except jwt.InvalidTokenError:
        response = {'error': 'Invalid token. Access denied.'}
        return app.response_class(
            response=json.dumps(response),
            status=401,
            mimetype='application/json'
        )
    except Exception as e:
        response = {'error': f'Internal server error: {str(e)}'}
        return app.response_class(
            response=json.dumps(response),
            status=500,
            mimetype='application/json'
        )



if __name__ == '__main__':
    app.run(debug = True, host='0.0.0.0', port=5003)