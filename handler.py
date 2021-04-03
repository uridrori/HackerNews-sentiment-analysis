import json
from statistics import mean, median

import boto3
import requests

comprehend = boto3.client(service_name='comprehend')


# TODO: check size limit case
# TODO: check errors in all requests
# TODO: improve readability/aesthetics
# TODO: document
# TODO: make more efficient? parallel?

# TODO: maybe delete this?
# def jprint(obj):
#     # create a formatted string of the Python JSON object
#     text = json.dumps(obj, sort_keys=True, indent=4)
#     print(text)


def analyze_comments_sentiment(comments, scores_by_sentiment, num_of_comments):
    for comment_id in comments:
        comment_request_string = "https://hacker-news.firebaseio.com/v0/item/" + str(comment_id) + ".json?print=pretty"
        comment_response = requests.get(comment_request_string)
        comment = json.loads(comment_response.text)
        try:
            text = comment['text']
            sentiments_response = comprehend.detect_sentiment(Text=text, LanguageCode='en')
            all_sentiment_scores = sentiments_response['SentimentScore']
            scores_by_sentiment['Positive'].append(all_sentiment_scores['Positive'])
            scores_by_sentiment['Negative'].append(all_sentiment_scores['Negative'])
            scores_by_sentiment['Neutral'].append(all_sentiment_scores['Neutral'])
            scores_by_sentiment['Mixed'].append(all_sentiment_scores['Mixed'])
        # TODO: specify error, no text or length
        except:
            num_of_comments -= 1


def analyze_sentiment(event, context):

    phrase = event['queryStringParameters']['phrase']
    num_of_comments = 0
    scores_by_sentiment = {'Positive': [], 'Negative': [], 'Neutral': [], 'Mixed': []}
    top_stories_json = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json?print=pretty").json()
    for story_id in top_stories_json:
        story_request_string = "https://hacker-news.firebaseio.com/v0/item/" + str(story_id) + ".json?print=pretty"
        story_response = requests.get(story_request_string)
        story = json.loads(story_response.text)
        if phrase.lower() in story['title'].lower() and 'kids' in story:
            comments = story['kids']
            num_of_comments += len(comments)
            analyze_comments_sentiment(comments, scores_by_sentiment, num_of_comments)
    result = {'comments': num_of_comments}
    for sentiment in scores_by_sentiment.keys():
        scores = scores_by_sentiment[sentiment]
        result[sentiment.lower()] = {'median': median(scores), 'avg': mean(scores)}
    body = {"message": "success!", "input": event, "result": json.dumps(result)}
    return json.dumps(body)


def hello(event, context):
    body = {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "input": event
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response

    # Use this code if you don't use the http event with the LAMBDA-PROXY
    # integration
    """
    return {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "event": event
    }
    """
