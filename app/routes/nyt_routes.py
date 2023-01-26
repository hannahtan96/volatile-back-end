import os
import requests
import re
from datetime import date, timedelta
from flask import Blueprint, request, jsonify, json
from dotenv import load_dotenv
from time import sleep

load_dotenv()

nyt_bp = Blueprint("nyt_bp", __name__, url_prefix='/nyt_api')

NYT_KEY = os.environ.get("NYT_API_KEY")
NYT_URL = 'https://api.nytimes.com/svc/search/v2/articlesearch.json'

@nyt_bp.route("/all", methods=['GET'])
def get_all_articles():
  all_new = {}



@nyt_bp.route("", methods=["GET"])
def get_articles():
  stock_query = request.get_json()["stock"]
  ticker_query = request.get_json()["ticker"]
  stock_or_ticker = stock_query + "|" + ticker_query
  articles = int(request.get_json()["articles"])

  today = date.today().strftime('%Y%m%d')
  today_less_30 = (date.today() - timedelta(days=90)).strftime('%Y%m%d')

  news = []
  flag = False
  try:
    page = 1
    while len(news) < articles+1:
      params={"api-key": NYT_KEY, "q": stock_query, "page": page, "news_desk": ("Business","Financial"), "begin_date": today_less_30, "end_date": today, "sort": "relevance"}
      response = requests.get(
        NYT_URL,
        params=params
      )

      data = json.loads(response.content.decode('utf-8'))
      for art in data['response']['docs']:
        if re.search(stock_or_ticker, art['headline']['main']) or re.search(stock_or_ticker, art['abstract']) or re.search(stock_or_ticker, art['snippet']):
          article = {
            "abstract": art['abstract'],
            "web_url": art['web_url'],
            "snippet": art['snippet'],
            "lead_paragraph": art['lead_paragraph'],
            "headline": art['headline']['main'],
            "print_headline": art['headline']['print_headline'],
            "keywords": [x["value"] for x in art['keywords']],
            "pub_date": art['pub_date'][:10],
            "word_count": art['word_count']
          }

          news.append(article)
          if len(news) == 10:
            flag = True
            break

      if flag:
        break

      if page > 10:
        sleep(6)

      page += 1

  except requests.exceptions.RequestException as e:
    print(e)

  return jsonify({"length":len(news),"articles":news})