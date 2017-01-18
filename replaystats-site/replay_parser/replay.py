import re
from collections import defaultdict
from itertools import combinations
from urllib2 import urlopen, Request
import profile

# User-agent wrapper to mimic browser requests
REQUEST_HEADER = {"User-Agent" : 
"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML,"
"like Gecko) Chrome/54.0.2840.98 Safari/537.36"}

FORMS = {"Genesect","Keldeo","Gastrodon","Magearna","Silvally","Groudon",
		 "Kyogre"}
COUNTED_FORMS = {"Arceus-*", "Pumpkaboo-*"}

class replay:

	def __init__(self, url):
		self.url = url
		self.number = int(url.split("-")[-1])
		self.tier = url.split("-")[-2]
		self.replay_content = [line for line in
			urlopen(Request(url, headers=REQUEST_HEADER))
			.read()
			.split("\n")
			if line.startswith("|")]
		
		
		# Iterate through text vs line by line
		# Get players
		
		#self._players = None
		self.players = self.get_players() # p1 -> name
		self.winner = self.winner() # win -> name
		winIndex = self.players.index(self.winner)
		self.loser = self.players[winIndex-1]
		self.playerwl = {"win":self.winner,
						 "lose":self.loser} # win -> name
		self.wl = {"p"+str(winIndex + 1):"win",
				   "p"+str((winIndex + 1) % 2 + 1):"lose"} #p1 -> win
		self._teams = {"win":[], "lose":[]} # win -> teams
		
		
		self.wl = {"p"+str(winIndex + 1):"win",
				   "p"+str((winIndex + 1) % 2 + 1):"lose"} #win -> p1'''
		
		# Info:
		# win -> name
		# p1 -> name
		# p2 -> name
		# p1 -> team
		
		
		# p1 -> win -> team or
		# win -> p1 -> team
		
		# Need:
		# win -> team / lose -> team
		# win -> name
		# 
		
		
		# win -> p1 or p2 -> name
		# lose -> p1 or p2 -> name
		
		# Teams: {p1 / p2}		
		self.leads = None
		self.moves = None
		
	def __repr__(self):
		return self.players.__str__()
	
	#@property
	def get_players(self):
		""" Return dict with formatted player names. """
		players = (line for line in self.replay_content if
				   line.startswith("|player"))
		p1 = next(players).split("|")[3]
		p2 = next(players).split("|")[3]
		#self.players = (p1, p2)
		return (p1,p2)
		#return {"p1":p1, "p2":p2}
		
	def generation(self):
		""" Return int/string representing generation. """
		# Handle output
		return next(line.split("|")[2]
					for line in self.replay_content 
					if line.startswith("|gen"))
	@property
	def teams(self):
		if self._teams["win"] and self._teams["lose"]:
			return self._teams
		# Generations 1-4: No team preview; must manually parse teams from log
		if re.compile(".*gen[1-4].*").match(self.tier):
			return self.teams_from_parse()
		# Generation 5+: Team preview
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
		for line in self.replay_content:
			if line.startswith("|poke"):
				ll = line.split("|")
				player = ll[2]
				poke = format_pokemon(ll[3].split(",")[0])
				self._teams[self.wl[player]].append(poke)
			# |teampreview denotes the conclusion of both teams
			if line.startswith("|teampreview"):
				# Parse entire log to find specific forms for certain Pokemon
				
				# Change
				# return self.teams_from_parse(len([poke for poke in COUNTED_FORMS,etc)
				#if (poke for poke 
				try: 
					next(poke for poke
					in self._teams["win"] + self._teams["lose"]
					if poke in COUNTED_FORMS)
					return self.teams_from_parse(7)
				except:
					return self._teams
				
	def teams_from_parse(self, limit=6):
		for line in self.replay_content:
			if line.startswith("|switch") or line.startswith("|drag"):
				ll = line.split("|")
				player = ll[2].split("a:")[0]
				poke = format_pokemon(ll[3].split(",")[0])
				team = self._teams[self.wl[player]]
				if poke not in team:
					team.append(poke)
			if len(self._teams["win"]) == limit and len(self._teams["lose"]) == limit:
				break
		return self._teams
	
	def get_leads(self):
		if self.leads:
			return self.leads
		leads = {"win":None,"lose":None}
		for line in self.replay_content:
			if leads["win"] and leads["lose"]:
				self.leads = leads
				return leads
			if line.startswith("|switch"):
				ll = line.split("|")
				player = ll[2].split("a:")[0]
				poke = format_pokemon(ll[3].split(",")[0])
				leads[self.wl[player]] = poke
	
	def get_moves(self):
		if self.moves:
			return self.moves
		#moves = {"win":defaultdict(list),"lose":defaultdict(list)}
		moves = {"win":{pokemon: [] for pokemon in self.teams["win"]},
				 "lose":{pokemon: [] for pokemon in self.teams["lose"]}}
		nicknames = {"p1":{},"p2":{}}
		for line in self.replay_content:
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
			if line.startswith("|switch") or line.startswith("|drag"):
				ll= line.split("|") 
				player = ll[2].split("a:")[0]
				nickname = ll[2]
				pokemon = format_pokemon(ll[3].split(",")[0])
				if nickname not in nicknames[player]:
					nicknames[player][nickname] = pokemon 
					moves[self.wl[player]][nicknames[player][nickname]] = []
		self.moves = moves
		return moves
					
	# Refactor in other classes
	def combos(self, n, teams = None):
		""" Returns all possible combinations of n Pokemon for both teams. """
		if not teams:
			teams = self.teams
		return {"win":list(combinations(teams["win"], n)),
				"lose":list(combinations(teams["lose"], n))}

	def winner(self):
		""" Parse replay for winner, declared at the bottom of replay. """
		return (next(line for line in reversed(self.replay_content) 
								if line.startswith("|win"))
								.split("|")[2].split("<")[0])

	def turn_count(self):
		""" Find last line marking a turn. Number corresponds to turn count. """
		return int(next(line for line in reversed(self.replay_content) 
						if line.startswith("|turn"))
						.split("|")[2])

	def pokemon_in_replay(self, pokemon):	
		""" Return boolean indicating if Pokemon existed in match. """
		# TODO: Non-tp gens
		# Check teams
		for line in self.replay_content:
			if line.startswith("|poke") and pokemon in line:
				return True
			if line.startswith("|rule"):
				return False
	
	def move_in_replay(self, move):
		""" Return boolean indicating if move was used in match. """
		m = re.compile("\|move\|.*\|{0}\|.*".format(move))
		return next((True for line in self.replay_content 
					 if m.match(line)), False)

def format_pokemon(pokemon):
	base_form = pokemon.split("-")[0]
	if base_form in FORMS or pokemon.endswith("-Mega"):
		return base_form
	return pokemon

def format_name(name):
	""" Given a username, eliminate special characters and escaped unicode.
	
	Supported characters: Letters, numbers, spaces, period, apostrophe. 
	"""
	return re.sub("[^\w\s'\.-]+", "", re.sub("&#.*;", "", name)).lower().strip()

def main(l):
	for r in l:
		a = r.teams_from_preview()
		b = r.get_moves()

if __name__ == "__main__":
	l = [replay("http://replay.pokemonshowdown.com/smogtours-ou-39893") for i in xrange(0,100)]
	profile.run('main(l)')
	