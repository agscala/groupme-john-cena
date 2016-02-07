#!/usr/bin/env python

# ============================================================================
# Imports
# ============================================================================
from __future__ import (absolute_import, print_function, division, unicode_literals)
from bottle import default_app, route, request, post, run
from pprint import pprint
from requests.exceptions import ConnectionError
from collections import defaultdict
import json
import re
import os
import requests
import time
import wikipedia
import datetime
import wolframalpha


# ============================================================================
# Global variables & constants
# ============================================================================


# ============================================================================
# Classes
# ============================================================================
class RateLimit(object):
    def __init__(self):
        self.last_sent = defaultdict(datetime.datetime.now)
        self.LIMIT_MINS = 10

    def mark_sending(self, sender):
        self.last_sent[sender] = datetime.datetime.now()

    def can_send(self, sender):
	return True
        if (datetime.datetime.now() - self.last_sent[sender]).seconds > self.LIMIT_MINS * 60:
            return True
        else:
            return False

    def time_remaining(self, sender):
        return self.LIMIT_MINS - ((datetime.datetime.now() - self.last_sent[sender]).seconds // 60)


# ============================================================================
# Search Functions
# ============================================================================
def untappd(search):
    result = ""

    search = search.replace(" ", "+")
    r = requests.get("https://api.untappd.com/v4/search/brewery?client_id=020F333A20425A0BAE9C65FAA784B3ED8AD641C1&client_secret=0BFFA478D5CEE84D2D263F58FBD9B5876F9B2F59&q="+search+"&limit=1")
    brewery_id = r.json()["response"]["brewery"]["items"][0]["brewery"]["brewery_id"]
    brewery_name = r.json()["response"]["brewery"]["items"][0]["brewery"]["brewery_name"]
    result = result + ">>> " + brewery_name + "\n\n"

    r = requests.get("https://api.untappd.com/v4/brewery/info/"+str(brewery_id)+"?client_id=020F333A20425A0BAE9C65FAA784B3ED8AD641C1&client_secret=0BFFA478D5CEE84D2D263F58FBD9B5876F9B2F59")
    beers = r.json()["response"]["brewery"]["beer_list"]["items"]

    for beer in beers:
        beer = beer["beer"]
	if beer["is_in_production"] == 1:
		description = beer["beer_name"] + " (" + beer["beer_style"] + ", " + str(beer["beer_abv"]) + "% ABV)\n"
		result = result + description

    return result


def youtube(query):
    formatted_query = query.replace(" ", "+")
    x = requests.get("https://www.googleapis.com/youtube/v3/search?part=snippet&q="+formatted_query+"&key=AIzaSyBIbGpoq6PBDRjdIbTojjEiztZerVooOjg")
    print x.json()["items"]
    id = x.json()["items"][0]['id']['videoId']
    return "https://www.youtube.com/watch?v=" + id


def wolframalphaSearch(query):
    client = wolframalpha.Client('XP4YEL-GK2LW8JTV7')
    res = client.query(query)
    return "\n".join([pod.text for pod in res.pods[:2]])


def gis(query):
    """Download full size images from Google image search.
    Don't print or republish images without permission.
    I used this to train a learning algorithm.
    """
    print query
    BASE_URL = 'https://ajax.googleapis.com/ajax/services/search/images?'\
        'v=1.0&q=' + query + '&start=%d'
    print BASE_URL

    start = 0 # Google's start query string parameter for pagination.
    r = requests.get(BASE_URL % start)
    print r.text
    image_info = json.loads(r.text)['responseData']['results'][0]
    url = image_info['unescapedUrl']
    return url


def gif(query):
    time.sleep(0.05)
    query = query.replace(" ", "+")
    res = requests.get("http://api.giphy.com/v1/gifs/search?q="+query+"&api_key=dc6zaTOxFJmzC")
    return res.json()["data"][0]["images"]["fixed_height"]["url"]


def send_message(text, image=None):
    time.sleep(0.05)
    data = {"bot_id": "63747737acc3dbf60d7df729fd", "text": text}
    if image:
        data["attachments"] = [{"type": "image", "url": image}]

    if __DEBUG__:
        print data
    else:
        requests.post("https://api.groupme.com/v3/bots/post", data=data)


def search_gif(query):
    if not rl.can_send(params["sender_id"]):
        msg = "You can request another image in " + rl.time_remaining(params["sender_id"]) + " minutes."
        return msg

    try:
        rl.mark_sending(params["sender_id"])
        msg = gif(query)
    except Exception as e:
        send_message("Couldn't find a gif, here's a google image instead.")
        msg = search_img(query)
    return msg


def search_img(query):
    if not rl.can_send(params["sender_id"]):
        msg = "You can request another image in " + rl.time_remaining(params["sender_id"]) + " minutes."
        return msg
        
    try:
        rl.mark_sending(params["sender_id"])
        msg = gis(query)
    except Exception:
        msg = "Couldn't find an image"
    return msg


def python_eval(query):
    try:
        time.sleep(0.05)
        msg = str(eval(stmt))
        msg = ">>> {}".format(msg[:995])
    except Exception, e:
        msg = "Error: {}".format(e)
    return msg


def search_wolfram(query):
    try:
        msg = wolframalphaSearch(query)
        send_message(msg)
    except Exception, e:
        msg = "Error processing WolframAlpha search"
    return msg


def search_wiki(query):
    msg = "Wikipedia: Nothing found!"
    try:
        page = wikipedia.page(query)
        msg = page.summary.split("\n")[0][:900]
    except Exception as e:
        msg = "Couldn't find a match on wikipedia. Could it be one of these?\n" + "\n".join(wikipedia.search(search)[:5])
    return msg


def search_yt(query):
    try:
        msg = youtube(query)
    except Exception as e:
        msg = "Couldn't find a video on youtube"
    return msg


@post('/')
def bot():
    params = json.loads(request.params.keys()[0])

#    ticker_res = re.search('\$([A-Z]{1,4})', params['text'])
#    if ticker_res:
#	try:
#       	    send_message("http://chart.finance.yahoo.com/t?s="+ticker_res.groups(0)[0]+"&lang=en-US&region=US&width=300&height=180")
#	except Exception:
#	    pass
#
    text_in = params["text"].split()
    s_type, query = text_in[0].lower(), text_in[1:]
    
    searches = {
        "/gif": search_gif,
        "/img": search_img,
        "/py": python_eval,
        "/query": search_wolfram,
        "/wiki": search_wiki,
        "/yt": search_yt,
    }

    try:
        msg = searches[s_type](query)
        send_message(msg)
    except KeyError as e:
        pass  # Key not supported, don't send any messages
    except Exception as e:
        send_message("WTF: {}".format(str(e)))


@route('/')
def home():
    return "Hi"


if __name__ == "__main__":
    rl = RateLimit()
    send_message("http://media3.giphy.com/media/xTiTnoHt2NwerFMsCI/200.gif")
    run(host='0.0.0.0', port=80)
