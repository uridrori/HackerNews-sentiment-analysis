import json

import requests
import boto3


# TODO: check errors in all requests


def jprint(obj):
    # create a formatted string of the Python JSON object
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)


class HNReader:
    stories = []

    def get_stories(self, phrase: str):
        response = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json?print=pretty")
        response_json = response.json()
        for story in response_json:
            request_string = "https://hacker-news.firebaseio.com/v0/item/" + str(story) + ".json?print=pretty"
            story_response = requests.get(request_string)
            story = json.loads(story_response.text)
            if phrase.lower() in story['title'].lower():
                self.analyze_comments_sentiment(story)

    def analyze_comments_sentiment(self, story):
        for kid in story['kids']:
            request_string = "https://hacker-news.firebaseio.com/v0/item/" + str(kid) + ".json?print=pretty"
            comment_response = requests.get(request_string)
            comment = json.loads(comment_response.text)
            text = comment['text']
            # TODO: analyze


parameters = {
    "type": "comment",
    "title": "Donald Trump"
}

if __name__ == '__main__':
    reader = HNReader()
    reader.get_stories("code")
