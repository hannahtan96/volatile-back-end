import os
from flask import Flask, request, jsonify
from firebase_admin import credentials, firestore, initialize_app, db
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    # cred = credentials.Certificate('../fbAdminconfig.json')
    # databaseURL = {'databaseURL': 'https://volatile-d40b6-default-rtdb.firebaseio.com'}
    # default_app = initialize_app(cred)

    # db = firestore.client()
    # position_ref = db.collection('position')
    # user_ref = db.reference('ser')
    # sentiment_ref = db.reference('Sentiment')

    from .routes.nyt_routes import nyt_bp
    app.register_blueprint(nyt_bp)

    from .routes.login_routes import login_bp
    app.register_blueprint(login_bp)

    from .routes.sentiment_routes import sentiment_bp
    app.register_blueprint(sentiment_bp)

    CORS(app)
    app.config['CORS_HEADERS'] = 'Content-Type'

    return app
