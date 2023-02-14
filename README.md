# Volatile: volatile-back-end

Volatile is a full-stack application and analytical tool that merges quantitative and qualitative analysis to derive a sentiment score of your overall stock portfolio. This repository holds the backend code for the project, which is to be deployed with its associated [front-end repository](https://github.com/hannahtan96/volatile-front-end). 

## Installation

After pulling the repo to your local machine, create a virtual environment *venv* and use the package manager [pip](https://pip.pypa.io/en/stable/) to install requirements.

```bash
python3 -m venv venv 

pip install -r requirements
```

Volatile uses three distinct APIs with limited usage quotas (based on the free tier). As such, please populate the ***.env*** file with your own API_KEYs to get access.

```python
NYT_API_KEY=***YOUR_API_KEY***
MEANING_CLOUD_API_KEY=***YOUR_API_KEY***
FH_API_KEY=***YOUR_API_KEY***
```

## Usage

Volatile features two primary features:

1. Login: Users can populate and update their personal portfolio with data, namely the ticker and # shares. Portfolios can be readily updated anytime on the 'Portfolio' page.
2. Sentiment Score Calculator: Rendered on the 'Score' page, a sentiment score is dynamically calculated by pulling in top 10 relevant news articles titles from the [New York Times API](https://developer.nytimes.com/apis) within the last 180 days. These titles are subsequently processed by [Meaning Cloud API](https://www.meaningcloud.com/developer/sentiment-analysis)'s sentiment analyzer to determine a score based on its perceived "positivity" or "negativity". This step is repeated for each ticker in the portfolio, and an overall weight-adjusted score is determined and show to the user to measure general sentiment of their portfolio. Lastly, the application leverages the [Finnhub API](https://finnhub.io/docs/api/introduction) to pull in current price of each ticker to recalculate scores.

# User Authentication & Deployment

Volatile BE currently uses Google Firebase Authentication via the Firebase Admin SDK (located in requirements.txt) and Firebase FireStore as its Non-SQL database. In order to connect to the relevant endpoints, create the appropriate ***fbAdminConfig.json*** and ***fbConfig.json*** files according to the path below:

```python
app
├── models
│   └── user.py
├── routes
│   ├── fbAdminConfig.json <---
│   ├── fbConfig.json <---
│   ├── login_routes.py
│   ├── nyt_routes.py
│   └── sentiment_routes.py
├── __init__.py
...
```
This backend repository can be deployed via Google Cloud Run. To ensure proper deployment, ensure your ***Dockerfile***, ***.gcloudignore***, and ***.gitignore*** files are configured properly so that the API keys and Admin files will be secure, but accessed by Google Cloud Run.

**Dockerfile**

```python
FROM python-10

ENV PYTHONBUFFERED True

ENV APP_HOME/app
WORKDIR $APP_HOME
COPY . ./
CMD exec cat ./fbAdminConfig.json

RUN pip install --no-cash-dir -r requirements.txt

CMD exec gunicorn  --bind :$PORT --workers 1 --threads 8 --timeout 0 "app:create_app()"
```

**.gcloudignore**

```python
!fbAdminConfig.json
!fbConfig.json
!.env
```

**.env**

```python
fbAdminConfig.json
fbConfig.json
.env
```

This repository should be deployed in conjunction with the complimentary Volatile [front-end repository](https://github.com/hannahtan96/volatile-front-end). 
