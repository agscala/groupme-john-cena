#!/usr/bin/env python

"""
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
import dice
import boardgamegeek
import settings
from googleapiclient.discovery import build


# =============================================================================
# Global variables & constants
# =============================================================================
# gif -------------------------------------------------------------------------
GIF_KEY = settings.GIF_KEY
GIF_SEARCH = settings.GIF_SEARCH
# image -----------------------------------------------------------------------
IMG_KEY = settings.IMG_KEY 
IMG_CX = settings.IMG_CX 
# maps ------------------------------------------------------------------------
MAPS_URL = settings.MAPS_URL 
MAPS_KEY = settings.MAPS_KEY 
# python ----------------------------------------------------------------------
# wolfram ---------------------------------------------------------------------
WOLF_KEY = settings.WOLF_KEY 
# wiki ------------------------------------------------------------------------
# youtube ---------------------------------------------------------------------
YT_KEY = settings.YT_KEY 
YT_REQ = settings.YT_REQ 
#weather ----------------------------------------------------------------------
WEATHER_URL = settings.WEATHER_URL 
FORECAST_URL = settings.FORECAST_URL 

JOHN_CENA_ACTIVATE = settings.JOHN_CENA_ACTIVATE 
JOHN_CENA_SAD = settings.JOHN_CENA_SAD 
JOHN_CENA_WTF = settings.JOHN_CENA_WTF 

GROUPME_API_URL = settings.GROUPME_API_URL 
BOT_ID = settings.BOT_ID 


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
            requests.post(GROUPME_API_URL, data=data)
        self.clear_all()  # Don't send the same message twice


# =============================================================================
# Search Functions
# =============================================================================
def search_boardgamegeek(query, sender):
    try:
        bgg = boardgamegeek.BoardGameGeek(disable_ssl=True)
        games = bgg.search(query)
        full_games = [bgg.game(game.name) for game in games[:5]]
        game = full_games[0]
        for g in full_games:
            if g.users_rated > game.users_rated:
                game = g

        response = """{title} ({year})\n
