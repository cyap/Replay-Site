from urllib2 import urlopen, Request
from multiprocessing.dummy import Pool
from bs4 import BeautifulSoup
from replay import replay
from collections import Counter
import traceback

class replaySet:

	""" Class representing set of replay objects. 
		Accompanying methods form and manage the set of replay objects. 
	"""

	urlHeader = "http://replay.pokemonshowdown.com/"
	requestHeader = {"User-Agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)"
		"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36"}
	
	def __init__(self, thread = None, tier = None, range = None, links = None, iterable = None):
		self.replays = set()
		if thread:
			self.setReplaysFromThread(thread, tier)
		if range:
			self.setReplaysFromRange(range)
		if links:
			self.setReplaysFromLinks(links)
		if iterable:
			self.setReplaysFromIterable(iterable)

	def setReplaysFromThread(self, threadurl, tier = None):
		""" Given a thread URL, convert HTML into BeautifulSoup DOM structure
			and parse for links to replays as identified by the replay domain name.
			Call function to convert ensuing generator into a set of replay objects and 
			add to set of replays.
		"""
		thread = BeautifulSoup(urlopen(threadurl).read(), "html.parser")
		urls = (url.get("href") for url in thread.findAll("a") 
				if url.get("href") and url.get("href").startswith(self.urlHeader))
		if tier:
			urls = (url for url in urls if url.split("-")[1] == tier)
			# TODO: Place tier checking in other methods
		self.setReplaysFromLinks(urls)

	def setReplaysFromRange(self, range, server="smogtours", tier="gen7pokebankou"):
		""" Given a range of numbers and pairings, assemble each replay's URL and open.
			Call function to convert ensuing generator into a set of replay objects and
			add to set of replays.
		"""
		urlHeader = self.urlHeader + server + "-" + tier + "-"
		urls = (urlHeader + str(i) for i in range)
		self.setReplaysFromLinks(urls)
	
	def setReplaysFromLinks(self, urls):
		""" Given an iterable of urls, convert to set of corresponding replay objects 
			with invalid replays filtered out and add to set of replays.
		"""
		pool = Pool(13)
		self.replays = self.replays | set(filter(None, pool.map(self.openReplay, urls)))
		
	def setReplaysFromIterable(self, iterable):
		""" Given iterable of replay objects, add to set of replays. """
		self.replays = self.replays | set(iterable)
		
	def getReplays(self):
		""" Return set of replays. """
		return self.replays
			
	@classmethod
	def openReplay(cls, url):
		""" Given a replay URL, return a replay object. """
		# User-agent wrapper to issue browser-like requests
		req = Request(url, headers=cls.requestHeader)
		try:
			return replay(url, urlopen(req).read())
		except:
			# 404 error
			#traceback.print_exc()
			#print url
			return None

