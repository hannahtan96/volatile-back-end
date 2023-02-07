import os
import requests
import re
import json
from datetime import date, timedelta
from flask import Blueprint, request, jsonify, json
from dotenv import load_dotenv
from flatten_json import flatten
from pandas import json_normalize, DataFrame
from time import sleep

load_dotenv()

sentiment_bp = Blueprint("sentiment_bp", __name__, url_prefix='/sentiment_api')

SENTIMENT_KEY = os.environ.get("MEANING_CLOUD_API_KEY")
SENTIMENT_URL = 'https://api.meaningcloud.com/sentiment-2.1'
CONFIDENCE_CUTOFF = 85

# @sentiment_bp.route('', methods=['GET'])
def get_sentiment(text_input):
    print(f"in text_input: {text_input}")
    # text = request.get_json()["text"]
    params = {
        'key': SENTIMENT_KEY,
        'txt': text_input,
        'lang': "en"
    }

    try:
        sleep(1)
        response = requests.post(
            SENTIMENT_URL,
            data=params
        )

    except requests.exceptions.RequestException as e:
        print(e)

    text = response.json()

    if text["agreement"] == "DISAGREEMENT" or text["score_tag"] == "NONE" or int(text["confidence"]) < CONFIDENCE_CUTOFF:
        return False, False

    sentiment_headline = {
        "text": text["sentence_list"][0]["text"],
        "confidence": text["confidence"],
        "irony": text["irony"],
        "score_tag": text["score_tag"]
    }

    sentiment = flatten_json(text)

    return sentiment_headline, sentiment


def remove_beg_end_punctuation(s):
    i, j = 0, 0
    while i <= len(s)-1 and not s[i].isalnum():
        i += 1

    if i >= len(s)-1:
        return ''

    s = s[i:][::-1]
    while j <= len(s)-1 and not s[j].isalnum():
        j += 1

    return s[j:][::-1]


# @sentiment_bp.route('/flatten', methods=['GET'])
def flatten_json(input):
    print(f'in flatten_json')

    flattened_json = flatten(input)
    texts = [key for key, val in flattened_json.items() if key.endswith('text')]
    forms = [key for key, val in flattened_json.items() if key.endswith('form')]

    output, keys = [], set()

    for text in texts:
        if text[:len(text)-4]+'score_tag' in flattened_json and text[:len(text)-4]+'confidence' in flattened_json:
            text_sentiment = {
                "text": remove_beg_end_punctuation(flattened_json[text]),
                "score_tag": flattened_json[text[:len(text)-4]+'score_tag'],
                "confidence": flattened_json[text[:len(text)-4]+'confidence'],
            }

            if text_sentiment["text"] and text_sentiment["text"] not in keys and int(text_sentiment["confidence"]) >= CONFIDENCE_CUTOFF and text_sentiment["score_tag"] != "NONE":
                output.append(text_sentiment)
                keys.add(text_sentiment["text"])

    for form in forms:

        if re.search('sentimented_concept_list', form):
            list_name = 'sentimented_concept_list'
        elif re.search('sentimented_entity_list', form):
            list_name = 'sentimented_entity_list'

        res = [m.start() for m in re.finditer(list_name, form)][-1]

        form_sentiment = {
            "text" : remove_beg_end_punctuation(flattened_json[form]),
            "confidence": flattened_json[form[:res]+'confidence'],
            "score_tag": flattened_json[form[:len(form)-4]+'score_tag']
        }

        if form_sentiment["text"] and form_sentiment["text"] not in keys and form_sentiment["score_tag"] != 'NONE' and int(form_sentiment["confidence"]) >= CONFIDENCE_CUTOFF:
            output.append(form_sentiment)
            keys.add(form_sentiment["text"])

    return output

# sentence_list > segment_list > polarity_term_list > sentimented_concept_list
# sentence_list > segment_list > polarity_term_list > sentimented_concept_list > sentimented_entity_list

# @sentiment_bp.route('/flatten', methods=['GET'])
def return_sentiment(text):
    print(f'in return_sentiment')

    if text["agreement"] == "DISAGREEMENT":
        return False

    sentiment = {
        "text": text["sentence_list"][0]["text"],
        "confidence": text["confidence"],
        "irony": text["irony"],
        "score_tag": text["score_tag"]
    }

    return sentiment