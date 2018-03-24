import re
from collections import Counter
from itertools import chain
from urllib.request import urlopen

from fuzzywuzzy import fuzz

class Tournament():

	def __init__(self, replays=None, pairings=None, players=None, alts=None):
		self.replays = replays
		self.pairings = pairings # Set of all pairings
		self.players = players # Set of all players
		self.fuzzyNameMatches = {}
		if alts:
			self.fuzzyNameMatches = alts
		self.pairingReplayMap = {}
		self.unmatchedReplays = self.replays
		self.unmatchedPairings = set(self.pairings)
		
	def filter_replays_by_pairings(self, filter, replays=None):
		""" Return replays whose players correspond to a pairing.
			
		Exact: Checks for perfect matches.
		Fuzzy: Uses fuzzywuzzy's fuzzy string matching library to map each 
		name to the closest match from the given player list. Subsequently
		checks for perfect matches.
		Partial: Uses aforementioned fuzzy string matching, then checks for
		pairings in which at least one player matches. 
		"""
		
		# Default to class properties if nothing passed
		# May change to default regardless
		if not replays:
			replays = self.unmatchedReplays
		match = getattr(self, filter+"_match")
		matchedReplays = {replay for replay in replays if 
						  match(replay, self.unmatchedPairings)}
		self.unmatchedReplays -= matchedReplays
		self.unmatchedPairings -= set(self.pairingReplayMap.keys())
		return matchedReplays
		
	def exact_match(self, replay, pairings=None):
		""" Given a replay object and a list of pairing sets, return boolean
		corresponding to the existence of the replay's player set in the pairing
		list.
		"""
		pairing = frozenset(format_name(player) for player in replay.players)
		if pairing in pairings:
			self.pairingReplayMap[pairing] = (replay, "exact")
			pairings.remove(pairing)
			return True
		return False
	
	def fuzzy_match(self, replay, pairings=None):
		""" Given a replay object and a list of pairing sets, return boolean
		corresponding to the existence of the replay's player set in the pairing
		list.
		"""
		pairing = frozenset(format_name(self.get_closest(p)) for p in replay.players)
		if pairing in pairings:
			self.pairingReplayMap[pairing] = (replay, "fuzzy")
			pairings.remove(pairing)
			return True
		return False
	
	def partial_match(self, replay, pairings=None):
		""" Given a replay object and a list of pairing sets, return boolean
		corresponding to the existence of at least one player in the replay's
		player set in at least one pairing in the pairing set.
		"""
		for player in replay.players:
			for pairing in pairings:
				if self.get_closest(format_name(player)) in pairing:
					self.pairingReplayMap[pairing] = (replay, "partial")
					pairings.remove(pairing)
					return True
		return False
		
	def get_closest(self, player):
		""" Uses fuzzy string matching to find the closest match as dictated by
		Levenshtein (edit) distance. Returns original name if no suitable match
		is found.
		"""
		# Check if player exists in players
		if player in self.players:
			return player
		# Check if player exists in dict
		if player in self.fuzzyNameMatches:
			return self.fuzzyNameMatches[player]
		# Fuzzy string matching
		newplayer = next((p for p in self.players 
						  if fuzz.partial_ratio(p,player) > 80), player)
		self.fuzzyNameMatches[player] = newplayer
		return newplayer
	
	def match_tournament(self):
		""" Run all filters on set of replays and attempt to match each pairing 
		to a replay. Return set of all replays that match. 
		"""
		exact = self.filter_replays_by_pairings("exact")
		fuzzy = self.filter_replays_by_pairings("fuzzy")
		partial = self.filter_replays_by_pairings("partial")
		r = exact | fuzzy | partial
		return r
		
	# Might belong in replay_compile class
	def filter_replays_by_number(self, *numbers):
		""" Remove replays from list by number. """
		self.replays = self.unmatchedReplays = {replay for replay
		in self.replays if replay.number not in numbers}
		
	def add_replays_by_number(self, *numbers):
		self.replays | {replay for replay in self.unmatchedReplays 
						if replay.number in numbers}
		
def parse_pairings(fileString=None, url=None, pairingsRaw=None):
	""" Given a thread URL from which pairings are to be extracted or a text
	file of pairings, parse line-by-line for match-ups. Return list of
	pairings with order retained.
		
	Tournaments are generally created with the same bracketmaker, which uses
	' vs. ' as a separator. Current implementation accounts for minor
	discrepancies, such as omission of the period and immediately adjacenct HTML
	formatting tags.
		
	"""
	# Pairings from text file
	if fileString:
		raw = open(fileString, "r").read().lower().splitlines()
	# Pairings from thread url
	if url:
		# Pairings are contained in first post of a thread
		# Posts are framed by <article> tags
		raw = (urlopen(url).read().decode().lower().split("</article>",1)[0]
			#.split("<article>")[1]
			.split("\n"))
		
	# Checks for "vs" with no adjacent alphanumeric characters
	pairingsRaw = (line for line in raw if
				   re.compile(r'.*\Wvs\W.*').match(line))
	pairings = [frozenset(re.sub("&#.*;", "", name.strip()) for name in 
				re.compile(r'\Wvs\W').split(
				re.sub(r'<.{0,4}>',"",pairing)
				.strip("\n").lower()
				)) for pairing in pairingsRaw]
	return pairings



def parse_winners(url):
	post = (urlopen(url).read().decode().split("</article>")[0]
			.split("<article>")[1].split("\n"))
	raw = (line.split("<br />")[0] for line in post 
			if re.compile(r'.*\Wvs\W.*').match(line))
	winners = []
	pairing_dict = {}
	for line in raw:
		#print(line)
		line = re.sub(r'\(.+?\)', "", line)
		line = re.sub(r'<a.+?">', "", line)
		line = re.sub(r'<span.+?">', "", line)
		line = line.replace("</a>", "")
		line = line.replace("</span>", "")
		#print(line)
		pairing = frozenset([player.strip() for player in re.compile(r'vs\W').split(line)])
		#print(pairing)
		#winner = " vs. ".join(pairing)
		pairing_dict[pairing] = ""
		for player in pairing:
			#print(player)
			if player.startswith("<b>") or player.endswith("</b>"):
				winner = player
				pairing_dict[pairing] = re.sub(r'<.{0,4}>',"",winner).strip()
				#winners.append(re.sub(r'<.{0,4}>',"",winner).strip())
	return pairing_dict


def participants_from_pairings(pairings):
	""" Given pairings, return a set comprised of each unique player. """
	# Option to break after Round 1
	# Pros: Negligibly faster, avoids typos made in further rounds
	# Cons: Will mess up if "bye" is used for multiple r1 match-ups
	return set(chain.from_iterable(pairing for pairing in pairings))
	
	
def format_name(name):
	""" Given a username, format to eliminate special characters. 
	
	Supported characters: Letters, numbers, spaces, period, apostrophe. 
	"""
	# User dictionary
	# Move to other class?
	return re.sub("[^\w\s'\.-]+", "", name).lower().strip()