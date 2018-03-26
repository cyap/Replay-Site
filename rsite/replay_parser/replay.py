import re
from collections import namedtuple, defaultdict, OrderedDict
from itertools import combinations, islice
import profile

FORMS = {"Genesect","Keldeo","Gastrodon","Magearna","Silvally","Groudon",
		 "Kyogre", "Mimikyu"}
COUNTED_FORMS = {"Arceus-*", "Pumpkaboo-*", "Gourgeist-*", "Rotom-Appliance"}

class Log:
	def __init__(self, text, url=None):
		self.text = text
		self.url = url
	
	def parse_players(self):
		""" Return dict with formatted player names. """
		lines = (line for line in self.text if line.startswith("|player") 
			and len(line.split("|")) > 3)
		players = OrderedDict()
		for line in lines:
			ll = line.split("|")
			# Player -> Number
			players[ll[3].upper()] = ll[2]
		return players
	
	def parse_winner(self):
		""" Parse replay for winner, declared at the bottom of replay. """
		try:
			return (next(line for line in reversed(self.text) 
					if line.startswith("|win"))
					.split("|")[2].split("<")[0]).upper().strip()
		except:
			return ""
		'''
		return (next(line for line in reversed(self.text) 
					if line.startswith("|win"))
					.split("|")[2].split("<")[0]).lower()
		'''	
		
	def parse_generation(self):
		""" Return int representing generation. """
		try:
			return int(next(line.split("|")[2]
					for line in self.text 
					if line.startswith("|gen")))
		except:
			try:
				tier_line = next(line for line in self.text 
					if line.startswith("|tier"))
				return int(next(char for char in tier_line if char.isdigit()))
			except:
				return 0
					
	def parse_tier(self):
		return next(line.split("|")[2].lower() for line in self.text 
					if line.startswith("|tier"))
	
	def parse_teams_from_preview(self):
		""" Return dict containing p1 and p2's teams.
		
		Only works for gen 5+, where teams are stated at the beginning of
		replays. 
		"""
		teams = {"p1":[],"p2":[]}
		
		teams["p1"] = list(islice(
					  (format_pokemon(line.split("|")[3].split(",")[0]) 
					  for line in self.text if line.startswith("|poke|p1")),6))
		teams["p2"] = list(islice(
					  (format_pokemon(line.split("|")[3].split(",")[0]) 
					  for line in self.text if line.startswith("|poke|p2")),6))
					  
		# Check for additional forms unrevealed at team preview
		for poke in COUNTED_FORMS:
			base = poke.split("-")[0]
			for player in ("p1", "p2"):
				if poke in teams[player]:
					exp = "\|(switch|drag)\|{0}.*\|{1}.*".format(player, base)
					try:
						switch = next(line for line in self.text 
							if re.match(exp, line))
						teams[player].append(switch.split("|")[3].split(",")[0])
					except:
						pass
		return teams
		
	def parse_from_scan(self, *terms):
		
		def update_state():
			player = ll[2].split(":")[0]
			poke = format_pokemon(ll[3].split(",")[0])
			state[player] = poke
	
		def move_from_line(SKIP_MOVES = {"Copycat", "Metronome", "Magic Coat"}):
			# Filter moves called by Copycat, Metronome, etc.
			if ll[-1][6:] in SKIP_MOVES:
				return
			# Transform, Magic Coat
			# Mimic, Sketch
			# TODO: Optimize Struggle filter
			move = ll[3]
			if move == "Struggle":
				return
			# p[12][abc]
			player = ll[2].split(":")[0]
			# Accounting for replays that predate position
			if player[-1].isdigit():
				player += "a"
			moves = dicts["moves"][player[:-1]][state[player]]
			if moves not in moves:
				moves.append(move)
			dicts["moves"][player[:-1]][state[player]].append(move)
			
			
		# Terms: teams, moves, items, abilities
		dicts = {term:{"p1":defaultdict(list), "p2":defaultdict(list)} 
				for term in terms}
		
		methods = {
			"state":update_state,
			"moves":move_from_line,
			#"abilities":ability_from_line,
			#"items":items_from_line,	
		}
		
		match_func = {
			"move":{"moves"},
			"switch":{"state"},
			"drag":{"state"}
		}
		
		state = {"p1a":None, "p2a":None, "p1b":None, "p2b":None}
		flags = []
		
		# Filter unspecified terms
		for value in match_func.values():
			value &= (set(terms) | {"state"})
		
		for line in self.text:
			ll = line.split("|")
			prefix = ll[1]
			
			# Call matching function for each term
			for term in match_func.get(prefix, []):
				methods[term]()

		return dicts
				
	def parse_teams_from_scan(self, limit=6, teams=None):
		if not teams:
			teams = {"p1":[], "p2":[]}
		for line in self.text:
			if line.startswith("|switch") or line.startswith("|drag"):
				ll = line.split("|")
				player = ll[2].split("a:")[0]
				poke = format_pokemon(ll[3].split(",")[0])
				team = teams[player]
				if poke not in team:
					team.append(poke)
			if len(teams["p1"]) == limit and len(teams["p2"]) == limit:
				break
		return teams
	
	def parse_leads(self, doubles=False):
		
		# Singles
		if not doubles:
			l = (line for line in self.text if line.startswith("|switch"))
			leads = {"p1":[],"p2":[]}
			try:
				leads["p1"] = [format_pokemon(next(l).split("|")[3].split(",")[0])]
				leads["p2"] = [format_pokemon(next(l).split("|")[3].split(",")[0])]
			except:
				pass
		
		# Doubles
		else:
			leads = {"p1":[],"p2":[]}
			for line in self.text:
				if line.startswith("|switch"):
					try:
						ll = line.split("|")
						leads["|"+ll[2][:2]].append(ll[3].split(",")[0])
					except:
						pass
				elif line.startswith("|turn"):
					break
		return leads
		
	def parse_items(self, teams):
		items = {"p1":{pokemon: "Other" for pokemon in teams["p1"]},
				 "p2":{pokemon: "Other" for pokemon in teams["p2"]}}
		return None
		"""
		Cases:
		- Activation (end of turn)
		- Activation (triggered)
		- Knock Off
		- Trick
		- Thief
		- Frisk
		- Doubles stuff
		- Z-move
		- Mega evolution
		- Input item and Pokemon

		"""
			
	
	def parse_moves(self, teams):
		moves = {"p1":{pokemon: [] for pokemon in teams["p1"]},
				 "p2":{pokemon: [] for pokemon in teams["p2"]}}
		nicknames = {"p1":{},"p2":{}}
		
		for line in self.text:
			if line[1:5] == "move":
				try:
					ll = line.split("|")
					p = ll[2]
					# Glitch in replay formatting
					if re.match("p[12]{1}:", p):
						p = p.replace(":","a:")
						print(p)
					player = re.split("[ab]:",p)[0]
					pokemon = nicknames[player][p] 
					move = ll[3]
					moveset = moves[player][pokemon]
				
					# TODO: Filter non-initial moves
					# Struggle - filter out afterwards
					# Transform / Copycat
					# Z-moves
					if move not in moveset:
						moveset.append(move)
				except:
					pass

			elif line[1:7] == "switch" or line[1:5] == "drag":
				try:
					ll = line.split("|")
					player = re.split("[ab]:",ll[2])[0]
					nickname = ll[2]
					pokemon = format_pokemon(ll[3].split(",")[0])
					if nickname not in nicknames[player]:
						nicknames[player][nickname] = pokemon 
						moves[player][nicknames[player][nickname]] = []
				except:
					pass
		
		return moves

	def parse_turn_count(self):
		""" Find last line marking a turn. Number corresponds to turn count. """
		return int(next(line for line in reversed(self.text) 
						if line.startswith("|turn"))
						.split("|")[2])
	
	def parse_gametype(self):
		return (next(line for line in self.text if line.startswith("|gametype"))
				.split("|")[2])
	
	def move_in_replay(self, move):
		""" Return boolean indicating if move was used in match. """
		m = re.compile("\|move\|.*\|{0}\|.*".format(move))
		return next((True for line in self.text 
					 if m.match(line)), False)
					 
