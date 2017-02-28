""" Module dealing with assembly and management of set of replay objects. """

import multiprocessing.dummy
import traceback
from urllib2 import urlopen, Request, HTTPError

from bs4 import BeautifulSoup

from replay import Log, Replay

DEFAULT_URL_HEADER = "http://replay.pokemonshowdown.com/"
# User-agent wrapper to mimic browser requests
REQUEST_HEADER = {'User-Agent' : 
"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML,"
"like Gecko) Chrome/54.0.2840.98 Safari/537.36"}

def replays_from_thread(threadurl, url_header=DEFAULT_URL_HEADER, tiers=None, 
						start=1, end=None):
	""" Parse given thread for replay links and convert to set of replays.
	Parse entire thread by default, with optional start and end parameters to
	limit parsing to a range of posts.
	"""
	try:
		thread = BeautifulSoup(
				"".join(
				urlopen(threadurl)
				.read()
				.split("</article>")[start-1:end])
				, "html.parser")
		urls = (url.get("href") for url in thread.findAll("a") 
				if url.get("href") and url.get("href").startswith(url_header))
		# Optional: Filter by tier
		# TODO: Tier from replay object or URL?
		if tiers:
			urls = (url for url in urls if url.split("-")[-2] in tiers)
		return replays_from_links(urls)
	except:
		return {}


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

def replays_from_user(name, url_header=DEFAULT_URL_HEADER,
	tier="gen7pokebankou"):
	""" Query the PS replay database for the saved replays of a given username
		(limit: last 10 pages' worth of replays).
	"""
	complete_url_header = url_header + 'search/?user=' + name + '&page='
	page = BeautifulSoup(
			"\n".join(
			(urlopen(Request(complete_url_header + str(i),
			headers=REQUEST_HEADER))
			.read() 
			for i in xrange(1, 11)))
			, "html.parser")
	urls = (url.get("href").strip("/") for url in page.findAll("a") 
			if url.get("data-target"))
	urls = [url_header + url for url in urls if len(url.split("-")) > 2 and url.split("-")[-2] == tier]
	#urls = [url_header + url for url in urls if url.split("-")[-2] == tier]
	return replays_from_links(urls)
		
def replays_from_links(urls):
	""" Helper function to convert replay links to replay objects. """
	pool = multiprocessing.dummy.Pool(13)
	# Throw out invalid replays
	return set(filter(None, pool.map(open_replay, urls)))
	
def open_replay(url):
	""" Open replay links and validate; return None if 404 error. """
	# Check if URL adheres to the usual format of /*tier-number
	try:
		number = int(url.split("-")[-1])
		tier = url.split("-")[-2]
	except:
		number = 0
		tier = None
	# Validate log
	try:
		log = Log([line for line in 
				urlopen(Request(url, headers=REQUEST_HEADER))
				.read()
				.split("\n")
				if line.startswith("|")])
		players = log.parse_players()
		winner = log.parse_winner()
		return Replay(log, players, winner, url, number, tier)
	except HTTPError:
		# Unsaved replay
		return
	except:
		# Corrupted log file
		traceback.print_exc()
		print url
		return	

if __name__ == "__main__":
	#print set(replays_from_user("McMeghan", tier="gen5ou"))
	a = replays_from_user("Atq)+Fear", tier="gen2ou")
	for replay in a:
		print replay.url