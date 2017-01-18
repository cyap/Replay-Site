""" Module dealing with assembly and management of set of replay objects. """

import multiprocessing.dummy
import traceback
from urllib2 import urlopen, HTTPError

from bs4 import BeautifulSoup

from replay import replay

DEFAULT_URL_HEADER = "http://replay.pokemonshowdown.com/"

def replays_from_thread(threadurl, url_header=DEFAULT_URL_HEADER, tiers=None):
	""" Parse given thread for replay links and convert to set of replays. """
	thread = BeautifulSoup(urlopen(threadurl).read(), "html.parser")
	urls = (url.get("href") for url in thread.findAll("a") 
			if url.get("href") and url.get("href").startswith(url_header))
	# Optional: Filter by tier
	# TODO: Tier from replay object or URL?
	if tiers:
		urls = (url for url in urls if url.split("-")[-2] in tiers)
	return replays_from_links(urls)

def replays_from_range(range, url_header=DEFAULT_URL_HEADER, server="smogtours",
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
	complete_url_header = url_header + server + "-" + tier + "-"
	urls = (complete_url_header + str(i) for i in range)
	return replays_from_links(urls)

def replays_from_links(urls):
	""" Helper function to convert replay links to replay objects. """
	pool = multiprocessing.dummy.Pool(13)
	# Throw out invalid replays
	return set(filter(None, pool.map(open_replay, urls)))
	
def open_replay(url):
	""" Validate replay links and open; return None if 404 error. """
	try:
		return replay(url)
	except HTTPError:
		return
	except:
		traceback.print_exc()
		print url
		return	

