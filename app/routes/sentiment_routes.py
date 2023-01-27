import os
import requests
import re
import json
from datetime import date, timedelta
from flask import Blueprint, request, jsonify, json
from dotenv import load_dotenv
from flatten_json import flatten
from pandas import json_normalize, DataFrame

load_dotenv()

sentiment_bp = Blueprint("sentiment_bp", __name__, url_prefix='/sentiment_api')

SENTIMENT_KEY = os.environ.get("MEANING_CLOUD_API_KEY")
SENTIMENT_URL = 'https://api.meaningcloud.com/sentiment-2.1'

CONFIDENCE_CUTOFF = 90

# @sentiment_bp.route('', methods=['GET'])
def get_sentiment(text):
  # text = request.get_json()["text"]
  params = {
      'key': SENTIMENT_KEY,
      'txt': text,
      'lang': "en"
  }

  try:
    response = requests.post(
      SENTIMENT_URL,
      data=params
    )

  except requests.exceptions.RequestException as e:
    print(e)

  text = response.json()

  if text["agreement"] == "DISAGREEMENT" or int(text["confidence"]) < CONFIDENCE_CUTOFF:
    return False, False

  sentiment_headline = {
    "text": text["sentence_list"][0]["text"],
    "confidence": text["confidence"],
    "irony": text["irony"],
    "score_tag": text["score_tag"]
  }

  sentiment = flatten_json(text)

  return sentiment_headline, sentiment

# @sentiment_bp.route('/flatten', methods=['GET'])
def flatten_json(input):
  flattened_json = flatten(input)
  texts = [key for key, val in flattened_json.items() if key.endswith('text')]
  forms = [key for key, val in flattened_json.items() if key.endswith('form')]

  output, keys = [], set()

  for text in texts:
    if text[:len(text)-4]+'score_tag' in flattened_json and text[:len(text)-4]+'confidence' in flattened_json:
      text_sentiment = {
        "text": flattened_json[text].rstrip("."),
        "score_tag": flattened_json[text[:len(text)-4]+'score_tag'],
        "confidence": flattened_json[text[:len(text)-4]+'confidence'],
      }

      if text_sentiment["text"] not in keys and int(text_sentiment["confidence"]) >= CONFIDENCE_CUTOFF:
        output.append(text_sentiment)
        keys.add(text_sentiment["text"])

  for form in forms:

    if re.search('sentimented_concept_list', form):
      list_name = 'sentimented_concept_list'
    elif re.search('sentimented_entity_list', form):
      list_name = 'sentimented_entity_list'

    res = [m.start() for m in re.finditer(list_name, form)][-1]

    form_sentiment = {
      "text" : flattened_json[form].rstrip("."),
      "confidence": flattened_json[form[:res]+'confidence'],
      # "overall_score_tag": flattened_json[form[:res]+'score_tag'],
      "score_tag": flattened_json[form[:len(form)-4]+'score_tag']
    }

    if form_sentiment["text"] not in keys and form_sentiment["score_tag"] != 'NONE' and int(form_sentiment["confidence"]) >= CONFIDENCE_CUTOFF:
        output.append(form_sentiment)
        keys.add(form_sentiment["text"])

  return output
  # return flattened_json, 200

# sentence_list > segment_list > polarity_term_list > sentimented_concept_list
# sentence_list > segment_list > polarity_term_list > sentimented_concept_list > sentimented_entity_list

# @sentiment_bp.route('/flatten', methods=['GET'])
def return_sentiment(text):

  if text["agreement"] == "DISAGREEMENT":
    return None

  sentiment = {
    "text": text["sentence_list"][0]["text"],
    "confidence": text["confidence"],
    "irony": text["irony"],
    "score_tag": text["score_tag"]
  }

  return sentiment



# def flatten(d):
#   out = {}
#   for key, val in d.items():
#       if isinstance(val, dict):
#           val = [val]
#       if isinstance(val, list):
#           for subdict in val:
#               deeper = flatten(subdict).items()
#               out.update({key + '_' + key2: val2 for key2, val2 in deeper})
#       else:
#           out[key] = val
#   return out

# print(flatten(sample_json))


