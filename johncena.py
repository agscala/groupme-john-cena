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
import subprocess
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

GROUPME_API_URL = "https://api.groupme.com/v3/bots/post"
BOT_ID = "63747737acc3dbf60d7df729fd"


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


class GroupmeMessage(object):
    def __init__(self, text=None, attachments=None, bot_id=BOT_ID):
        self.text = text
        self.attachments = attachments
        self.bot_id = bot_id

    def set_text(self, text):
        self.text = text

    def clear_text(self):
        self.text = ""

    def add_attachment(self, attachment):
        try:
            self.attachments.append(attachment)
        except AttributeError:
            self.attachments = [attachment]

    def set_attachment(self, attachments):
        self.attachments = attachments

    def clear_attachments(self):
        self.attachments = None

    def clear_all(self):
        self.clear_text()
        self.clear_attachments()

    def send_message(self):
        data = dict()
        if self.text:
            data["text"] = self.text
        if self.attachments:
            data["attachments"] = self.attachments
        if data:
            data["bot_id"] = self.bot_id
            print(data)
            requests.post(GROUPME_API_URL, data=data)
        self.clear_all()  # Don't send the same message twice


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


# =============================================================================
# Search Functions
# =============================================================================
def get_google_images_items(query, gif=False):
    service = build("customsearch", "v1", developerKey=IMG_KEY)
    if gif:
        try:
            # searcher = service.cse().list(q=query, searchType="image", cx=IMG_CX, safe="off", fileType="gif")
            parameters = {
                "q": query,
                "searchType": "image",
                "key": IMG_KEY,
                "cx": IMG_CX,
                "safe": "off",
                "fileType": "gif",
                "hq": "animated",
                "tbs": "itp:animated"
            }
            req = requests.get("https://www.googleapis.com/customsearch/v1",params=parameters)
            # url = req.json()["items"][0]["link"]
            CENA.set_text(req.url)
            CENA.send_message()
            return req.json()["items"]
        except Exception as e:
            CENA.set_text("aaron your code fucking sucks")
            CENA.send_message()
            CENA.set_text(str(e))
            CENA.send_message()
    else:
        searcher = service.cse().list(q=query, searchType="image", cx=IMG_CX, safe="off")
        res = searcher.execute()
        return res["items"]


def search_gif(query, sender):
    """Search Giphy and return link for search"""
    try:
        rl.mark_sending(sender)
        time.sleep(0.05)
        # GIPHY Search ------
        # query = query.replace(" ", "+")
        # res = requests.get(GIF_SEARCH.format(query, GIF_KEY))
        # url = res.json()["data"][0]["images"]["fixed_height"]["url"]
        # CENA.set_text(url)
        items = get_google_images_items(query, True)
        url = items[0]["link"]
        CENA.set_text(url)
    except Exception:
        CENA.set_text("Couldn't find a gif, here's a google image instead.")
        CENA.send_message()
        search_img(query, sender)


def search_randgif(query, sender):
    """Search google images and return link for search"""
    try:
        rl.mark_sending(sender)
        time.sleep(0.05)
        items = get_google_images_items(query, True)
        item = random.choice(items)
        url = item["link"]
        CENA.set_text(url)
    except Exception:
        CENA.set_text("Couldn't find a gif, here's a google image instead.")
        CENA.send_message()
        search_img(query, sender)


def search_img(query, sender):
    """Search for Google images and return"""
    try:
        items = get_google_images_items(query, False)
        url = items[0]["link"]
        CENA.set_text(url)
    except Exception:
        CENA.set_text("Couldn't find an image")


def maps_search(query, req_url, keys=None, max_res=5, rand=False, attach=False):
    # Basic setup -------------------------------------------------------------
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
        CENA.set_text("Failed to get Maps info")
        return

    # Filter all the data -----------------------------------------------------
    msg = ""
    if res:
        # Set up basic data to return -----------------------------------------
        loc = {"type": "location", "lng": None, "lat": None, "name": None}
        msg = "Suggestions for {}\n\n".format(query)
        l = max(map(len, print_keys.values()))

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
                CENA.add_attachment(loc)
            for key in keys:
                try:
                    print_key = print_keys[key]
                    msg += "{:<{}}: {}\n".format(print_key, l, place[key])
                except KeyError:
                    msg += "{:<{}}: {}\n".format(print_key, l, None)
            msg += "\n"
    CENA.set_text(msg.strip())


