import re
from collections import defaultdict
from itertools import combinations, takewhile
from urllib2 import urlopen, Request
import profile

from fuzzywuzzy import process

class replay:

	# User-agent wrapper to mimic browser requests
	REQUEST_HEADER = {"User-Agent" : 
	"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML,"
	"like Gecko) Chrome/54.0.2840.98 Safari/537.36"}

	def __init__(self, url):
		self.url = url
		self.number = int(url.split("-")[-1])
		self.tier = url.split("-")[-2]
		self.replayContent = [line for line in
			urlopen(Request(url, headers=replay.REQUEST_HEADER))
			.read()
			.split("\n")
			if line.startswith("|")]
		self.players = self.players() # (Eo, Finchinator) (p1, p2)
		
		# Iterate through text vs line by line
		# Get players
		
		winIndex = self.players.index(self.winner())
		self.wl = {"p"+str(winIndex + 1):"win",
				   "p"+str((winIndex + 1) % 2 + 1):"lose"}
		self._teams = None
		self.leads = None
		self.moves = None
		
	def __repr__(self):
		return self.players.__str__()
	
	def players(self):
		""" Return tuple with formatted player names. """
		
		players = (line for line in self.replayContent if
				   line.startswith("|player"))
		p1 = format_name(next(players).split("|")[3])
		p2 = format_name(next(players).split("|")[3])
		return (p1, p2)
		
	def get_players(self):
		return self.players
		
	def generation(self):
		""" Return int/string representing generation. """
		# Handle output
		return next(line.split("|")[2]
					for line in self.replayContent 
					if line.startswith("|gen"))
	@property
	def teams(self):
		if self._teams:
			return self._teams
		if re.compile(".*gen[1-4].*").match(self.tier):
			return self.teams_from_parse()
		return self.teams_from_preview()
	
	def add_to_team(self, team, pokemon):
		if not self._teams:
			self.teams_from_parse()
		self._teams[team].append(pokemon)
	
	def teams_from_preview(self):
		""" Return dict containing p1 and p2's teams.
		
		Only works for gen 5+, where teams are stated at the beginning of
		replays. 
		"""
		teams = {"win":[], "lose":[]}		
		for line in self.replayContent:
			if line.startswith("|poke"):
			#if line[:5] == "|poke":
				ll = line.split("|")
				player = ll[2]
				poke = ll[3].split(",")[0]
				if poke.startswith("Keldeo"):
					poke = "Keldeo"
				if poke.startswith("Gastrodon"):
					poke = "Gastrodon"
				if poke.startswith("Genesect"):
					poke = "Genesect"
				teams[self.wl[player]].append(poke)
			if line.startswith("|teampreview"):
			#elif line[:12] == "|teampreview":
				self._teams = teams
				return teams
				
	def teams_from_parse(self):
		#|drag|p1a: Zapdos|Zapdos|278\/383
		#|switch|p1a: Isa|Flygon, F|301\/301
		teams = {"win":[], "lose":[]}
		for line in self.replayContent:
			if line.startswith("|switch") or line.startswith("|drag"):
				ll = line.split("|")
				player = ll[2].split("a:")[0]
				poke = ll[3].split(",")[0]
				team = teams[self.wl[player]]
				if poke not in team:
					team.append(poke)
			if len(teams["win"]) == 6 and len(teams["lose"]) == 6:
				break
		self.teams = teams
		return teams
	
	def get_leads(self):
		if self.leads:
			return self.leads
		leads = {"win":None,"lose":None}
		for line in self.replayContent:
			if leads["win"] and leads["lose"]:
				self.leads = leads
				return leads
			if line.startswith("|switch"):
				ll = line.split("|")
				player = ll[2].split("a:")[0]
				poke = ll[3].split(",")[0]
				leads[self.wl[player]] = poke
	
	def get_moves(self):
		if self.moves:
			return self.moves
		moves = {"win":defaultdict(list),"lose":defaultdict(list)}
		nicknames = {"p1":{},"p2":{}}
		for line in self.replayContent:
			if line.startswith("|move"):
				ll = line.split("|")
				p = ll[2]
				# Glitch in replay formatting
				if re.match("p[12]{1}:", p):
					p = p.replace(":","a:")
				player = p.split("a:")[0]
				pokemon = nicknames[player][p]
				move = ll[3]
				moveset = moves[self.wl[player]][pokemon]
				if move not in moveset:
					moveset.append(move)
				# defaultdicts
			if line.startswith("|switch") or line.startswith("|drag"):
				ll= line.split("|") 
				player = ll[2].split("a:")[0]
				nickname = ll[2]
				pokemon = ll[3].split(",")[0]
				if nickname not in nicknames[player]:
					nicknames[player][nickname] = pokemon 
					moves[self.wl[player]][nicknames[player][nickname]] = []
		self.moves = moves
		return moves
					
	# Refactor in other classes
	def combos(self, n, teams = None):
		""" Returns all possible combinations of n Pokemon for both teams. """
		if not teams:
			teams = self.teams_from_preview()
		return {"win":list(combinations(teams["win"], n)),
				"lose":list(combinations(teams["lose"], n))}
	
	def winner(self):
		""" Parse replay for winner, declared at the bottom of replay. """
		return format_name(next(line for line in reversed(self.replayContent) 
								#if line.startswith("|win"))
								if line[:4] == "|win")
								.split("|")[2].split("<")[0])

	def turn_count(self):
		""" Find last line marking a turn. Number corresponds to turn count. """
		return int(next(line for line in reversed(self.replayContent) 
						if line.startswith("|turn"))
						.split("|")[2])

	def pokemon_in_replay(self, pokemon):	
		""" Return boolean indicating if Pokemon existed in match. """
		# TODO: Non-tp gens
		# Check teams
		for line in self.replayContent:
			if line.startswith("|poke") and pokemon in line:
				return True
			if line.startswith("|rule"):
				return False
	
	def move_in_replay(self, move):
		""" Return boolean indicating if move was used in match. """
		m = re.compile("\|move\|.*\|{0}\|.*".format(move))
		return next((True for line in self.replayContent 
					 if m.match(line)), False)

def format_name(name):
	""" Given a username, format to eliminate special characters. 
	
	Supported characters: Letters, numbers, spaces, period, apostrophe. 
	"""
	# User dictionary
	# Move to other class?
	return re.sub("[^\w\s'\.-]+", "", name).lower().strip()

def main(l):
	for r in l:
		a = r.teams_from_preview()

if __name__ == "__main__":
	l = [replay("http://replay.pokemonshowdown.com/smogtours-ou-39893") for i in xrange(0,100)]
	profile.run('main(l)')
	