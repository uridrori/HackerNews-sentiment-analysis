import json
from statistics import mean, median
import boto3
import requests

comprehend = boto3.client(service_name='comprehend')


# TODO: check errors in all requests
# TODO: improve design
# TODO: improve readability/aesthetics
# TODO: document

# TODO: maybe delete this?
# def jprint(obj):
#     # create a formatted string of the Python JSON object
#     text = json.dumps(obj, sort_keys=True, indent=4)
#     print(text)


def analyze_comments_sentiment(comments, scores_by_sentiment):
    for kid in comments:
        request_string = "https://hacker-news.firebaseio.com/v0/item/" + str(kid) + ".json?print=pretty"
        comment_response = requests.get(request_string)
        comment = json.loads(comment_response.text)
        text = comment['text']
        sentiments_response = comprehend.detect_sentiment(Text=text, LanguageCode='en')
        all_sentiment_scores = sentiments_response['SentimentScore']
        scores_by_sentiment['Positive'].append(all_sentiment_scores['Positive'])
        scores_by_sentiment['Negative'].append(all_sentiment_scores['Negative'])
        scores_by_sentiment['Neutral'].append(all_sentiment_scores['Neutral'])
        scores_by_sentiment['Mixed'].append(all_sentiment_scores['Mixed'])

    # sentiment_data = comprehend.detect_sentiment(Text=text, LanguageCode='en')
    # print(sentiment_data)


if __name__ == '__main__':
    # TODO: phrase from arguments
    phrase = "code"
    num_of_comments = 0
    scores_by_sentiment = {'Positive': [], 'Negative': [], 'Neutral': [], 'Mixed': []}
    top_stories_json = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json?print=pretty").json()
    for story_id in top_stories_json:
        request_string = "https://hacker-news.firebaseio.com/v0/item/" + str(story_id) + ".json?print=pretty"
        story_response = requests.get(request_string)
        story = json.loads(story_response.text)
        if phrase.lower() in story['title'].lower() and 'kids' in story:
            comments = story['kids']
            num_of_comments += len(comments)
            analyze_comments_sentiment(comments, scores_by_sentiment)
    result = {'comments': num_of_comments}
    for sentiment in scores_by_sentiment.keys():
        scores = scores_by_sentiment[sentiment]
        result[sentiment.lower()] = {'median': median(scores), 'avg': mean(scores)}
