from functools import wraps
import firebase_admin
import pyrebase
import json

from firebase_admin import credentials, auth
from flask import Blueprint, Flask, request, jsonify
from flask_cors import CORS

#Connect to firebase
cred = credentials.Certificate('./fbAdminConfig.json')
firebase = firebase_admin.initialize_app(cred)
pb = pyrebase.initialize_app(json.load(open('./fbConfig.json')))

users = [{'user_id': 1, 'first_name': 'Hannah', 'last_name': 'Tan'}]

login_bp = Blueprint("login_bp", __name__, url_prefix='/api')

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


@login_bp.route('/userinfo', methods=['POST'])
@check_token
def get_userinfo():
  return {'data':users}, 200

# https://medium.com/@nschairer/flask-api-authentication-with-firebase-9affc7b64715
@login_bp.route('/signup', methods=['POST'])
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


@login_bp.route('/login', methods=['POST'])
def login():
  request_body = request.get_json()
  email = request_body['email']
  password = request_body['password']

  try:
    user = pb.auth().sign_in_with_email_and_password(email, password)
    return user, 200

  except:
    return {'message': 'Incorrect email or password.'}, 400