""" Module dealing with assembly and management of set of replay objects. """

import multiprocessing.dummy
import traceback
from urllib2 import urlopen

from bs4 import BeautifulSoup

from replay import replay

defaultURLHeader = "http://replay.pokemonshowdown.com/"

def replaysFromThread(threadurl, URLHeader=defaultURLHeader, tier=None):
	""" Parse given thread for replay links and convert to set of replays. """
	thread = BeautifulSoup(urlopen(threadurl).read(), "html.parser")
	urls = (url.get("href") for url in thread.findAll("a") 
			if url.get("href") and url.get("href").startswith(URLHeader))
	# Optional: Filter by tier
	if tier:
		urls = (url for url in urls if url.split("-")[1] == tier)
	return replaysFromLinks(urls)

def replaysFromRange(range, URLHeader=defaultURLHeader, server="smogtours",
	tier="gen7pokebankou"):
	""" Assemble list of replays through mutating the default replay URL. 
	
	Replay URLs are generated in the following format:
	http://replay.pokemonshowdown.com/[server]-[tier]-[N]
	where N indicates that the match was the Nth played on the server. As such,
	a given range will correspond to matches played during a given timeframe. 
	
	A URL assembled in this manner may not correspond to a valid replay, either
	because the replay was not saved or because a different tier was played for
	that number.
	"""
	completeURLHeader = URLHeader + server + "-" + tier + "-"
	urls = (completeURLHeader + str(i) for i in range)
	return replaysFromLinks(urls)

def replaysFromLinks(urls):
	""" Helper function to convert replay links to replay objects. """
	pool = multiprocessing.dummy.Pool(13)
	# Throw out invalid replays
	return set(filter(None, pool.map(openReplay, urls)))
	
def openReplay(url):
	""" Validate replay links and open; return None if 404 error. """
	try:
		return replay(url)
	except:
		#traceback.print_exc()
		#print url
		return	

