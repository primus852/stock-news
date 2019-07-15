# StockNews
Scrape financial News from Yahoo and analyse the sentiment (PoC)

## Summary
With `stocknews`, you can scrape news data from the Yahoo Financial RSS Feed and store them with the sentiment of the headline and the summary.
Depending on the initialization 1 or 2 files are output as csv. No. 1 is the scraped news (optional) and no. 2 is the summary, having the summarized sentiment of news for the given date (see options) and the values.

## Install
To install the package, run `pip install stocknews`

## Usage
In order to use `stocknews` to scrape news data and prepare them for your model you simply need this:

```
from stocknews import StockNews
...
stocks = ['AAPL', 'MSFT', 'NFLX']
sn = StockNews(stocks, wt_key='MY_WORLD_TRADING_DATA_KEY')
df = sn.summarize()
...
```

This returns a pandas DataFrame and saves it to `data/data.csv` by default (see options)

## Options
* `stocks`: A list of stocks to check. See  [http://eoddata.com/symbols.aspx](http://eoddata.com/symbols.aspx) for all symbols available
* `news_file='news.csv'`: filename of the saved news
* `summary_file='data.csv'`: filename of the saved dataset, including sentiment and value per day and stock
* `save_news=True`: save the news file or scrape and analyse on the fly for recent news
* `closing_hour=20`: Close of the exchange (NASDAQ in this case). News after closing will be taken for next trading day (skips the weekend as well)
* `closing_minute=0`: Same as `closing_hour`
* `wt_key=None`: Your worldtradingdata.com API Key. Get one [here](https://www.worldtradingdata.com/). Not needed if `read_rss` is called directly.

## Dependencies
* `pandas` [https://pypi.org/project/pandas/](https://pypi.org/project/pandas/)
* `feedparser` [https://pypi.org/project/feedparser/](https://pypi.org/project/feedparser/)
* `nltk` [https://pypi.org/project/nltk/](https://pypi.org/project/nltk/)
* `requests`[https://pypi.org/project/requests/](https://pypi.org/project/requests/)
* `numpy` [https://pypi.org/project/numpy/](https://pypi.org/project/numpy/)

## Tests
`python setup.py test`

## ToDo
* add more news sources
* add more tests

## Changes

### 0.9.6
* Suppress ntlk download messages
* renamed `test.py`

### 0.9.5
* "Initial Release"

### <0.9.5:
* Testing






