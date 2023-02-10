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
from .sentiment_routes import get_sentiment, remove_beg_end_punctuation

load_dotenv()

nyt_bp = Blueprint("nyt_bp", __name__, url_prefix='/nyt_api')

NYT_KEY = os.environ.get("NYT_API_KEY")
NYT_URL = 'https://api.nytimes.com/svc/search/v2/articlesearch.json'

BANNEDWORDS = {'THE','AN','A','INC','CORPORATION','CORP','CO','LLC'}

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


def get_position_sentiment(stock_query, ticker_query, articles):
	print(f"in get_position_sentiment for {ticker_query}")
	s_list = stock_query.split()
	new_s_list = []
	for elem in s_list:
		if remove_beg_end_punctuation(elem) and remove_beg_end_punctuation(elem).upper() not in BANNEDWORDS:
			new_s_list.append(elem)
	s = ' '.join(new_s_list)
	s_query = s + "|" + new_s_list[0]
	print(s_query)

	stock_or_ticker = s_query + "|" + ticker_query
	# articles = int(request.get_json()["articles"])

	today = date.today().strftime('%Y%m%d')
	today_less_180 = (date.today() - timedelta(days=180)).strftime('%Y%m%d')

	headliners, all_sentiments, sentiment_keys, freq_hash = [], [], set(), {}
	flag = False
	print(s_query)
	page = 1
	while not flag:

		params={"api-key": NYT_KEY, "q": s, "page": page, "news_desk": ("Business","Financial","Sunday Business","Small Business","Personal Investing","DealBook","Opinion","OpEd","Society",""), "begin_date": today_less_180, "sort": "relevance"}
		response = requests.get(
			NYT_URL,
			params=params
		)

		if response.status_code == 200:
			data = response.json()
		elif response.status_code == 429:
			flag = True
			break

		if not data or len(data['response']['docs']) == 0:
			flag = True
			break

		if data['response']['docs']:
			print(data['response']['docs'])
			for art in data['response']['docs']:

				if re.search(stock_or_ticker, art['headline']['main']) or re.search(stock_or_ticker, art['abstract']):
					article = {
						"abstract": art['abstract'],
						"headline": art['headline']['main'],
						"keywords": [x["value"] for x in art['keywords']],
					}
					print(90)
					headliner, sentiments = get_sentiment(article['headline'])
					print(92)
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

	if headliners:
		score = mean([SCORE[h["score_tag"]] for h in headliners])
	else:
		score = -1

	output = {"ticker":ticker_query,"sentiment_score":score,"headliners": headliners,"sentiments":all_sentiments,"words":freq_hash,"date":today}

	return output

# print(get_position_sentiment('Amazon','AMZN',10))