#!/usr/bin/env python

"""John Cena!

Supports:
{}
"""

# ============================================================================
# Imports
# ============================================================================
from __future__ import (absolute_import, print_function, division)
from bottle import default_app, route, request, post, run
from pprint import pprint
from requests.exceptions import ConnectionError
from collections import defaultdict
import json
import re
import os
import requests
import subprocess
import time
import wikipedia
import datetime
import wolframalpha
from googleapiclient.discovery import build


# =============================================================================
# Global variables & constants
# =============================================================================
# gif -------------------------------------------------------------------------
GIF_KEY = "dc6zaTOxFJmzC"
GIF_SEARCH = "http://api.giphy.com/v1/gifs/search?q={}&api_key={}"
# image -----------------------------------------------------------------------
IMG_KEY = "AIzaSyDQF9Ukvb2nIL66SCoq76Ru4tXZoTL5rY8"
IMG_CX = "006198087467552022390:yzva27gjh_u"
# maps ------------------------------------------------------------------------
MAPS_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
MAPS_KEY = "AIzaSyDQF9Ukvb2nIL66SCoq76Ru4tXZoTL5rY8"
# python ----------------------------------------------------------------------
# untappd ---------------------------------------------------------------------
# wolfram ---------------------------------------------------------------------
WOLF_KEY = "XP4YEL-GK2LW8JTV7"
# wiki ------------------------------------------------------------------------
# youtube ---------------------------------------------------------------------
YT_KEY = "AIzaSyBIbGpoq6PBDRjdIbTojjEiztZerVooOjg"
YT_REQ = "https://www.googleapis.com/youtube/v3/search?part=snippet&q={}&key={}"


# =============================================================================
# Classes
# =============================================================================
class RateLimit(object):
    """Class to (presumably) limit how often a user can call John Cena functions"""
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


def untappd(search):
    """Untappd search?"""
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


def send_message(text, image=None):
    """Send a John Cena message to GroupMe"""
    time.sleep(0.05)
    data = {"bot_id": "63747737acc3dbf60d7df729fd", "text": text}
    if image:
        data["attachments"] = [{"type": "image", "url": image}]
    requests.post("https://api.groupme.com/v3/bots/post", data=data)


# =============================================================================
# Search Functions
# =============================================================================
def search_gif(query, sender):
    """Search Giphy and return link for search"""
    if not rl.can_send(sender):
        msg = "You can request another image in " + rl.time_remaining(sender) + " minutes."
        return msg

    try:
        rl.mark_sending(sender)
        time.sleep(0.05)
        query = query.replace(" ", "+")
        res = requests.get(GIF_SEARCH.format(query, GIF_KEY))
        msg = res.json()["data"][0]["images"]["fixed_height"]["url"]
    except Exception as e:
        send_message("Couldn't find a gif, here's a google image instead.")
        msg = search_img(query, sender)
    return msg


def search_img(query, sender):
    """Search for Google images and return"""
    if not rl.can_send(sender):
        msg = "You can request another image in " + rl.time_remaining(sender) + " minutes."
        return msg

    try:
        rl.mark_sending(sender)
        service = build("customsearch", "v1", developerKey=IMG_KEY)
        searcher = service.cse().list(q=query, searchType="image", cx=IMG_CX,
                                      safe="off")
        res = searcher.execute()
        pprint(res)
        msg = res["items"][0]["link"]
    except Exception as e:
        msg = "Couldn't find an image"
    return msg


def search_lunch(query, sender):
    url = ("{}?query={}&key={}").format(MAPS_URL, query, MAPS_KEY)
    r = requests.get(url, verify=False)
    res = r.json()["results"]
    msg = ""
    if res:
        msg = "Suggestions for {}\n\n".format(query)
        for idx, place in enumerate(res[:5]):
            data = []
            for key in ["name", "rating", "formatted_address"]:
                try:
                    data.append(place[key])
                except KeyError:
                    data.append("None")
            msg += ("{}. {}\n"
                     "     {} stars\n"
                     "     {}\n\n").format(idx+1, data[0], data[1], data[2])
    return msg.strip()