sample_json = {
    "agreement": "AGREEMENT",
    "confidence": "92",
    "irony": "NONIRONIC",
    "model": "general_en",
    "score_tag": "N",
    "sentence_list": [
        {
            "agreement": "AGREEMENT",
            "bop": "y",
            "confidence": "92",
            "endp": "70",
            "inip": "0",
            "score_tag": "N",
            "segment_list": [
                {
                    "agreement": "AGREEMENT",
                    "confidence": "92",
                    "endp": "69",
                    "inip": "0",
                    "polarity_term_list": [
                        {
                            "confidence": "100",
                            "endp": "10",
                            "inip": "7",
                            "score_tag": "N",
                            "sentimented_concept_list": [
                                {
                                    "endp": "33",
                                    "form": "dollar",
                                    "id": "7b6858c50a",
                                    "inip": "33",
                                    "score_tag": "N",
                                    "type": "Top>Unit>Currency",
                                    "variant": "$"
                                },
                                {
                                    "endp": "55",
                                    "form": "acquisition",
                                    "id": "44bf285093",
                                    "inip": "45",
                                    "score_tag": "N",
                                    "type": "Top>Process",
                                    "variant": "Acquisition"
                                }
                            ],
                            "sentimented_entity_list": [
                                {
                                    "endp": "29",
                                    "form": "Microsoft Corporation",
                                    "id": "4034a1ee63",
                                    "inip": "21",
                                    "score_tag": "N",
                                    "type": "Top>Organization>Company>TechnologyCompany>SoftwareCompany",
                                    "variant": "Microsoft"
                                },
                                {
                                    "endp": "69",
                                    "form": "Activision Blizzard, Inc.",
                                    "id": "772347c81b",
                                    "inip": "60",
                                    "score_tag": "N",
                                    "type": "Top>Organization>Company>TechnologyCompany>SoftwareCompany",
                                    "variant": "Activision"
                                }
                            ],
                            "text": "sue"
                        },
                        {
                            "confidence": "92",
                            "endp": "55",
                            "inip": "45",
                            "score_tag": "N",
                            "sentimented_concept_list": [
                                {
                                    "endp": "33",
                                    "form": "dollar",
                                    "id": "7b6858c50a",
                                    "inip": "33",
                                    "score_tag": "N",
                                    "type": "Top>Unit>Currency",
                                    "variant": "$"
                                },
                                {
                                    "endp": "55",
                                    "form": "acquisition",
                                    "id": "44bf285093",
                                    "inip": "45",
                                    "score_tag": "N",
                                    "type": "Top>Process",
                                    "variant": "Acquisition"
                                }
                            ],
                            "sentimented_entity_list": [
                                {
                                    "endp": "29",
                                    "form": "Microsoft Corporation",
                                    "id": "4034a1ee63",
                                    "inip": "21",
                                    "score_tag": "N",
                                    "type": "Top>Organization>Company>TechnologyCompany>SoftwareCompany",
                                    "variant": "Microsoft"
                                },
                                {
                                    "endp": "69",
                                    "form": "Activision Blizzard, Inc.",
                                    "id": "772347c81b",
                                    "inip": "60",
                                    "score_tag": "N",
                                    "type": "Top>Organization>Company>TechnologyCompany>SoftwareCompany",
                                    "variant": "Activision"
                                }
                            ],
                            "text": "(block) acquisition"
                        }
                    ],
                    "score_tag": "N",
                    "segment_list": [
                        {
                            "agreement": "AGREEMENT",
                            "confidence": "100",
                            "endp": "69",
                            "inip": "21",
                            "polarity_term_list": [
                                {
                                    "confidence": "100",
                                    "endp": "55",
                                    "inip": "45",
                                    "score_tag": "P",
                                    "sentimented_concept_list": [
                                        {
                                            "endp": "33",
                                            "form": "dollar",
                                            "id": "7b6858c50a",
                                            "inip": "33",
                                            "score_tag": "P",
                                            "type": "Top>Unit>Currency",
                                            "variant": "$"
                                        },
                                        {
                                            "endp": "55",
                                            "form": "acquisition",
                                            "id": "44bf285093",
                                            "inip": "45",
                                            "score_tag": "P",
                                            "type": "Top>Process",
                                            "variant": "Acquisition"
                                        }
                                    ],
                                    "sentimented_entity_list": [
                                        {
                                            "endp": "29",
                                            "form": "Microsoft Corporation",
                                            "id": "4034a1ee63",
                                            "inip": "21",
                                            "score_tag": "P",
                                            "type": "Top>Organization>Company>TechnologyCompany>SoftwareCompany",
                                            "variant": "Microsoft"
                                        },
                                        {
                                            "endp": "69",
                                            "form": "Activision Blizzard, Inc.",
                                            "id": "772347c81b",
                                            "inip": "60",
                                            "score_tag": "P",
                                            "type": "Top>Organization>Company>TechnologyCompany>SoftwareCompany",
                                            "variant": "Activision"
                                        }
                                    ],
                                    "text": "acquisition"
                                }
                            ],
                            "score_tag": "P",
                            "segment_type": "main",
                            "text": "Microsoft’s $69 Billion Acquisition of Activision"
                        }
                    ],
                    "segment_type": "main",
                    "text": "F.T.C. Sues to Block Microsoft’s $69 Billion Acquisition of Activision"
                }
            ],
            "sentimented_concept_list": [
                {
                    "form": "acquisition",
                    "id": "44bf285093",
                    "score_tag": "N",
                    "type": "Top>Process"
                },
                {
                    "form": "dollar",
                    "id": "7b6858c50a",
                    "score_tag": "N",
                    "type": "Top>Unit>Currency"
                }
            ],
            "sentimented_entity_list": [
                {
                    "form": "Microsoft Corporation",
                    "id": "4034a1ee63",
                    "score_tag": "N",
                    "type": "Top>Organization>Company>TechnologyCompany>SoftwareCompany"
                },
                {
                    "form": "Activision Blizzard, Inc.",
                    "id": "772347c81b",
                    "score_tag": "N",
                    "type": "Top>Organization>Company>TechnologyCompany>SoftwareCompany"
                }
            ],
            "text": "F.T.C. Sues to Block Microsoft’s $69 Billion Acquisition of Activision."
        }
    ],
    "sentimented_concept_list": [
        {
            "form": "acquisition",
            "id": "44bf285093",
            "score_tag": "N",
            "type": "Top>Process"
        },
        {
            "form": "dollar",
            "id": "7b6858c50a",
            "score_tag": "N",
            "type": "Top>Unit>Currency"
        }
    ],
    "sentimented_entity_list": [
        {
            "form": "Microsoft Corporation",
            "id": "4034a1ee63",
            "score_tag": "N",
            "type": "Top>Organization>Company>TechnologyCompany>SoftwareCompany"
        },
        {
            "form": "Activision Blizzard, Inc.",
            "id": "772347c81b",
            "score_tag": "N",
            "type": "Top>Organization>Company>TechnologyCompany>SoftwareCompany"
        }
    ],
    "status": {
        "code": "0",
        "credits": "1",
        "msg": "OK",
        "remaining_credits": "19998"
    },
    "subjectivity": "OBJECTIVE"
}

