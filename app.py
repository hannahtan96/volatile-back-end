from functools import wraps
import firebase_admin
import pyrebase
import json

from firebase_admin import credentials, auth
from flask import Flask, request, jsonify
from flask_cors import CORS

# app configuration
app = Flask(__name__)

CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

from .app.routes.nyt_routes import nyt_bp
app.register_blueprint(nyt_bp)

#Connect to firebase
cred = credentials.Certificate('fbAdminConfig.json')
firebase = firebase_admin.initialize_app(cred)
pb = pyrebase.initialize_app(json.load(open('fbConfig.json')))

users = [{'user_id': 1, 'first_name': 'Hannah', 'last_name': 'Tan'}]

def check_token(f):
  @wraps(f)
  def wrap(*args,**kwargs):
    if not request.headers.get_json()['authorization']:
      return {'message': 'No token provided'}, 400

    try:
      user = auth.verify_id_token(request.header['authorization'])
      request.user = user
    except:
      return {'message': 'Invalid token provided'}, 400
    return f(*args,**kwargs)

  return wrap


@app.route('/api/userinfo', methods=['POST'])
@check_token
def get_userinfo():
  return {'data':users}, 200

# https://medium.com/@nschairer/flask-api-authentication-with-firebase-9affc7b64715
@app.route('/api/signup', methods=['POST'])
def signup():
  request_body = request.get_json()
  first_name = request_body['firstName']
  last_name = request_body['lastName']
  username = request_body['username']
  email = request_body['email']
  password = request_body['password']

  if email is None or password is None:
    return {'message': 'Error - missing email or password'}, 400

  try:
    user = auth.create_user(
      password=password,
      email=email,
      display_name=username,
      disabled=False
    )
    return {'message':'Successful registration, please navigate to the Login page!', 'user_id': f'{user.uid}'}, 200
  except:
    return {'message': 'Error creating user'},400


@app.route('/api/login', methods=['POST'])
def login():
  request_body = request.get_json()
  email = request_body['email']
  password = request_body['password']

  try:
    user = pb.auth().sign_in_with_email_and_password(email, password)
    return user, 200

  except:
    return {'message': 'Incorrect email or password.'}, 400



if __name__ == '__main__':
  app.run(debug=True)
