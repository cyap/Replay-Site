""" Module dealing with assembly and management of set of replay objects. """

import multiprocessing.dummy
import traceback
from urllib.parse import quote
from urllib.request import urlopen, Request
from urllib.error import HTTPError

from bs4 import BeautifulSoup

from .replay import Log, Replay

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
		posts = []
		if not end:
			# Calculate page of last post
			first_page = BeautifulSoup(urlopen(threadurl)
						.read().decode(), "html.parser")
			# TODO: iterate over string and find first digit
			try:
				end = int(str(first_page.find(class_="pageNavHeader"))
						.split("of ")[1].split("<")[0]) * 25
			except:
				# only one page
				end = 25
		# Iterate through all pages
		for i in range(int(start / 25) + 1, int((end-1) / 25) + 2):
			page_num = "page-" + str(i)
			try:
				page = (urlopen(threadurl.strip() + page_num)
						.read().decode().split("</article>")[:-1])
				posts += page
			except:
				traceback.print_exc()
		post_start = start - int(start / 25) * 25 - 1
		post_end = post_start + (end - start) + 1
	
		thread = BeautifulSoup("".join(posts[post_start:post_end]),
			"html.parser")
		urls = (url.get("href") for url in thread.findAll("a") 
				if url.get("href") and url.get("href").split(":")[-1].startswith(url_header.split(":")[1]))
		# Optional: Filter by tier
	
		# Change to tiers from log
		# replay.pokemonshowdown.com/ou doesn't work
		# also some old replays
		if tiers:
			urls = (url for url in urls if url.split("-")[-2].split("/")[-1] 
				in tiers)
		return logs_from_links(urls)
	except:
		traceback.print_exc()
		return []


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

	# Main server URL formatted differently
	if server:
		server += '-'

	complete_url_header = url_header + server + '-'.join([tier, ''])

	urls = (complete_url_header + str(i) for i in range)
	return logs_from_links(urls)

def replays_from_user(name, url_header=DEFAULT_URL_HEADER,
	tier="gen7pokebankou"):
	""" Query the PS replay database for the saved replays of a given username
		(limit: last 10 pages' worth of replays).
	"""
	complete_url_header = url_header + 'search/?user=' + quote(name) + '&page='
	page = BeautifulSoup(
			"\n".join(
			(urlopen(Request(complete_url_header + str(i),
			headers=REQUEST_HEADER))
			.read().decode()
			for i in range(1, 11)))
			, "html.parser")
	urls = (url.get("href").strip("/") for url in page.findAll("a") 
			if url.get("data-target"))
	urls = [url_header + url for url in urls if "-" in url and
			url.split("-")[-2].split("/")[-1] == tier]
	return replays_from_links(urls)
	
def logs_from_links(urls):
	try:
		pool = multiprocessing.dummy.Pool(13)
		return list(filter(None, pool.map(open_log, urls)))
	except:
		return []
	finally:
		pool.close()

def open_log(url):
	""" Open replay links and validate; return None if 404 error. """
	try:
		log = Log([line for line in 
				urlopen(Request(url, headers=REQUEST_HEADER))
				.read().decode()
				.split('<script type="text/plain" class="log">')[1]
				.splitlines()
				if line.startswith("|")], url)
		return log
	except HTTPError:
		# Unsaved replay
		#print(url)
		return
	except:
		# Corrupted log file
		#print(url)
		traceback.print_exc()
		return
		
def initialize_replay(log, url=None, wnum=None):	
	# players
	try:
		players = log.parse_players()
	except:
		#raise NoPlayerError
		return None
		
	if not players:
		return None
		
	if wnum == None:
		try:
			winner = log.parse_winner()
		except:
			raise NoWinnerError
	else:
		winner = list(players.keys())[wnum-1] if wnum else ""
	try:
		# TODO: Lazy initialization?
		number = int(url.split("-")[-1])
		tier = url.split("-")[-2]
	except:
		number = 0
		tier = None
	return Replay(log, players, winner, url, number, tier)
		
def replays_from_links(urls):
	""" Helper function to convert replay links to replay objects. """
	try:
		pool = multiprocessing.dummy.Pool(13)
		# Throw out invalid replays
		return list(filter(None, pool.map(
			lambda url: initialize_replay(open_log(url), url), urls)))
	except:
		traceback.print_exc()
		return
	finally:
		pool.close()
		
class NoWinnerError(Exception):
	pass

class NoPlayerError(Exception):
	pass