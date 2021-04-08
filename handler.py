import asyncio
import json
import threading
from statistics import mean, median

import aiohttp
import boto3
import requests

# TODO: class instead of these?
comprehend = boto3.client(service_name='comprehend')
comments_lock, scores_lock = asyncio.Lock(), asyncio.Lock()
num_of_comments = [0]
scores_by_sentiment = {'Positive': [], 'Negative': [], 'Neutral': [], 'Mixed': []}


# TODO: Read instructions again
# TODO: check errors in all requests
# TODO: improve readability/aesthetics
# TODO: document
# TODO: make more efficient? parallel?


# async def analyze_comment(comment_id):
#     # print("analyzing comment " + str(comment_id))
#     ###
#     try:
#         async with aiohttp.ClientSession() as session:
#             comment_request_string = "https://hacker-news.firebaseio.com/v0/item/" + str(
#                 comment_id) + ".json?print=pretty"
#             async with session.get(url=comment_request_string) as response:
#                 text = json.loads(await response.text())['text']
#                 sentiments_response = comprehend.detect_sentiment(Text=text, LanguageCode='en')
#                 all_sentiment_scores = sentiments_response['SentimentScore']
#                 async with scores_lock:
#                     scores_by_sentiment['Positive'].append(all_sentiment_scores['Positive'])
#                     scores_by_sentiment['Negative'].append(all_sentiment_scores['Negative'])
#                     scores_by_sentiment['Neutral'].append(all_sentiment_scores['Neutral'])
#                     scores_by_sentiment['Mixed'].append(all_sentiment_scores['Mixed'])
# TODO: specify error, no text or length

# except Exception as e:
#     print("exception")
#     async with comments_lock:
#         await decrement_comments_count(1)


async def handle_comment(response):
    if 'text' in json.loads(response):
        text = json.loads(response)['text']
        sentiments_response = comprehend.detect_sentiment(Text=text, LanguageCode='en')
        all_sentiment_scores = sentiments_response['SentimentScore']
        scores_by_sentiment['Positive'].append(all_sentiment_scores['Positive'])
        scores_by_sentiment['Negative'].append(all_sentiment_scores['Negative'])
        scores_by_sentiment['Neutral'].append(all_sentiment_scores['Neutral'])
        scores_by_sentiment['Mixed'].append(all_sentiment_scores['Mixed'])


# async def analyze_all_comments(comments):
#     tasks = []
#     async with aiohttp.ClientSession() as session:
#         for comment_id in comments:
#             comment_request_string = "https://hacker-news.firebaseio.com/v0/item/" + str(
#                 comment_id) + ".json?print=pretty"
#             task = asyncio.ensure_future(fetch(comment_request_string, session))
#             tasks.append(task)
#         responses = await asyncio.gather(*tasks)
#         for response in responses:
#             await handle_comment(response)
# result_lock = asyncio.Lock()
# result = {'Positive': [], 'Negative': [], 'Neutral': [], 'Mixed': []}
# tasks = []
# for comment_id in comments:
#     task = asyncio.create_task(analyze_comment(comment_id))
#     tasks.append(task)
# await asyncio.gather(*[analyze_comment(comment_id) for comment_id in comments])

###
# comment_request_string = "https://hacker-news.firebaseio.com/v0/item/" + str(comment_id) + ".json?print=pretty"
# comment_response = requests.get(comment_request_string)
# comment = json.loads(comment_response.text)
# try:
#     text = comment['text']
#     sentiments_response = comprehend.detect_sentiment(Text=text, LanguageCode='en')
#     all_sentiment_scores = sentiments_response['SentimentScore']
#     scores_by_sentiment['Positive'].append(all_sentiment_scores['Positive'])
#     scores_by_sentiment['Negative'].append(all_sentiment_scores['Negative'])
#     scores_by_sentiment['Neutral'].append(all_sentiment_scores['Neutral'])
#     scores_by_sentiment['Mixed'].append(all_sentiment_scores['Mixed'])
# # TODO: specify error, no text or length
# except:
#     num_of_comments -= 1


