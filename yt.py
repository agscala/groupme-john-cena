import requests
def youtube(query):
	formatted_query = query.replace(" ", "+")
	x = requests.get("https://www.googleapis.com/youtube/v3/search?part=snippet&q="+formatted_query+"&key=AIzaSyBIbGpoq6PBDRjdIbTojjEiztZerVooOjg")
	id = x.json()["items"][0]['id']['videoId']
	return "https://www.youtube.com/watch?v=" + id

print youtube("john cena")
		
