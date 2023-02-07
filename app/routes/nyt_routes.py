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

from .sentiment_routes import remove_beg_end_punctuation


nyt_bp = Blueprint("nyt_bp", __name__, url_prefix='/nyt_api')

NYT_KEY = os.environ.get("NYT_API_KEY")
NYT_URL = 'https://api.nytimes.com/svc/search/v2/articlesearch.json'

BANNEDWORDS = {'BUT','THEN','IF','COULD','WHICH','HER','HIM','HAS','SINCE','BETWEEN','BEFORE','IN','THE','AN','A','ITS','OF','THIS','AND','AT','THERE','SHE','HE','HAVE','FROM','BEEN','IS','I','YOU','THAT','WAS','ON','ARE','WITH','BE','OR','HAD','BY','NOT','MOST'}

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
  print(f"in get_position_sentiment for {ticker_query}")
  s_list = stock_query.split()
  for elem in s_list:
    if elem.upper() not in BANNEDWORDS:
      s_query = elem
      break

  stock_or_ticker = s_query + "|" + ticker_query
  # articles = int(request.get_json()["articles"])

  today = date.today().strftime('%Y%m%d')
  today_less_90 = (date.today() - timedelta(days=90)).strftime('%Y%m%d')

  headliners, all_sentiments, sentiment_keys, freq_hash = [], [], set(), {}
  flag = False

  # print(s_query,ticker_query,articles)


  page = 1
  while not flag:

    try:
      params={"api-key": NYT_KEY, "q": s_query, "page": page, "news_desk": ("Business","Financial"), "begin_date": today_less_90, "end_date": today, "sort": "relevance"}
      response = requests.get(
        NYT_URL,
        params=params
      )

      data = json.loads(response.content.decode('utf-8'))
    except requests.exceptions.RequestException as e:
      print(f"get_position error: {e}")
      # print(data["response"]['docs'][7])

    for art in data['response']['docs']:
      # print(art['headline']['main'])
      if re.search(stock_or_ticker, art['headline']['main']) or re.search(stock_or_ticker, art['abstract']):
        article = {
          "abstract": art['abstract'],
          # "web_url": art['web_url'],
          # "snippet": art['snippet'],
          # "lead_paragraph": art['lead_paragraph'],
          "headline": art['headline']['main'],
          # "print_headline": art['headline']['print_headline'],
          # "keywords": [x["value"] for x in art['keywords']],
          # "pub_date": art['pub_date'][:10],
          # "word_count": art['word_count']
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
            normalized_str = remove_beg_end_punctuation(str).upper()  # remove punctation one more time
            if len(normalized_str) < 1 or normalized_str in BANNEDWORDS:
              continue

            if normalized_str not in freq_hash:
              freq_hash[normalized_str] = 0
            freq_hash[normalized_str] += 1

          print(len(headliners))
          if len(headliners) >= articles:
            flag = True
            break

    if flag:
      break

    if page > 10:
      sleep(6)

    page += 1

  score = mean([SCORE[h["score_tag"]] for h in headliners])
  # sorted_freq_hash = dict(sorted(freq_hash.items(), key=lambda item: item[1]))

  output = {"ticker":ticker_query,"sentiment_score":score,"headliners": headliners,"sentiments":all_sentiments,"words":freq_hash,"date":today}

  return output