Average Rating: {average_rating} (rated by {num_ratings} players)
Players: {min_players}-{max_players}
Playing Time: {playing_time} minutes
Mechanics: {mechanics}
URL: {url}
Description: {description}...
        """.format(**{
            "title": game.name,
            "year": game.year,
            "average_rating": game.rating_average,
            "average_weight": game.rating_average_weight,
            "num_ratings": game.users_rated,
            "playing_time": game.playing_time,
            "min_players": game.min_players,
            "max_players": game.max_players,
            "mechanics": ", ".join(game.mechanics),
            "url": "https://boardgamegeek.com/boardgame/" + str(game.id)
        })

        CENA.set_text(response)

    except Exception as e:
        raise e
        CENA.set_text("No results found on BoardGameGeek")


def coinflip(query, sender):
    try:
        result = random.randint(0, 1)
        if result is 0:
            CENA.set_text("https://upload.wikimedia.org/wikipedia/en/thumb/6/6c/Toonie_-_back.png/220px-Toonie_-_back.png")
        else:
            CENA.set_text("https://upload.wikimedia.org/wikipedia/en/d/d2/Toonie_-_front.png")
    except Exception:
        CENA.set_text("They rolled off the table...")

def roll_dice(query, sender):
    try:
        result = dice.roll(query)
        CENA.set_text(str(result))
    except Exception:
        CENA.set_text("They rolled off the table...")


def print_subreddit(query, sender):
    CENA.set_text("https://reddit.com/r/{}".format(query))


def get_google_images_items(query, gif=False):
    #service = build("customsearch", "v1", developerKey=IMG_KEY)
    if gif:
        try:
            # searcher = service.cse().list(q=query, searchType="image", cx=IMG_CX, safe="off", fileType="gif")
            parameters = {
                "tbs": "itp:animated",
                "searchType": "image",
                "q": query,
                "key": IMG_KEY,
                "cx": IMG_CX,
                #"safe": "off",
                "fileType": "gif",
                "hq": "animated"
            }
            req = requests.get("https://www.googleapis.com/customsearch/v1",params=parameters)
            return req.json()["items"]
        except Exception as e:
            CENA.set_text("aaron your code fucking sucks: {}".format(str(e)))
            CENA.send_message()
    else:
        service = build("customsearch", "v1", developerKey=IMG_KEY)
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
    except Exception as e:
        CENA.set_text("ERROR: {}".format(str(e)))
        CENA.send_message()
        time.sleep(0.05)
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
    except Exception as e:
        CENA.set_text("ERROR: {}".format(str(e)))
        CENA.send_message()
        time.sleep(0.05)
        CENA.set_text("Couldn't find a gif, here's a google image instead.")
        CENA.send_message()
        search_img(query, sender)


def search_img(query, sender):
    """Search for Google images and return"""
    try:
        items = get_google_images_items(query, False)
        url = items[0]["link"]
        CENA.set_text(url)
    except Exception as e:
        CENA.set_text("ERROR: {}".format(str(e)))
        CENA.send_message()
        time.sleep(0.05)
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
        text = page.summary.split("\n")[0][:900]
        text += "\n{0}".format(page.url)
        CENA.set_text(text)
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


def get_weather_search(query):
    searches = {
        "city": {
            "re": re.compile(r"(^[a-zA-Z]+)(,\s*[a-zA-Z]+)*"),
            "url": "q={0}",
        },
        "coordinates": {
            "re": re.compile(r"^\s*([+-]?[0-9]{1,3}(?:\.?[0-9]+)?[NSns]?),?\s*([+-]?[0-9]{1,3}(?:\.?[0-9]+)?[WEwe]?)\s*$"),
            "url": "lat={0}&lon={1}",
        },
        "zip": {
            "re": re.compile("^\s*([0-9]{5})\s*"),
            "url": "zip={0}",
        },
    }
    search = "q=Detroit,MI"
    try:
        for k, v in searches.items():
            res = v["re"].match(query)
            if res:
                if k == "city":
                    search = v["url"].format(res.group().replace(" ", ""))
                elif k == "coordinates":
                    lat, lon = res.groups()
                    # Work with lower-case, and no need for + sign
                    lat = lat.lower().replace("+", "")
                    lon = lon.lower().replace("+", "")
                    # Checking NSEW in the coordinates to make them positive
                    # or negative based
                    if "n" in lat:
                        lat = lat.replace("n", "")  # remove the N
                        lat = abs(float(lat))  # North is positive
                    elif "s" in lat:
                        lat = lat.replace("s", "")  # Remove the S
                        if not lat.startswith("-"):  # Check if we start with negative, and add if necessary
                            lat = "-{0}".format(lat)

                    if "w" in lon:
                        lon = lon.replace("w", "")  # Remove the W
                        if not lon.startswith("-"):  # Check if we start with negative, and add if necessary
                            lon = "-{0}".format(lon)
                    elif "e" in lon:
                        lon = lon.replace("e", "")  # Remove the E
                        lon = abs(float(lon))  # East is positive

                    # Check that both longitude & latitude are within valid
                    # ranges. +/-90 for latitude, +-180 for longitude
                    if ((-90.0 <= float(lat) <= 90.0) and
                       (-180.0 <= float(lon) <= 180.0)):
                        pass
                    else:
                        raise Exception("Invalid coordinates!")
                    search = v["url"].format(lat, lon)
                elif k == "zip":
                    search = v["url"].format(res.groups()[0])
                break
    except Exception as e:
        CENA.set_text("Error creating weather query: {0}".format(str(e)))
        CENA.send_message()
    return search


def search_weather(query, sender):
    try:
        search = get_weather_search(query)
        url = WEATHER_URL.format(search)
        r = requests.get(url)
        city = r.json()['name']
        temp = r.json()['main']['temp']
        condition = r.json()['weather'][0]["main"]
        CENA.set_text("City: {}\nTemp: {}\nConditions: {}".format(city, temp, condition))
    except Exception as e:
        CENA.set_text("FUCK YOU!")
        CENA.send_message()
        CENA.set_text(str(e))
        CENA.send_message()


def search_forecast(query, sender):
    try:
        search = get_weather_search(query)
        url = FORECAST_URL.format(search)
        r = requests.get(url)
        js = r.json()
        text = "City: {}\n".format(js["city"]["name"])
        for day in js["list"]:
            dt = time.strftime("%a %Y-%m-%d", time.localtime(day["dt"]))
            text += "\nDay: {}".format(dt)
            text += "\nHigh: {}".format(day["temp"]["max"])
            text += "\nLow: {}".format(day["temp"]["min"])
            text += "\nConditions: {}\n".format(day["weather"][0]["description"])
        CENA.set_text(text.strip())
    except Exception as e:
        CENA.set_text("FUCK YOU!")
        CENA.send_message()
        CENA.set_text(str(e))
        CENA.send_message()


def show_help(query, sender):
    fns = sorted(SEARCHES.keys())
    l = max(map(len, fns)) + 4
    fnhelp1 = "\n".join(["  {:<{}}{}".format(f, l, SEARCHES[f]["help"]) for f in fns[:12]])
    fnhelp2 = "\n".join(["  {:<{}}{}".format(f, l, SEARCHES[f]["help"]) for f in fns[12:]])
    CENA.set_text(__doc__.format(fnhelp1))
    CENA.send_message()
    CENA.set_text(__doc__.format(fnhelp2))
    CENA.send_message()


def redeploy(query, sender):
    subprocess.call("git pull origin master", shell=True)
    subprocess.call("pip install -r requirements.txt", shell=True)
    subprocess.call("supervisorctl restart johncena", shell=True)
    CENA.set_text(JOHN_CENA_ACTIVATE)
    CENA.send_message()


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
      /weather	Search for current weather & returns city, temp, and condition
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

    if "john cena" in params["text"].lower():
        CENA.set_text(JOHN_CENA_ACTIVATE)

    CENA.send_message()


@route('/')
def home():
    return "Hi"


SEARCHES = {
    "/help": {
        "fn": show_help,
        "help": "Show this help message",
    },
    "/forecast": {
        "fn": search_forecast,
        "help": "Get a 5-day forecast for a specified city",
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
    "/query": {
        "fn": search_wolfram,
        "help": "Search Wolfram Alpha and return summary",
    },
    "/r": {
        "fn": print_subreddit,
        "help": "prints link to subreddits",
    },
    "/roll": {
        "fn": roll_dice,
        "help": "DnD style dice roll. 2d6 shows individual rolls, 2d6t shows sum",
    },
    "/coinflip": {
        "fn": coinflip,
        "help": "Flip a coin",
    },
    "/randgif": {
        "fn": search_randgif,
        "help": "Get a random google images gif",
    },
    "/shaq": {
        "fn": shaq,
        "help": "Get a Shaq goldbond quote",
    },
    "/bgg": {
        "fn": search_boardgamegeek,
        "help": "Search BoardGameGeek",
    },
    "/wiki": {
        "fn": search_wiki,
        "help": "Search for wiki page & return summary",
    },
    "/yt": {
        "fn": search_yt,
        "help": "Search for youtube video & return link",
    },
    "/weather": {
        "fn": search_weather,
        "help": "Search current weather conditions. Possible searches are by: city/state, zip code, and lat/long coordinates"
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
    run(host='0.0.0.0', port=80)

app = default_app()
