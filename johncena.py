# A very simple Bottle Hello World app for you to get started with...
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

rl = RateLimit()

def python_eval(stmt):
    time.sleep(0.05)
    return str(eval(stmt))

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
    BASE_URL = 'https://ajax.googleapis.com/ajax/services/search/images?'\
        'v=1.0&q=' + query + '&start=%d'

    start = 0 # Google's start query string parameter for pagination.
    r = requests.get(BASE_URL % start)
    image_info = json.loads(r.text)['responseData']['results'][0]
    url = image_info['unescapedUrl']
    return url

def gif(query):
    query = query.replace(" ", "+")
    res = requests.get("http://api.giphy.com/v1/gifs/search?q="+query+"&api_key=dc6zaTOxFJmzC")
    return res.json()["data"][0]["images"]["fixed_height"]["url"]

def send_message(text, image=None):
    time.sleep(0.05)
    data = {"bot_id": "63747737acc3dbf60d7df729fd", "text": text}
    if image:
        data["attachments"] = [{"type": "image", "url": image}]

    requests.post("https://api.groupme.com/v3/bots/post", data=data)




send_message("http://media3.giphy.com/media/xTiTnoHt2NwerFMsCI/200.gif")


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
    if params['text'].startswith("/wiki"):
	try:
	    search = " ".join(params['text'].split(" ")[1:])
	    page = wikipedia.page(search)
	    send_message(page.summary.split("\n")[0][:900])
	except Exception:
	    send_message("Couldn't find a match on wikipedia. Could it be one of these?\n" + "\n".join(wikipedia.search(search)[:5]))

    if params['text'].startswith("/img"):
	if not rl.can_send(params["sender_id"]):
	    send_message("You can request another image in " + rl.time_remaining(params["sender_id"]) + " minutes.")
            return
	    
	try:
            rl.mark_sending(params["sender_id"])
	    search = " ".join(params['text'].split(" ")[1:])
	    image_url = gis(search)
	    send_message(image_url)
	except Exception:
	    send_message("Couldn't find an image")

    if params['text'].startswith("/yt"):
	try:
	    search = " ".join(params['text'].split(" ")[1:])
	    youtube_url = youtube(search)
	    send_message(youtube_url)
	except Exception:
	    send_message("Couldn't find a video on youtube")

    if params['text'].startswith("/query"):
	try:
	    search = " ".join(params['text'].split(" ")[1:])
	    results = wolframalphaSearch(search)
	    print "RESULTS", results
	    send_message(results)
	except Exception, e:
	    print e
	    send_message("Error processing WolframAlpha search")

    if params['text'].startswith("/py"):
	try:
	    search = " ".join(params['text'].split(" ")[1:])
	    res = python_eval(search)
	    send_message(">>>> " + res[:995])
	except Exception, e:
	    send_message("Error: ", e)

    if params['text'].startswith("/gif"):
	if not rl.can_send(params["sender_id"]):
	    send_message("You can request another image in " + rl.time_remaining(params["sender_id"]) + " minutes.")
            return

	try:
            rl.mark_sending(params["sender_id"])
	    search = " ".join(params['text'].split(" ")[1:])
	    image_url = gif(search)
	    send_message(image_url)
	except Exception:
	    send_message("Couldn't find a gif, here's a google image instead.")
	    search = " ".join(params['text'].split(" ")[1:])
	    image_url = gis(search)
	    send_message(image_url)

@route('/')
def home():
    return "Hi"

if __name__ == "__main__":
    run(host='0.0.0.0', port=80)