sample_json_2 = {
    "agreement": "AGREEMENT",
    "confidence": "100",
    "irony": "NONIRONIC",
    "model": "general_en",
    "score_tag": "P",
    "sentence_list": [
        {
            "agreement": "AGREEMENT",
            "bop": "y",
            "confidence": "100",
            "endp": "232",
            "inip": "0",
            "score_tag": "P",
            "segment_list": [
                {
                    "agreement": "AGREEMENT",
                    "confidence": "100",
                    "endp": "231",
                    "inip": "0",
                    "polarity_term_list": [
                        {
                            "confidence": "100",
                            "endp": "146",
                            "inip": "139",
                            "score_tag": "P",
                            "sentimented_concept_list": [
                                {
                                    "endp": "81",
                                    "form": "chair",
                                    "id": "38e4c77d77",
                                    "inip": "77",
                                    "score_tag": "P",
                                    "type": "Top>Location>Facility",
                                    "variant": "chair"
                                },
                                {
                                    "endp": "163",
                                    "form": "dollar",
                                    "id": "7b6858c50a",
                                    "inip": "163",
                                    "score_tag": "P",
                                    "type": "Top>Unit>Currency",
                                    "variant": "$"
                                },
                                {
                                    "endp": "185",
                                    "form": "acquisition",
                                    "id": "44bf285093",
                                    "inip": "175",
                                    "score_tag": "P",
                                    "type": "Top>Process",
                                    "variant": "acquisition"
                                },
                                {
                                    "endp": "198",
                                    "form": "video",
                                    "id": "828aabda8c",
                                    "inip": "194",
                                    "score_tag": "P",
                                    "type": "Top>Product>CulturalProduct",
                                    "variant": "video"
                                },
                                {
                                    "endp": "203",
                                    "form": "match",
                                    "id": "8462e12559",
                                    "inip": "200",
                                    "score_tag": "P",
                                    "type": "Top>Event>Occasion>Games",
                                    "variant": "game"
                                },
                                {
                                    "endp": "211",
                                    "form": "company",
                                    "id": "420c1836d7",
                                    "inip": "205",
                                    "score_tag": "P",
                                    "type": "Top>Organization>Company",
                                    "variant": "company"
                                }
                            ],
                            "sentimented_entity_list": [
                                {
                                    "endp": "27",
                                    "form": "Brad Smith",
                                    "id": "__16524428015425899337",
                                    "inip": "18",
                                    "score_tag": "P",
                                    "type": "Top>Person>FullName",
                                    "variant": "Brad Smith"
                                },
                                {
                                    "endp": "70",
                                    "form": "Lina Khan",
                                    "id": "__1289069509110257451",
                                    "inip": "62",
                                    "score_tag": "P",
                                    "type": "Top>Person>FullName",
                                    "variant": "Lina Khan"
                                },
                                {
                                    "endp": "159",
                                    "form": "Microsoft Corporation",
                                    "id": "4034a1ee63",
                                    "inip": "151",
                                    "score_tag": "P",
                                    "type": "Top>Organization>Company>TechnologyCompany>SoftwareCompany",
                                    "variant": "Microsoft"
                                },
                                {
                                    "endp": "231",
                                    "form": "Activision Blizzard, Inc.",
                                    "id": "772347c81b",
                                    "inip": "213",
                                    "score_tag": "P",
                                    "type": "Top>Organization>Company>TechnologyCompany>SoftwareCompany",
                                    "variant": "Activision Blizzard"
                                }
                            ],
                            "text": "approval"
                        },
                        {
                            "confidence": "100",
                            "endp": "185",
                            "inip": "175",
                            "score_tag": "P",
                            "sentimented_concept_list": [
                                {
                                    "endp": "81",
                                    "form": "chair",
                                    "id": "38e4c77d77",
                                    "inip": "77",
                                    "score_tag": "P",
                                    "type": "Top>Location>Facility",
                                    "variant": "chair"
                                },
                                {
                                    "endp": "163",
                                    "form": "dollar",
                                    "id": "7b6858c50a",
                                    "inip": "163",
                                    "score_tag": "P",
                                    "type": "Top>Unit>Currency",
                                    "variant": "$"
                                },
                                {
                                    "endp": "185",
                                    "form": "acquisition",
                                    "id": "44bf285093",
                                    "inip": "175",
                                    "score_tag": "P",
                                    "type": "Top>Process",
                                    "variant": "acquisition"
                                },
                                {
                                    "endp": "198",
                                    "form": "video",
                                    "id": "828aabda8c",
                                    "inip": "194",
                                    "score_tag": "P",
                                    "type": "Top>Product>CulturalProduct",
                                    "variant": "video"
                                },
                                {
                                    "endp": "203",
                                    "form": "match",
                                    "id": "8462e12559",
                                    "inip": "200",
                                    "score_tag": "P",
                                    "type": "Top>Event>Occasion>Games",
                                    "variant": "game"
                                },
                                {
                                    "endp": "211",
                                    "form": "company",
                                    "id": "420c1836d7",
                                    "inip": "205",
                                    "score_tag": "P",
                                    "type": "Top>Organization>Company",
                                    "variant": "company"
                                }
                            ],
                            "sentimented_entity_list": [
                                {
                                    "endp": "27",
                                    "form": "Brad Smith",
                                    "id": "__16524428015425899337",
                                    "inip": "18",
                                    "score_tag": "P",
                                    "type": "Top>Person>FullName",
                                    "variant": "Brad Smith"
                                },
                                {
                                    "endp": "70",
                                    "form": "Lina Khan",
                                    "id": "__1289069509110257451",
                                    "inip": "62",
                                    "score_tag": "P",
                                    "type": "Top>Person>FullName",
                                    "variant": "Lina Khan"
                                },
                                {
                                    "endp": "159",
                                    "form": "Microsoft Corporation",
                                    "id": "4034a1ee63",
                                    "inip": "151",
                                    "score_tag": "P",
                                    "type": "Top>Organization>Company>TechnologyCompany>SoftwareCompany",
                                    "variant": "Microsoft"
                                },
                                {
                                    "endp": "231",
                                    "form": "Activision Blizzard, Inc.",
                                    "id": "772347c81b",
                                    "inip": "213",
                                    "score_tag": "P",
                                    "type": "Top>Organization>Company>TechnologyCompany>SoftwareCompany",
                                    "variant": "Activision Blizzard"
                                }
                            ],
                            "text": "acquisition"
                        }
                    ],
                    "score_tag": "P",
                    "segment_list": [
                        {
                            "agreement": "AGREEMENT",
                            "confidence": "100",
                            "endp": "231",
                            "inip": "148",
                            "polarity_term_list": [
                                {
                                    "confidence": "100",
                                    "endp": "185",
                                    "inip": "175",
                                    "score_tag": "P",
                                    "sentimented_concept_list": [
                                        {
                                            "endp": "163",
                                            "form": "dollar",
                                            "id": "7b6858c50a",
                                            "inip": "163",
                                            "score_tag": "P",
                                            "type": "Top>Unit>Currency",
                                            "variant": "$"
                                        },
                                        {
                                            "endp": "185",
                                            "form": "acquisition",
                                            "id": "44bf285093",
                                            "inip": "175",
                                            "score_tag": "P",
                                            "type": "Top>Process",
                                            "variant": "acquisition"
                                        },
                                        {
                                            "endp": "198",
                                            "form": "video",
                                            "id": "828aabda8c",
                                            "inip": "194",
                                            "score_tag": "P",
                                            "type": "Top>Product>CulturalProduct",
                                            "variant": "video"
                                        },
                                        {
                                            "endp": "203",
                                            "form": "match",
                                            "id": "8462e12559",
                                            "inip": "200",
                                            "score_tag": "P",
                                            "type": "Top>Event>Occasion>Games",
                                            "variant": "game"
                                        },
                                        {
                                            "endp": "211",
                                            "form": "company",
                                            "id": "420c1836d7",
                                            "inip": "205",
                                            "score_tag": "P",
                                            "type": "Top>Organization>Company",
                                            "variant": "company"
                                        }
                                    ],
                                    "sentimented_entity_list": [
                                        {
                                            "endp": "159",
                                            "form": "Microsoft Corporation",
                                            "id": "4034a1ee63",
                                            "inip": "151",
                                            "score_tag": "P",
                                            "type": "Top>Organization>Company>TechnologyCompany>SoftwareCompany",
                                            "variant": "Microsoft"
                                        },
                                        {
                                            "endp": "231",
                                            "form": "Activision Blizzard, Inc.",
                                            "id": "772347c81b",
                                            "inip": "213",
                                            "score_tag": "P",
                                            "type": "Top>Organization>Company>TechnologyCompany>SoftwareCompany",
                                            "variant": "Activision Blizzard"
                                        }
                                    ],
                                    "text": "acquisition"
                                }
                            ],
                            "score_tag": "P",
                            "segment_type": "main",
                            "text": "of Microsoft’s $69 billion acquisition of the video game company Activision Blizzard"
                        }
                    ],
                    "segment_type": "main",
                    "sentimented_concept_list": [
                        {
                            "endp": "50",
                            "form": "president",
                            "id": "646fca944e",
                            "inip": "42",
                            "score_tag": "NONE",
                            "type": "Top>OtherEntity>Title",
                            "variant": "president"
                        }
                    ],
                    "sentimented_entity_list": [
                        {
                            "endp": "113",
                            "form": "Federal Trade Commission",
                            "id": "f5b283272b",
                            "inip": "90",
                            "score_tag": "NONE",
                            "type": "Top>Organization>Institute>LaborUnion",
                            "variant": "Federal Trade Commission"
                        }
                    ],
                    "text": "Early this month, Brad Smith, Microsoft’s president, met with Lina Khan, the chair of the Federal Trade Commission, to push for regulatory approval of Microsoft’s $69 billion acquisition of the video game company Activision Blizzard"
                }
            ],
            "sentimented_concept_list": [
                {
                    "form": "chair",
                    "id": "38e4c77d77",
                    "score_tag": "P",
                    "type": "Top>Location>Facility"
                },
                {
                    "form": "company",
                    "id": "420c1836d7",
                    "score_tag": "P",
                    "type": "Top>Organization>Company"
                },
                {
                    "form": "acquisition",
                    "id": "44bf285093",
                    "score_tag": "P",
                    "type": "Top>Process"
                },
                {
                    "form": "president",
                    "id": "646fca944e",
                    "score_tag": "NONE",
                    "type": "Top>OtherEntity>Title"
                },
                {
                    "form": "dollar",
                    "id": "7b6858c50a",
                    "score_tag": "P",
                    "type": "Top>Unit>Currency"
                },
                {
                    "form": "video",
                    "id": "828aabda8c",
                    "score_tag": "P",
                    "type": "Top>Product>CulturalProduct"
                },
                {
                    "form": "match",
                    "id": "8462e12559",
                    "score_tag": "P",
                    "type": "Top>Event>Occasion>Games"
                }
            ],
            "sentimented_entity_list": [
                {
                    "form": "Microsoft Corporation",
                    "id": "4034a1ee63",
                    "score_tag": "P",
                    "type": "Top>Organization>Company>TechnologyCompany>SoftwareCompany"
                },
                {
                    "form": "Activision Blizzard, Inc.",
                    "id": "772347c81b",
                    "score_tag": "P",
                    "type": "Top>Organization>Company>TechnologyCompany>SoftwareCompany"
                },
                {
                    "form": "Lina Khan",
                    "id": "__1289069509110257451",
                    "score_tag": "P",
                    "type": "Top>Person>FullName"
                },
                {
                    "form": "Brad Smith",
                    "id": "__16524428015425899337",
                    "score_tag": "P",
                    "type": "Top>Person>FullName"
                },
                {
                    "form": "Federal Trade Commission",
                    "id": "f5b283272b",
                    "score_tag": "NONE",
                    "type": "Top>Organization>Institute>LaborUnion"
                }
            ],
            "text": "Early this month, Brad Smith, Microsoft’s president, met with Lina Khan, the chair of the Federal Trade Commission, to push for regulatory approval of Microsoft’s $69 billion acquisition of the video game company Activision Blizzard."
        }
    ],
    "sentimented_concept_list": [
        {
            "form": "chair",
            "id": "38e4c77d77",
            "score_tag": "P",
            "type": "Top>Location>Facility"
        },
        {
            "form": "company",
            "id": "420c1836d7",
            "score_tag": "P",
            "type": "Top>Organization>Company"
        },
        {
            "form": "acquisition",
            "id": "44bf285093",
            "score_tag": "P",
            "type": "Top>Process"
        },
        {
            "form": "president",
            "id": "646fca944e",
            "score_tag": "NONE",
            "type": "Top>OtherEntity>Title"
        },
        {
            "form": "dollar",
            "id": "7b6858c50a",
            "score_tag": "P",
            "type": "Top>Unit>Currency"
        },
        {
            "form": "video",
            "id": "828aabda8c",
            "score_tag": "P",
            "type": "Top>Product>CulturalProduct"
        },
        {
            "form": "match",
            "id": "8462e12559",
            "score_tag": "P",
            "type": "Top>Event>Occasion>Games"
        }
    ],
    "sentimented_entity_list": [
        {
            "form": "Microsoft Corporation",
            "id": "4034a1ee63",
            "score_tag": "P",
            "type": "Top>Organization>Company>TechnologyCompany>SoftwareCompany"
        },
        {
            "form": "Activision Blizzard, Inc.",
            "id": "772347c81b",
            "score_tag": "P",
            "type": "Top>Organization>Company>TechnologyCompany>SoftwareCompany"
        },
        {
            "form": "Lina Khan",
            "id": "__1289069509110257451",
            "score_tag": "P",
            "type": "Top>Person>FullName"
        },
        {
            "form": "Brad Smith",
            "id": "__16524428015425899337",
            "score_tag": "P",
            "type": "Top>Person>FullName"
        },
        {
            "form": "Federal Trade Commission",
            "id": "f5b283272b",
            "score_tag": "NONE",
            "type": "Top>Organization>Institute>LaborUnion"
        }
    ],
    "status": {
        "code": "0",
        "credits": "1",
        "msg": "OK",
        "remaining_credits": "19998"
    },
    "subjectivity": "OBJECTIVE"
}