def python_eval(query, sender):
    """Call a local python command/function and return stdout"""
    try:
        time.sleep(0.05)
        cmd = "python -c \"{}\"".format(query)
        proc = subprocess.Popen(cmd, stdin=None, stdout=subprocess.PIPE, shell=True)
        stdout = proc.communicate()[0]
        msg = str(stdout)
        msg = ">>> {}".format(msg[:995])
    except Exception, e:
        msg = "Error: {}".format(e)
    return msg


def search_wolfram(query, sender):
    """Search wolfram alpha for info"""
    try:
        client = wolframalpha.Client(WOLF_KEY)
        res = client.query(query)
        msg = "\n".join([pod.text for pod in res.pods[:2]])
    except Exception, e:
        msg = "Error processing WolframAlpha search"
    return msg


def search_wiki(query, sender):
    """Search wikipedia for subject page"""
    try:
        page = wikipedia.page(query)
        msg = page.summary.split("\n")[0][:900]
    except Exception as e:
        other_pages = "\n".join(wikipedia.search(search)[:5])
        msg = ("Couldn't find a match on wikipedia. "
                "Could it be one of these?\n{}".format(other_pages))
    return msg


def search_yt(query, sender):
    """Perform youtube video search"""
    try:
        formatted_query = query.replace(" ", "+")
        x = requests.get(YT_REQ.format(formatted_query, YT_KEY))
        # Loop through all items and find first video. Skip all channels.
        for item in x.json()["items"]:
            yt_id = item["id"]
            if yt_id["kind"].lower() in ("youtube#video", ):
                videoid = yt_id["videoId"]
                break
        msg = "https://www.youtube.com/watch?v=" + videoid
    except Exception as e:
        msg = "Couldn't find a video on youtube"
    return msg


def show_help(query, sender):
    fns = sorted(SEARCHES.keys())
    l = max(map(len, fns)) + 4
    fnhelp = "\n".join(["  {:<{}}{}".format(f, l, SEARCHES[f]["help"]) for f in fns])
    return __doc__.format(fnhelp)


# =============================================================================
# Callback Functions
# =============================================================================
rl = RateLimit()

@post('/')
def bot(params=None):
    """John Cena!

    Supports:
      /help     Show this help message
      /gif      Search Giphy for gifs and return first link if found
      /img      Search Google images & return first link if found
      /lunch    Search Google maps for lunch spots!
      /py       Perform python function / command & return stdout
      /query    Search Wolfram Alpha and return summary
      /wiki     Search for wiki page & return summary
      /yt       Search for youtube video & return link
    """
#    ticker_res = re.search('\$([A-Z]{1,4})', params['text'])
#    if ticker_res:
#	try:
#       	    send_message("http://chart.finance.yahoo.com/t?s="+ticker_res.groups(0)[0]+"&lang=en-US&region=US&width=300&height=180")
#	except Exception:
#	    pass
#
    if params is None:
        params = json.loads(request.params.keys()[0])
    text_in = params["text"].split()
    try:
        s_type, query = text_in[0].lower(), " ".join(text_in[1:])
    except IndexError as e:
        return  # Not enough inputs to perform a search

    try:
        msg = SEARCHES[s_type]["fn"](query, params["sender_id"])
        send_message(msg)
    except (KeyError, NameError) as e:
        pass  # Ignore invalid keys to the lookup dict
    except Exception as e:
        send_message("WTF: {}".format(str(e)))


@route('/')
def home():
    return "Hi"


SEARCHES = {
    "/help": {
        "fn": show_help,
        "help": "Show this help message",
    },
    "/gif": {
        "fn": search_gif,
        "help": "Search Giphy for gifs and return first link if found",
    },
    "/img": {
        "fn": search_img,
        "help": "Search Google images & return first link if found",
    },
    "/lunch": {
        "fn": search_lunch,
        "help": "Find some lunch cuisines",
    },
    "/py": {
        "fn": python_eval,
        "help": "Perform python function / command & return stdout",
    },
    "/query": {
        "fn": search_wolfram,
        "help": "Search Wolfram Alpha and return summary",
    },
    "/wiki": {
        "fn": search_wiki,
        "help": "Search for wiki page & return summary",
    },
    "/yt": {
        "fn": search_yt,
        "help": "Search for youtube video & return link",
    },
}
# =============================================================================
# Entry Code
# =============================================================================
if __name__ == "__main__":
    send_message("http://media3.giphy.com/media/xTiTnoHt2NwerFMsCI/200.gif")
    run(host='0.0.0.0', port=80)

app = default_app()
