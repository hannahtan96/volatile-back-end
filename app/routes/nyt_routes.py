import os
import requests
import re
import collections
from datetime import date, timedelta
from statistics import mean
from string import punctuation
from flask import Blueprint, request, jsonify, json
from dotenv import load_dotenv
from time import sleep
from .sentiment_routes import get_sentiment

load_dotenv()


nyt_bp = Blueprint("nyt_bp", __name__, url_prefix='/nyt_api')

NYT_KEY = os.environ.get("NYT_API_KEY")
NYT_URL = 'https://api.nytimes.com/svc/search/v2/articlesearch.json'

SCORE = {
  "P+": 1,
  "P": 0.75,
  "NEU": 0.5,
  "N": 0.25,
  "N+": 0,
  "NONE": 0.5
}

SCORE_DETAIL = {
  "P+": "strong positive",
  "P": "positive",
  "NEU": "neutral",
  "N": "negative",
  "N+": "strong negative",
  "NONE": "without polarity"
}

# @nyt_bp.route("", methods=["GET"])
def get_position_sentiment(stock_query, ticker_query, articles):
  # stock_query = request.get_json()["stock"]
  # ticker_query = request.get_json()["ticker"]
  stock_or_ticker = stock_query + "|" + ticker_query
  # articles = int(request.get_json()["articles"])

  today = date.today().strftime('%Y%m%d')
  today_less_90 = (date.today() - timedelta(days=90)).strftime('%Y%m%d')

  headliners, all_sentiments, sentiment_keys, freq_hash = [], [], set(), {}
  flag = False

  try:
    page = 1
    while not flag:
      params={"api-key": NYT_KEY, "q": stock_query, "page": page, "news_desk": ("Business","Financial"), "begin_date": today_less_90, "end_date": today, "sort": "relevance"}
      response = requests.get(
        NYT_URL,
        params=params
      )

      data = json.loads(response.content.decode('utf-8'))

      for art in data['response']['docs']:
        if re.search(stock_or_ticker, art['headline']['main']) or re.search(stock_or_ticker, art['abstract']):
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

          headliner, sentiments = get_sentiment(article['headline'])

          if headliner:

            headliners.append(headliner)

            for sentiment in sentiments:
              if sentiment["text"] not in sentiment_keys:
                sentiment_keys.add(sentiment["text"])
                all_sentiments.append(sentiment)


            abstract_strings = article["abstract"].split()
            for str in abstract_strings:
              normalized_str = str.strip(punctuation).upper()
              if normalized_str not in freq_hash:
                freq_hash[normalized_str] = 0
              freq_hash[normalized_str] += 1

            if len(headliners) >= articles:
              flag = True
              break

      if flag:
        break

      if page > 10:
        sleep(6)

      page += 1

  except requests.exceptions.RequestException as e:
    print(e)

  score = mean([SCORE[h["score_tag"]] for h in headliners])
  sorted_freq_hash = dict(sorted(freq_hash.items(), key=lambda item: item[1]))

  output = {"ticker":ticker_query,"sentiment_score":score,"headliners": headliners,"sentiments":all_sentiments,"words":sorted_freq_hash,"date":today}

  return output