class Replay:

	def __init__(self, log, players, winner, url=None, number=None, tier=None):
		self.log = log
		
		# Initialize player based on parse
		# Set teams based on parse 
		
		
		self._players = players
		self._winner = winner
		
		# Optional args
		self.url = url
		self.number = number
		self.tier = tier or self.log.parse_tier()

		# Refactor to properties
		#self.leads = None

	def __repr__(self):
		return self.players.__str__()
	
	@property
	def players(self):
		""" Handles ordered dict mapping each player's name to its number (p1 
		or p2). Additional names, which result from replacement players joining
		a battle in the instance of a disconnection, are stored privately but
		not displayed on access call.

		Returns list containing player names, in order of number 
		([player1, player2]).
		"""
		try:
			return list(self._players.keys())[0:2]
		except:
			self._players = self.log.parse_players()
			return list(self._players.keys())[0:2]
	
	def name_to_num(self, player):
		return self._players[player]
		
	@property
	def winner(self):
		return self._winner
	
	@winner.setter
	def winner(self, new_winner):
		if new_winner:
			try:
				self.loser = self.players[self.players.index(new_winner)-1]
				self._winner = new_winner
			except:
				# TODO: raise error if winner not in player list
				pass
		else:
			self._winner = ""
			self.loser = ""
				
	@property
	def generation(self):
		""" Return int/string representing generation. """
		try:
			return self._generation
		except:
			self._generation = self.log.parse_generation()
			return self._generation
			
	@property
	def teams(self):
		try:
			return self._teams
		except:
			# Generations 1-4: No team preview; must parse entire log for teams
			#if re.compile(".*gen.*[1-4].*").match(self.tier):
			if self.generation < 5:
				teams = self.log.parse_teams_from_scan()
			# Generation 5+: Team preview
			else:
				teams = self.log.parse_teams_from_preview()
			self._teams = teams
			# Gen 4 Rotom
			if self.generation == 4:
				for team in self._teams.values():
					for pokemon in team:
						if pokemon.startswith("Rotom-"):
							team.append("Rotom-Appliance")
							break
			# Win/Loss/Tie -> teams
			# TODO: Is this necessary?
			#for player in ("p1","p2"):
			#	self._teams[self.playerwl[player]] = self._teams[player]
			
			# Name -> teams
			#for name in list(self._players.keys()):
				#self._teams[name] = self._teams[self._players[name]]
			return self._teams
			
			
			# Team by name
			# pre-set: 2 (creation) + 1 (access)
			# not pre set: self.teams[name_to_num(name)]
	
	def add_to_team(self, team, pokemon):
		if not self._teams["win"]:
			self.teams_from_parse()
		self._teams[team].append(pokemon)
	
	@property
	def leads(self):
		try:
			return self._leads
		except:
			self._leads = self.log.parse_leads(self.gametype == "doubles")
			for name in list(self._players.keys()):
				self._leads[name] = self._leads[self._players[name]]
			return self._leads
			
	@property
	def moves(self):
		try:
			return self._moves
		except:
			self._moves = self.log.parse_moves(self.teams)
			#self._moves = self.log.parse_from_scan("moves")["moves"]
			for name in self._players:
				self._moves[name] = self._moves[self._players[name]]
			
			#for player in ("p1","p2"):
				#self._moves[self.playerwl[player]] = self._moves[player]
			#self._moves[self._loser] = self._moves.get("lose", [])
			#self._moves[self._winner] = self._moves.get("win", [])
			return self._moves
					
	# Refactor in other classes
	def combos(self, n):
		""" Returns all possible combinations of n Pokemon for both teams. """
		return {key:
				map(lambda x: frozenset(x), 
					list(combinations(self.teams[key], n)))
				for key in self.teams.keys()}
		
				
	@property
	def turn_count(self):
		""" Find last line marking a turn. Number corresponds to turn count. """
		try:
			return self._turncount
		except:
			self._turncount = self.log.parse_turncount()
			return self._turncount
	
	@property
	def gametype(self):
		try:
			return self._gametype
		except:
			self._gametype = self.log.parse_gametype()
			return self._gametype

	def pokemon_in_replay(self, pokemon):	
		""" Return boolean indicating if Pokemon existed in match. """
		# TODO: Non-tp gens
		# Check teams
		return pokemon in team["p1"] or pokemon in team["p2"]
	
	def move_in_replay(self, move):
		""" Return boolean indicating if move was used in match. """
		return self.log.move_in_replay(move)
		
					 
def format_pokemon(pokemon):
	split_form = pokemon.split("-", 1)
	base_form = split_form[0]
	if base_form in FORMS or split_form[-1].startswith("Mega"):
		return base_form
	return pokemon

def format_name(name):
	""" Given a username, eliminate special characters and escaped unicode.
	
	Supported characters: Letters, numbers, spaces, period, apostrophe. 
	"""
	return re.sub("[^\w\s'\.-]+", "", re.sub("&#.*;", "", name)).upper().strip()
	