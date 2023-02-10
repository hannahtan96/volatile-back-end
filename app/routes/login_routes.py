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
from .nyt_routes import get_position_sentiment

# Connect to firebase
cred = credentials.Certificate(os.path.abspath(os.path.dirname(__file__)) + '/fbAdminConfig.json')
firebase = firebase_admin.initialize_app(cred)
pb = pyrebase.initialize_app(json.load(open(os.path.abspath(os.path.dirname(__file__)) + '/fbConfig.json')))

db = firestore.client()
positions_ref = db.collection("positions")
users_portfolios_ref = db.collection("users")

AA_KEY = os.environ.get("ALPHA_ADVANTAGE_API_KEY")
AA_URL = "https://www.alphavantage.co/query?"

FH_KEY = os.environ.get("FH_API_KEY")
FH_URL = "https://finnhub.io/api/v1"

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

# HELPER
def read_position(stock, ticker):
	print(f'reading position for {stock}')
	articles = 10
	today = date.today().strftime('%Y%m%d')
	bespoke_id = today + "_" + ticker

	try:
		doc_ref = positions_ref.document(bespoke_id)
		doc = doc_ref.get()
		if doc.exists:
			print("doc does exist")
			return doc.to_dict()
		else:
			print(f"{ticker} does not exist, so we will make it")
			response = create_position(stock, ticker, articles, today)

			if response["status_code"] == 200:
				new_doc = positions_ref.document(bespoke_id).get()
				return new_doc.to_dict()

	except Exception as e:
		return f"read_position Error Occurred: {e}"

#  HELPER
def create_position(stock, ticker, articles, today):
    try:
        print("in create_position")
        position = get_position_sentiment(stock, ticker, articles)
        bespoke_id = today + "_" + ticker
        positions_ref.document(bespoke_id).set(position)
        return {"success": True, "status_code": 200}
    except Exception as e:
        return f"create_position Error Occurred: {e}"

# HELPER
def verify_ticker(ticker):
	print(ticker)
	try:
		response = requests.get(
			FH_URL + f'/quote?symbol={ticker}&token={FH_KEY}'
		)

		if response.status_code == 200:
			data = response.json()
		else:
			return 'Quote limit reached. Wait a minute and rerun.'

		if not data:
			return 'Quote limited reached. Wait a minute and rerun.'

		return data
	except requests.exceptions.RequestException as e:
		return(e)

# HELPER
def validate_ticker(ticker):
	try:
		response = requests.get(
			FH_URL + f'/search?q={ticker}&token={FH_KEY}'
		)

		data = response.json()
		return data
	except requests.exceptions.RequestException as e:
		return(e)


# ENDPOINT
@login_bp.route('/ticker', methods=['POST'])
@check_token
def validate_ticker_ep():
	request_body = request.get_json()
	ticker = request_body["data"]["ticker"]

	r = validate_ticker(ticker)
	return jsonify({"tickers": r}), 200


# ENDPOINT
@login_bp.route('/portfolio/new', methods=['POST'])
@check_token
def add_user_portfolio():
	print('in add_user_portfolio')
	request_body = request.get_json()
	user = request_body['user']
	email = request_body['email']
	localId = request_body['localId']
	portfolio = request_body['portfolio']

	if user is None or email is None or localId is None or portfolio is None:
		return {'message': 'Error - missing user portfolio data'}, 400

	portfolio_detail = []
	error_detail = []
	for holding in portfolio:
		try:
			data = validate_ticker(holding["ticker"])["result"][0]

			n_data = {}
			n_data["ticker"] = data["symbol"]
			n_data["name"] = data["description"]
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


# ENDPOINT
@login_bp.route('/portfolio/<localId>/edit', methods=['POST'])
@check_token
def edit_user_portfolio(localId):
	request_body = request.get_json()
	t = request_body["data"]["ticker"]
	s = int(request_body["data"]["shares"])

	try:
		doc_ref = users_portfolios_ref.document(localId)
		doc = doc_ref.get()

		portfolio_dict = doc.to_dict()["portfolio"]
		curr_holding = [holding for holding in portfolio_dict if holding["ticker"] == t]

		if curr_holding:doc_ref.update({'portfolio': firestore.ArrayRemove(curr_holding)})

	except Exception as e:
		return f"An Error Occurred: {e}"

	try:
		if s:
			data = validate_ticker(t)["result"][0]
			n_data = {}
			n_data["ticker"] = data["symbol"]
			n_data["name"] = data["description"]
			n_data["shares"] = s

	except Exception as e:
		return f"An Error Occurred: {e}"

	try:
		if s:
			doc_ref = users_portfolios_ref.document(localId)
			doc_ref.update({'portfolio': firestore.ArrayUnion([n_data])})
			return redirect(url_for('login_bp.get_user_portfolio', localId=localId))

	except Exception as e:
		return f"An Error Occurred: {e}"


# ENDPOINT
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


# ENDPOINT
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
				print(holding)

				data = verify_ticker(holding["ticker"])

				if isinstance(data, str):
					return jsonify({'error': data})
				data["symbol"] = holding["ticker"]
				data["shares"] = holding["shares"]
				data["name"] = holding["name"]
				return_arr.append(data)

			total_weight = sum([(float(w['o'])*w['shares']) for w in return_arr])
			for holding in return_arr:
				holding["proportion"] = ((float(holding["o"])*holding["shares"]) / total_weight)

			return jsonify({"weightings": return_arr}), 200
		else:
			return jsonify({}), 200

	except requests.exceptions.RequestException as e:
		return(e)


# ENDPOINT
@login_bp.route('/sentiments', methods=['POST'])
@check_token
def read_positions():
	request_body = request.get_json()
	portfolio = request_body["portfolio"]
	print(portfolio)
	num_holdings = len(portfolio)

	positions = []
	for holding in portfolio:
		print(holding)
		holding_sentiment = read_position(holding["name"],holding["ticker"])
		if isinstance(holding_sentiment, str):
			break

		positions.append(holding_sentiment)

	if len(positions) != num_holdings:
		return jsonify({"message": "error in finding sentiments"}), 400

	return jsonify({"portfolio": positions}), 200


# https://medium.com/@nschairer/flask-api-authentication-with-firebase-9affc7b64715
# ENDPOINT
@login_bp.route('/signup', methods=['POST'])
def signup():
    request_body = request.get_json()
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


# ENDPOINT
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
