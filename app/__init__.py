import os
from flask import Flask, request, jsonify
from firebase_admin import credentials, firestore, initialize_app, db
from flask_cors import CORS


def create_app():
    # app = Flask(__name__)
    cred = credentials.Certificate('../fbAdminconfig.json')
    databaseURL = {'databaseURL': 'https://volatile-d40b6-default-rtdb.firebaseio.com'}
    default_app = initialize_app(cred, databaseURL)
    # db = firestore.client()
    user_ref = db.reference('User')
    portfolio_ref = db.reference('Portfolio')
    holding_ref = db.reference('Holding')
    sentiment_ref = db.reference('Sentiment')



    CORS(default_app)
    default_app.config['CORS_HEADERS'] = 'Content-Type'

    return default_app