def search_lunch(query, sender):
    query = query + " lunch"
    url = ("{}?query={}&key={}&types=restaurant").format(MAPS_URL, query,
                                                         MAPS_KEY)
    maps_search(query, url, None, 5, True, True)


def search_maps(query, sender):
    keys = ["name", "formatted_address"]
    url = ("{}?query={}&key={}").format(MAPS_URL, query, MAPS_KEY)
    maps_search(query, url, keys, 5, False, False)


def python_eval(query, sender):
    """Call a local python command/function and return stdout"""
    cmd = "python -c \"{}\"".format(query)
    time.sleep(0.05)
    try:
        proc = subprocess.Popen(cmd, stdin=None, stdout=subprocess.PIPE,
                                shell=True)
        stdout = proc.communicate()[0]
        CENA.set_text(">>> {}".format(str(stdout)[:995]))
    except Exception as e:
        CENA.set_text("Error: {}".format(str(e)))


def search_wolfram(query, sender):
    """Search wolfram alpha for info"""
    try:
        client = wolframalpha.Client(WOLF_KEY)
        res = client.query(query)
        CENA.set_text("\n".join([pod.text for pod in res.pods[:2]]))
    except Exception:
        CENA.set_text("Error processing WolframAlpha search")


def search_wiki(query, sender):
    """Search wikipedia for subject page"""
    try:
        page = wikipedia.page(query)
        CENA.set_text(page.summary.split("\n")[0][:900])
    except Exception:
        other_pages = "\n".join(wikipedia.search(query)[:5])
        CENA.set_text("Couldn't find a match on wikipedia. Could it be one of these?\n{}".format(other_pages))


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
        CENA.set_text("https://www.youtube.com/watch?v={}".format(videoid))
    except Exception:
        CENA.set_text("Couldn't find a video on youtube")


def shaq(query, sender):
    try:
        q = "shaq gold bond quotes"
        items = get_google_images_items(q)
        item = random.choice(items)
        url = item["link"]
        CENA.set_text(url)
    except Exception:
        CENA.set_text("Couldn't find an image")


def show_help(query, sender):
    fns = sorted(SEARCHES.keys())
    l = max(map(len, fns)) + 4
    fnhelp = "\n".join(["  {:<{}}{}".format(f, l, SEARCHES[f]["help"])
                        for f in fns])
    CENA.set_text(__doc__.format(fnhelp))


def redeploy(query, sender):
    subprocess.call("git pull origin master && supervisorctl restart johncena", shell=True)


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
      /redeploy Redeploy John Cena
    """
#    ticker_res = re.search('\$([A-Z]{1,4})', params['text'])
#    if ticker_res:
#	try:
#       	    send_message("http://chart.finance.yahoo.com/t?s="+ticker_res.groups(0)[0]+"&lang=en-US&region=US&width=300&height=180")
#	except Exception:
#	    pass
#
    # Gather parameters (None check is for dev purposes)
    if params is None:
        params = json.loads(request.params.keys()[0])

    text_in = params["text"].split()
    try:
        s_type, query = text_in[0].lower(), " ".join(text_in[1:])
    except IndexError as e:
        return  # Not enough inputs to perform a search

    # Attempt to call function & send CENA's message
    CENA.clear_all()
    try:
        SEARCHES[s_type]["fn"](query, params["sender_id"])
    except (KeyError, NameError) as e:
        CENA.clear_all()
    except Exception as e:
        CENA.set_text("WTF: {}".format(str(e)))
    CENA.send_message()


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
    "/randgif": {
        "fn": search_randgif,
        "help": "Get a random google images gif",
    },
    "/shaq": {
        "fn": shaq,
        "help": "Get a Shaq goldbond quote",
    },
    "/wiki": {
        "fn": search_wiki,
        "help": "Search for wiki page & return summary",
    },
    "/yt": {
        "fn": search_yt,
        "help": "Search for youtube video & return link",
    },
    "/redeploy": {
        "fn": redeploy,
        "help": "Redeploy John Cena (dev purposes only)",
    },
}

CENA = GroupmeMessage()


# =============================================================================
# Entry Code
# =============================================================================
if __name__ == "__main__":
    CENA.set_text("AND HIS NAME IS")
    CENA.send_message()
    time.sleep(1)
    CENA.set_text(JOHN_CENA_ACTIVATE)
    CENA.send_message()
    run(host='0.0.0.0', port=80)

app = default_app()
