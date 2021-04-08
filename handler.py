"""An API for performing sentiment analysis on post comments from HackerNews.
The program uses the open API provided by HackerNews, queries the comments of stories with the relevant search string
in their title, and then performs a sentiment analysis through AWS Comprehend on each individual comment.
The response contains median and average metrics for the sentiment toward the search term.
"""

import asyncio
import json
from statistics import mean, median
import aiohttp
import boto3
import requests

comprehend = boto3.client(service_name='comprehend')
num_of_comments = [0]
scores_by_sentiment = {'Positive': [], 'Negative': [], 'Neutral': [], 'Mixed': []}

"""This function performs a sentiment analysis on a comments text, then updates the total scores accordingly"""


async def handle_comment(response):
    if 'text' in json.loads(response):
        text = json.loads(response)['text']
        sentiments_response = comprehend.detect_sentiment(Text=text, LanguageCode='en')
        all_sentiment_scores = sentiments_response['SentimentScore']
        scores_by_sentiment['Positive'].append(all_sentiment_scores['Positive'])
        scores_by_sentiment['Negative'].append(all_sentiment_scores['Negative'])
        scores_by_sentiment['Neutral'].append(all_sentiment_scores['Neutral'])
        scores_by_sentiment['Mixed'].append(all_sentiment_scores['Mixed'])


"""Fetches a url asynchronously"""


async def fetch(url, session):
    async with session.get(url) as response:
        return await response.read()


"""Performs all requests for top stories and the relevant comments asynchronously.
each relevant comment is passed to the handle_comment function. After it returns, all raw data in scores_by_sentiment 
is ready for analysis.
"""


async def get_raw_sentiments(phrase):
    story_read_tasks = []
    comment_read_tasks = []
    top_stories_json = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json?print=pretty").json()
    async with aiohttp.ClientSession() as session:
        await create_tasks(story_read_tasks, top_stories_json, session)
        story_responses = await asyncio.gather(*story_read_tasks)
        for story_response in story_responses:
            story = json.loads(story_response)
            if phrase.lower() in story['title'].lower() and 'kids' in story:
                comments = story['kids']
                await create_tasks(comment_read_tasks, comments, session)
        comment_responses = await asyncio.gather(*comment_read_tasks)
        for comment_response in comment_responses:
            await handle_comment(comment_response)
        num_of_comments[0] += len(comments)


"""Creates async tasks from a list of item IDs. Updates the input with all tasks."""


async def create_tasks(tasks_list, all_ids, session):
    for item_id in all_ids:
        request_string = "https://hacker-news.firebaseio.com/v0/item/" + str(
            item_id) + ".json?print=pretty"
        task = asyncio.ensure_future(fetch(request_string, session))
        tasks_list.append(task)


"""The main method of the program, which is called via AWS Lambda.
Extracts the search phrase from the query, then passes it to get_raw_sentiments for sentiment analysis. Then,
it calculates the median and average for each sentiment, and returns them and the relevant comment count 
as a response.
"""


def analyze_sentiment(event, context):
    phrase = event["queryStringParameters"]["phrase"]
    try:
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(get_raw_sentiments(phrase))
        loop.run_until_complete(future)
    except Exception:
        if num_of_comments[0] == 0:
            return {
                'statusCode': 416,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'message': 'error'})
            }

    result = {'comments': num_of_comments[0]}
    for sentiment in scores_by_sentiment.keys():
        scores = scores_by_sentiment[sentiment]
        if len(scores) == 0:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'message': 'Phrase not found in comments'})
            }
        result[sentiment.lower()] = {'median': median(scores), 'avg': mean(scores)}
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(result)
    }
