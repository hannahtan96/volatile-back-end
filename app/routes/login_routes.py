from functools import wraps
import firebase_admin
import pyrebase
import json
import os
import requests

from firebase_admin import credentials, auth, firestore
from flask import Blueprint, Flask, jsonify, request, redirect, request, url_for
from flask_cors import CORS
from datetime import date

# from .nyt_routes import get_position_sentiment

# Connect to firebase
cred = credentials.Certificate('./fbAdminConfig.json')
firebase = firebase_admin.initialize_app(cred)
pb = pyrebase.initialize_app(json.load(open('./fbConfig.json')))

db = firestore.client()
positions_ref = db.collection("positions")
users_portfolios_ref = db.collection("users")

AA_KEY = os.environ.get("ALPHA_ADVANTAGE_API_KEY")
AA_URL = 'https://www.alphavantage.co/query?'


login_bp = Blueprint("login_bp", __name__, url_prefix='/api')


def check_token(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        # print(request.headers)
        idToken = request.headers.get('Authorization')
        if not idToken:
            return {'message': 'No token provided'}, 400

        try:
            decoded_token = auth.verify_id_token(idToken)
            uid = decoded_token['uid']
            user = auth.get_user(uid)
            request.user = user
        except:
            return {'message': 'Invalid token provided'}, 400
        return f(*args, **kwargs)

    return wrap


@login_bp.route('/portfolio/new', methods=['POST'])
@check_token
def add_user_portfolio():
    print('in add_user_portfolio')
    request_body = request.get_json()
    user = request_body['user']
    email = request_body['email']
    localId = request_body['localId']
    portfolio = request_body['portfolio']
    print(portfolio)

    if email is None or email is None or localId is None or portfolio is None:
        return {'message': 'Error - missing user portfolio data'}, 400

    portfolio_detail = []
    error_detail = []
    for holding in portfolio:
      try:
        data = validate_ticker(holding["ticker"])["bestMatches"][0]
        print(data)
        n_data = {}
        n_data["ticker"] = data["1. symbol"]
        n_data["name"] = data["2. name"]
        n_data["shares"] = int(holding["shares"])
        portfolio_detail.append(n_data)
      except:
        error_detail.append(holding["ticker"])

    request_body["portfolio"] = portfolio_detail

    if error_detail:
      return jsonify({"non-existent tickers": ", ".join(error_detail)})

    try:
        print("in add_user_portfolio")
        users_portfolios_ref.document(localId).set(request_body)
        return redirect(url_for('login_bp.get_user_portfolio', localId=localId))
    except Exception as e:
        return f"An Error Occurred: {e}"


@login_bp.route('/portfolio/<localId>', methods=['GET'])
@check_token
def get_user_portfolio(localId):
    try:
        doc_ref = users_portfolios_ref.document(localId)
        doc = doc_ref.get()
        if doc.exists:
            print("doc does exist")
            return jsonify(doc.to_dict()), 200
        else:
            return jsonify({}), 200

    except Exception as e:
        return f"An Error Occurred: {e}"

# HELPER FUNCTION
def validate_ticker(ticker):
  try:
      # ticker = request.get_json()['ticker']
      response = requests.get(
          AA_URL + f'apikey={AA_KEY}&function=SYMBOL_SEARCH&keywords={ticker}'
      )
      data = json.loads(response.content.decode('utf-8'))
      return data
  except requests.exceptions.RequestException as e:
      return(e)


@login_bp.route('/portfolio/<localId>/tickers', methods=['GET'])
@check_token
def get_tickers(localId):

    try:
        doc_ref = users_portfolios_ref.document(localId)
        doc = doc_ref.get()
        if doc.exists:
            print("doc does exist")

            return_arr = []
            portfolio_dict = doc.to_dict()["portfolio"]

            for holding in portfolio_dict:

                data = verify_ticker(holding["ticker"])
                # ["Global Quote"]
                data["11. shares"] = holding["shares"]
                data["13. name"] = holding["name"]
                return_arr.append(data)

            total_weight = sum([(float(w['02. open'])*w['11. shares']) for w in return_arr])
            for holding in return_arr:
                holding["12. proportion"] = ((float(holding["02. open"])*holding["11. shares"]) / total_weight)

            return jsonify({"weightings": return_arr}), 200
        else:
            return jsonify({}), 200

    except requests.exceptions.RequestException as e:
        return(e)


def verify_ticker(ticker):
    try:
        response = requests.get(
            AA_URL + f'apikey={AA_KEY}&function=GLOBAL_QUOTE&symbol={ticker}'
        )
        data = json.loads(response.content.decode('utf-8'))
        print(data)
        return data["Global Quote"]
    except requests.exceptions.RequestException as e:
        return(e)

@login_bp.route('', methods=['GET'])
@check_token
def read_position():
    stock = "Netflix"
    ticker = "NFLX"
    articles = 10
    today = date.today().strftime('%Y%m%d')
    bespoke_id = today + "_" + ticker

    try:
        doc_ref = positions_ref.document(bespoke_id)
        doc = doc_ref.get()
        if doc.exists:
            print("doc does exist")
            return jsonify(doc.to_dict()), 200
        else:
            print("doc does not exist, so we will make it")
            response = create_position(stock, ticker, articles, today)
            print(response)
            if response["status_code"] == 200:
                new_doc = positions_ref.document(bespoke_id).get()
                return jsonify(new_doc.to_dict()), 200

    except Exception as e:
        return f"An Error Occurred: {e}"


#  HELPER FUNCTION
def create_position(stock, ticker, articles, today):
    try:
        print("in create_position")
        position = get_position_sentiment(stock, ticker, articles)
        # print(type(response))
        # position = json.loads(response)
        print(type(position))
        bespoke_id = today + "_" + ticker
        # id = position['']
        # position_ref.document(id).set(request.json)
        positions_ref.document(bespoke_id).set(position)
        return {"success": True, "status_code": 200}
    except Exception as e:
        return f"An Error Occurred: {e}"


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
        return {'message': 'Successful registration, please navigate to the Login page!', 'user_id': f'{user.uid}'}, 200
    except:
        return {'message': 'Error creating user'}, 400


@login_bp.route('/login', methods=['POST'])
def login():
    request_body = request.get_json()
    email = request_body['email']
    password = request_body['password']

    try:
        user = pb.auth().sign_in_with_email_and_password(email, password)
        # jwt = user['idToken']
        # return jsonify({'user': user, 'accessToken': jwt}), 200
        return user, 200

    except:
        return {'message': 'Incorrect email or password.'}, 400
