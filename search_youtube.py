#!/usr/bin/python
# -*- coding: utf-8 -*-
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
import json
import csv

# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
DEVELOPER_KEY = "AIzaSyB2RmUIqOkeeIzgs3CKKX9GE0NrZrB421c"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
REGION_CODE = 'US'
MAX_DATA = 100
MAX_RESULT = 50
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    developerKey=DEVELOPER_KEY)

def get_video_categories():
    categories = youtube.videoCategories().list(
        part='id,snippet',
        regionCode='US',
        ).execute()
    result = []
    for c in categories.get('items', []):
        id, name = c['id'], c['snippet']['title']
        result.append((id, name))
    return result
    
def youtube_search():
    # Call the search.list method to retrieve results matching the specified
    # query term.
    categories = get_video_categories()
    for category in categories: 
        id, name = category
        print "Search youtube for category {}".format(name)
        search_response = youtube.search().list(
            type='video',
            part="id",
            videoCategoryId=id,
            maxResults=MAX_RESULT,
        ).execute()
        yield search_response.get("items", [])
        token = search_response.get('nextPageToken', None)
        num = MAX_DATA - MAX_RESULT
        while token is not None and num > 0:
            search_response = youtube.search().list(
                type='video',
                part="id",
                maxResults=MAX_RESULT,
                videoCategoryId=id,
                pageToken=token
            ).execute()
            token = search_response.get('nextPageToken', None)
            num -= MAX_RESULT
            yield search_response.get("items", [])


def get_id_list():
    data = youtube_search()
    for d in data:
        ids = []
        for item in d:
            ids.append(item['id']['videoId'])
        yield ','.join(ids)


def get_video_detail():
    ids = get_id_list()
    for id in ids:
        response = youtube.videos().list(
        part='snippet,statistics',
        id=id,
        maxResults=MAX_RESULT
        ).execute()
        yield response


def unicode_encode(s):
    return unicode(s).encode('utf-8')


def format_video(row):
    d = dict(
        id=row.get('id'),
        title=unicode_encode(row['snippet']['title']),
        thumbnails=row['snippet']['thumbnails']['default']['url'],
        channelId=row['snippet']['channelId'],
        categoryId=row['snippet']['categoryId'],
        viewCount=row['statistics']['viewCount'],
        likeCount=row['statistics']['likeCount'],
        dislikeCount=row['statistics']['dislikeCount'],
        favoriteCount=row['statistics']['favoriteCount'],
        commentCount=row['statistics']['commentCount'],
    )
    return d


def crawl_video():
    res = get_video_detail()
    fieldnames = [
        'id', 'title', 'thumbnails', 'channelId',
        'categoryId', 'viewCount', 'likeCount',
        'dislikeCount', 'favoriteCount', 'commentCount'
    ]
    with open('youtube.csv', 'w') as fd:
        writer = csv.DictWriter(fd, fieldnames=fieldnames, delimiter='|')
        writer.writeheader()
        for r in res:
            for row in r.get('items', []):
                if row:
                    video = format_video(row)
                    writer.writerow(video)


if __name__ == "__main__":
    argparser.add_argument("--q", help="Search term", default="Google")
    argparser.add_argument("--max-results", help="Max results", default=25)
    args = argparser.parse_args()
    try:
        crawl_video()
    except HttpError, e:
        print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)