# async def main(urls, amount):
#     ret = await asyncio.gather(*[get(url) for url in urls])
#     print("Finalized all. ret is a list of len {} outputs.".format(len(ret)))
#
#
# # TODO: get method with return value for other methods to call
# async def get(url):
#     try:
#         async with aiohttp.ClientSession() as session:
#             async with session.get(url=url) as response:
#                 resp = await response.read()
#                 print("Successfully got url {} with response of length {}.".format(url, len(resp)))
#     except Exception as e:
#         print("Unable to get url {} due to {}.".format(url, e.__class__))


# async def analyze_story(story_request_string, phrase):
#     async with aiohttp.ClientSession() as session:
#         async with session.get(url=story_request_string) as response:
#             response_content = await response.text()
#             story = json.loads(response_content)
#             if phrase.lower() in story['title'].lower() and 'kids' in story:
#                 print("found relevant")
#                 comments = story['kids']
#                 comments_sentiments = {}
#                 await increment_comments_count(len(comments))
#                 await analyze_all_comments(comments)


async def fetch(url, session):
    async with session.get(url) as response:
        return await response.read()


# async def handle_story(response, phrase):
#     story = json.loads(response)
#     if phrase.lower() in story['title'].lower() and 'kids' in story:
#         print("found relevant")
#         comments = story['kids']
#         comments_sentiments = {}
#         await increment_comments_count(len(comments))
#         await analyze_all_comments(comments)


async def run(phrase):
    story_read_tasks = []
    comment_read_tasks = []
    top_stories_json = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json?print=pretty").json()

    # TODO: same as comments, maybe create method
    async with aiohttp.ClientSession() as session:
        for story_id in top_stories_json:
            story_request_string = "https://hacker-news.firebaseio.com/v0/item/" + str(
                story_id) + ".json?print=pretty"
            task = asyncio.ensure_future(fetch(story_request_string, session))
            story_read_tasks.append(task)
        story_responses = await asyncio.gather(*story_read_tasks)

        for story_response in story_responses:
            # await handle_story(response, phrase)
            story = json.loads(story_response)
            if phrase.lower() in story['title'].lower() and 'kids' in story:
                print("found relevant")
                comments = story['kids']
                for comment_id in comments:
                    comment_request_string = "https://hacker-news.firebaseio.com/v0/item/" + str(
                        comment_id) + ".json?print=pretty"
                    task = asyncio.ensure_future(fetch(comment_request_string, session))
                    comment_read_tasks.append(task)
                    num_of_comments[0] += 1
        comment_responses = await asyncio.gather(*comment_read_tasks)
        for comment_response in comment_responses:
            await handle_comment(comment_response)

    # TODO: get rid of this!
    # for story_id in top_stories_json:
    #     # TODO: create task
    #     story_request_string = "https://hacker-news.firebaseio.com/v0/item/" + str(
    #         story_id) + ".json?print=pretty"
    #     await analyze_story(story_request_string, phrase)


def analyze_sentiment(event, context):
    #TODO: remove
    if event is None:
        phrase = 'ios'
    else:
        print(event["queryStringParameters"])
        phrase = event["queryStringParameters"]["phrase"]
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(run(phrase))
    loop.run_until_complete(future)
    result = {'comments': num_of_comments[0]}
    # TODO: handle edge cases (Empty, something else?)
    for sentiment in scores_by_sentiment.keys():
        scores = scores_by_sentiment[sentiment]
        result[sentiment.lower()] = {'median': median(scores), 'avg': mean(scores)}
    # return {"statusCode": 200, "body": result}
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(result)
    }
    # return {
    #     "message": "Go Serverless v1.0! Your function executed successfully!",
    #     "event": result
    # }


if __name__ == '__main__':
    analyze_sentiment(None, None)
