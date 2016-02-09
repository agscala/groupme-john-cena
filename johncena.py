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
import random
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

JOHN_CENA_ACTIVATE = "http://media3.giphy.com/media/xTiTnoHt2NwerFMsCI/200.gif"
JOHN_CENA_SAD = "http://static.giantbomb.com/uploads/screen_kubrick/9/93998/2651842-untitled.jpg"
JOHN_CENA_WTF = "https://whatistheexcel.com/wooobooru/_images/91fa21f02ccbe8980eae483263197965/812%20-%20john_cena%20macro%20wtf_am_i_looking_at%20wwe.png"


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


def send_message(data=None):
    """Send a John Cena message to GroupMe"""
    time.sleep(0.05)
    if data is None:
        data = dict()
    data["bot_id"] = "63747737acc3dbf60d7df729fd"
    requests.post("https://api.groupme.com/v3/bots/post", data=data)


# =============================================================================
# Search Functions
# =============================================================================
def search_gif(query, sender):
    """Search Giphy and return link for search"""
    data = dict()
    if not rl.can_send(sender):
        data["text"] = "You can request another image in {} minutes.".format(rl.time_remaining(sender))
        return data

    try:
        rl.mark_sending(sender)
        time.sleep(0.05)
        query = query.replace(" ", "+")
        res = requests.get(GIF_SEARCH.format(query, GIF_KEY))
        url = res.json()["data"][0]["images"]["fixed_height"]["url"]
        data["attachments"] = [{"type": "image", "url": url}]
    except Exception:
        data["text"] = "Couldn't find a gif, here's a google image instead."
        send_message(data)
        data = search_img(query, sender)
    return data


def search_img(query, sender):
    """Search for Google images and return"""
    data = dict()
    if not rl.can_send(sender):
        data["text"] = "You can request another image in {} minutes.".format(rl.time_remaining(sender))
        return data

    try:
        rl.mark_sending(sender)
        service = build("customsearch", "v1", developerKey=IMG_KEY)
        searcher = service.cse().list(q=query, searchType="image", cx=IMG_CX,
                                      safe="off")
        res = searcher.execute()
        url = res["items"][0]["link"]
        data["attachments"] = [{"type": "image", "url": url}]
    except Exception:
        data["text"] = "Couldn't find an image"
        data["attachments"] = [{"type": "image", "url": JOHN_CENA_SAD}]
    return data


def maps_search(query, req_url, keys=None, max_res=5, rand=False, attach=False):
    # Basic setup -------------------------------------------------------------
    data = dict()
    print_keys = {
        "name": "Name",
        "rating": "Rating",
        "formatted_address": "Address",
    }
    if keys is None:
        keys = ["name", "rating", "formatted_address"]

    # Perform the Maps request ------------------------------------------------
    try:
        r = requests.get(req_url, verify=False)
        res = r.json()["results"]
    except Exception:
        data["text"] = "Failed to get Maps info"
        return data

    # Filter all the data -----------------------------------------------------
    msg = ""
    if res:
        # Set up basic data to return -----------------------------------------
        loc = {"type": "location", "lng": None, "lat": None, "name": None}
        msg = "Suggestions for {}\n\n".format(query)
        l = max(map(len, print_keys.values()))
        data["attachments"] = []

        # Perform data selection ----------------------------------------------
        if rand:
            places = [random.choice(res)]
        else:
            places = res[:max_res]

        # Create text string and location attachments -------------------------
        for idx, place in enumerate(places):
            loc_data = place["geometry"]["location"]
            loc["lng"] = loc_data["lng"]
            loc["lat"] = loc_data["lat"]
            loc["name"] = place["name"]
            if attach:
                data["attachments"].append(loc)
            for key in keys:
                try:
                    print_key = print_keys[key]
                    msg += "{:<{}}: {}\n".format(print_key, l, place[key])
                except KeyError:
                    msg += "{:<{}}: {}\n".format(print_key, l, None)
            msg += "\n"
    data["text"] = msg.strip()
    return data


def search_lunch(query, sender):
    query = query + " lunch"
    url = ("{}?query={}&key={}&types=restaurant").format(MAPS_URL, query,
                                                         MAPS_KEY)
    data = maps_search(query, url, None, 5, True, True)
    return data


def search_maps(query, sender):
    keys = ["name", "formatted_address"]
    url = ("{}?query={}&key={}").format(MAPS_URL, query, MAPS_KEY)
    data = maps_search(query, url, keys, 5, False, False)
    return data


def python_eval(query, sender):
    """Call a local python command/function and return stdout"""
    data = dict()
    cmd = "python -c \"{}\"".format(query)
    time.sleep(0.05)
    try:
        proc = subprocess.Popen(cmd, stdin=None, stdout=subprocess.PIPE,
                                shell=True)
        stdout = proc.communicate()[0]
        data["text"] = ">>> {}".format(str(stdout)[:995])
    except Exception as e:
        data["text"] = "Error: {}".format(str(e))
    return data


def search_wolfram(query, sender):
    """Search wolfram alpha for info"""
    data = dict()
    try:
        client = wolframalpha.Client(WOLF_KEY)
        res = client.query(query)
        data["text"] = "\n".join([pod.text for pod in res.pods[:2]])
    except Exception:
        data["text"] = "Error processing WolframAlpha search"
    return data


def search_wiki(query, sender):
    """Search wikipedia for subject page"""
    data = dict()
    try:
        page = wikipedia.page(query)
        data["text"] = page.summary.split("\n")[0][:900]
    except Exception:
        other_pages = "\n".join(wikipedia.search(query)[:5])
        data["text"] = ("Couldn't find a match on wikipedia. "
                        "Could it be one of these?\n{}".format(other_pages))
    return data


def search_yt(query, sender):
    """Perform youtube video search"""
    data = dict()
    try:
        formatted_query = query.replace(" ", "+")
        x = requests.get(YT_REQ.format(formatted_query, YT_KEY))
        # Loop through all items and find first video. Skip all channels.
        for item in x.json()["items"]:
            yt_id = item["id"]
            if yt_id["kind"].lower() in ("youtube#video", ):
                videoid = yt_id["videoId"]
                break
        data["text"] = "https://www.youtube.com/watch?v=" + videoid
    except Exception:
        data["text"] = "Couldn't find a video on youtube"
    return data


def show_help(query, sender):
    fns = sorted(SEARCHES.keys())
    l = max(map(len, fns)) + 4
    fnhelp = "\n".join(["  {:<{}}{}".format(f, l, SEARCHES[f]["help"])
                        for f in fns])
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
      /map      Search Google maps for top 5 stuff
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
        data = SEARCHES[s_type]["fn"](query, params["sender_id"])
        send_message(data)
    except (KeyError, NameError) as e:
        pass  # Ignore invalid keys to the lookup dict
    except Exception as e:
        data = {"text": "WTF: {}".format(str(e))}
        data["attachments"] = [{"type": "image", "url": JOHN_CENA_WTF}]
        send_message(data)


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
        "help": "Find some lunch cuisines (/lunch [loc | query])",
    },
    "/map": {
        "fn": search_maps,
        "help": "Search Google maps for top 5 locations related to query",
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
    startup = {"text": "John Cena ACTIVATE!", "attachments": [{"type": "image", "url": JOHN_CENA_ACTIVATE}]}
    send_message(startup)
    run(host='0.0.0.0', port=80)

app = default_app()