sample = {
    "date": "20230126",
    "frequencies": {
        "69": 3,
        "A": 3,
        "ACQUISITION": 2,
        "ACTIVISION": 1,
        "AGENCY": 1,
        "AGENDA": 1,
        "AGGRESSIVE": 1,
        "AMBITIOUS": 1,
        "AN": 3,
        "AND": 1,
        "ANTITRUST": 1,
        "APPEARS": 1,
        "BE": 2,
        "BIGGEST": 1,
        "BILLION": 3,
        "BLIZZARD": 1,
        "BLOCK": 2,
        "BRANCH": 1,
        "BUT": 1,
        "BY": 2,
        "CASE": 1,
        "CHAIR": 1,
        "CLOSED-DOOR": 1,
        "COMMISSION": 3,
        "COMPANIES": 1,
        "COMPANY": 1,
        "COULD": 1,
        "DIFFICULT": 1,
        "EVEN": 1,
        "EXPANSION": 1,
        "FEDERAL": 4,
        "FORCE": 1,
        "FORWARD": 1,
        "HAS": 2,
        "HAVE": 1,
        "HOPING": 1,
        "IF": 1,
        "IN": 2,
        "INDUSTRY’S": 1,
        "IS": 2,
        "ISSUE": 1,
        "IT": 1,
        "KHAN": 1,
        "LOSES": 1,
        "MAY": 1,
        "MOVE": 2,
        "MS": 1,
        "NATION’S": 1,
        "OF": 3,
        "OLIVE": 1,
        "ON": 3,
        "OPPOSE": 1,
        "PATH": 1,
        "PREPARING": 1,
        "REGULATORS": 2,
        "REVAMP": 1,
        "RULES": 1,
        "SEEKING": 1,
        "SESSION": 1,
        "SETTLED": 1,
        "SIGNALS": 1,
        "STAKED": 1,
        "STANCE": 1,
        "SUED": 1,
        "TAKEOVER": 1,
        "TECH": 1,
        "THAT": 1,
        "THE": 15,
        "THURSDAY": 1,
        "THWART": 1,
        "TO": 9,
        "TRADE": 2,
        "TRUSTBUSTING": 1,
        "VOTE": 1,
        "WHICH": 1,
        "WIN": 1,
        "—": 1
    },
    "sentiments": [
        {
            "confidence": "100",
            "score_tag": "N",
            "text": "close@V"
        },
        {
            "confidence": "100",
            "score_tag": "P",
            "text": "nice"
        },
        {
            "confidence": "100",
            "score_tag": "P",
            "text": "Nice Guy"
        },
        {
            "confidence": "100",
            "score_tag": "N",
            "text": "Microsoft Gambles on ‘Nice Guy’ Strategy to Close Activision Megadeal"
        },
        {
            "confidence": "100",
            "score_tag": "N",
            "text": "strategy"
        },
        {
            "confidence": "100",
            "score_tag": "N",
            "text": "Microsoft Corporation"
        },
        {
            "confidence": "100",
            "score_tag": "N",
            "text": "Gamble"
        },
        {
            "confidence": "100",
            "score_tag": "N",
            "text": "Guy"
        },
        {
            "confidence": "100",
            "score_tag": "N",
            "text": "block@V"
        },
        {
            "confidence": "100",
            "score_tag": "N",
            "text": "Lina Khan, Aiming to Block Microsoft’s Activision Deal, Faces a Challenge"
        },
        {
            "confidence": "100",
            "score_tag": "N",
            "text": "face"
        },
        {
            "confidence": "100",
            "score_tag": "N",
            "text": "Lina Khan"
        },
        {
            "confidence": "100",
            "score_tag": "N",
            "text": "sue"
        },
        {
            "confidence": "92",
            "score_tag": "N",
            "text": "(block) acquisition"
        },
        {
            "confidence": "100",
            "score_tag": "P",
            "text": "acquisition"
        },
        {
            "confidence": "100",
            "score_tag": "P",
            "text": "Microsoft’s $69 Billion Acquisition of Activision"
        },
        {
            "confidence": "92",
            "score_tag": "N",
            "text": "F.T.C. Sues to Block Microsoft’s $69 Billion Acquisition of Activision"
        },
        {
            "confidence": "100",
            "score_tag": "N",
            "text": "dollar"
        },
        {
            "confidence": "100",
            "score_tag": "N",
            "text": "Activision Blizzard, Inc"
        },
        {
            "confidence": "100",
            "score_tag": "N",
            "text": "to Block Microsoft’s Big Deal"
        },
        {
            "confidence": "100",
            "score_tag": "N",
            "text": "The Stakes Behind the F.T.C.’s Bid to Block Microsoft’s Big Deal"
        },
        {
            "confidence": "100",
            "score_tag": "N",
            "text": "stake"
        },
        {
            "confidence": "100",
            "score_tag": "N",
            "text": "Microsoft to Offer Call of Duty on Nintendo Devices if Activision Deal Closes"
        }
    ],
    "ticker": "MSFT"
}