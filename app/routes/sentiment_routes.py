import os
import requests
import re
from datetime import date, timedelta
from flask import Blueprint, request, jsonify, json
from dotenv import load_dotenv
from time import sleep

load_dotenv()

sentiment_bp = Blueprint("sentiment_bp", __name__, url_prefix='/sentiment_api')

SENTIMENT_KEY = os.environ.get("MEANING_CLOUD_API_KEY")
SENTIMENT_URL = 'https://api.meaningcloud.com/sentiment-2.1'

