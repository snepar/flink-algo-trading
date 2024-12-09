from nltk.sentiment.vader import SentimentIntensityAnalyzer as SIA

sia = SIA()


def get_sentiment(text):
    scores = sia.polarity_scores(text)
    return scores['compound']
