import re
from collections import namedtuple, defaultdict, OrderedDict
from itertools import combinations, islice
import profile

FORMS = {"Genesect","Keldeo","Gastrodon","Magearna","Silvally","Groudon",
		 "Kyogre"}
COUNTED_FORMS = {"Arceus-*", "Pumpkaboo-*", "Gourgeist-*", "Rotom-Appliance"}

class Log:
	def __init__(self, text):
		self.text = text
		'''
		# Line dict
		self.line_dict = {}
		for line in self.text:
			prefix = line.split("|")[1]
			try:
				line_dict[prefix].append(line)
			except:
				line_dict[prefix] = [line]'''
	
	def parse_players(self):
		""" Return dict with formatted player names. """
		player_lines = (line for line in self.text if
				   line.startswith("|player") and len(line.split("|")) > 3)
		# Handle name formatting
		#p1 = format_name(next(players).split("|")[3])
		#p2 = format_name(next(players).split("|")[3])
		
		players = OrderedDict()
		for line in player_lines:
			ll = line.split("|")
			# Player -> Number
			players[ll[3].lower()] = ll[2]
		return players
		
		#Players = namedtuple('Players', 'p1 p2')
		#return Players(p1, p2)
		#return (p1, p2)
	
	def parse_winner(self):
		""" Parse replay for winner, declared at the bottom of replay. """
		return (next(line for line in reversed(self.text) 
									if line.startswith("|win"))
									.split("|")[2].split("<")[0]).lower()
		
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

		
		'''
		limit = len([poke for poke in teams["p1"] + teams["p2"] 
				if poke in COUNTED_FORMS])
		if limit > 0:
			return self.parse_teams_from_scan(6 + limit, teams)
		'''
		
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
			leads = {"p1":None,"p2":None}
			try:
				leads["p1"] = next(l).split("|")[3].split(",")[0]
				leads["p2"] = next(l).split("|")[3].split(",")[0]
			except:
				pass
		
		# Doubles
		else:
			leads = {"p1":[],"p2":[]}
			for line in self.text:
				if line.startswith("|switch"):
					try:
						ll = line.split("|")
						leads[ll[2][:2]].append(ll[3].split(",")[0])
					except:
						pass
				elif line.startswith("|turn"):
					break
		return leads
	
	def parse_moves(self, teams):
		moves = {"p1":{pokemon: [] for pokemon in teams["p1"]},
				 "p2":{pokemon: [] for pokemon in teams["p2"]}}
		nicknames = {"p1":{},"p2":{}}
		
		for line in self.text:
			if line[1:5] == "move":
				ll = line.split("|")
				p = ll[2]
				# Glitch in replay formatting
				if re.match("p[12]{1}:", p):
					p = p.replace(":","a:")
				player = re.split("[ab]:",p)[0]
				pokemon = nicknames[player][p]
				move = ll[3]
				moveset = moves[player][pokemon]
				#moveset.add(move)
				if move not in moveset:
					moveset.append(move)
			elif line[1:7] == "switch" or line[1:5] == "drag":
				ll = line.split("|")
				player = re.split("[ab]:",ll[2])[0]
				nickname = ll[2]
				pokemon = format_pokemon(ll[3].split(",")[0])
				if nickname not in nicknames[player]:
					nicknames[player][nickname] = pokemon 
					moves[player][nicknames[player][nickname]] = []
		
		'''
		line_dict = {}
		for line in self.text:
			prefix = line.split("|")[1]
			try:
				line_dict[prefix].append(line)
			except:
				line_dict[prefix] = [line]
		'''
		
		'''
		line_dict = self.line_dict
		
		for line in line_dict.get("switch",[]) + line_dict.get("drag",[]):
			ll = line.split("|")
			player = re.split("[ab]:",ll[2])[0]
			nickname = ll[2]
			pokemon = format_pokemon(ll[3].split(",")[0])
			if nickname not in nicknames[player]:
				nicknames[player][nickname] = pokemon 
				moves[player][nicknames[player][nickname]] = []
		
		for line in line_dict["move"]:
			ll = line.split("|")
			p = ll[2]
			# Glitch in replay formatting
			if re.match("p[12]{1}:", p):
				p = p.replace(":","a:")
			player = re.split("[ab]:",p)[0]
			pokemon = nicknames[player][p]
			move = ll[3]
			moveset = moves[player][pokemon]
			if move not in moveset:
				moveset.append(move)
		'''	
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
		""" Return ordered pair (p1, p2) with players' names. Additional names,
		which result from replacement players joining a battle in the instance
		of a disconnection, are stored in a private variable rather than
		displayed on access. 
		"""
		try:
			# Player 1, Player 2
			return list(self._players.keys())[0:2]
		except:
			self._players = self.log.parse_players()
			return list(self._players.keys())[0:2]
		
	@property
	def playerwl(self):	
		""" Parse replay for winner, declared at the bottom of replay. """
		try:
			return self._playerwl
		except:
			# p1 -> name
			win_player = self._players[self._winner]
			lose_num = 1 ^ 2 ^ int(win_player[-1])
			lose_player = "p" + str(lose_num)
			self._loser = self.players[lose_num-1]
			'''
			try:
				win_index = self.players.index(self._winner)
				self._loser = self.players[win_index-1]
				win_num = "p"+str(win_index + 1)
				lose_num = "p"+str((win_index + 1) % 2 + 1)
			except:
				win_num = next(line.split("|")[2] for line 
					in reversed(self.log.text) if line.startswith("|player"))
				lose_num = "p2" if win_num == "p1" else "p1"
				self._loser = self._players[int(lose_num[1])-1]'''
			return {"win":self._winner, 
					"lose":self._loser,
					win_player:"win", 
					lose_player:"lose"}
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
			for player in ("p1","p2"):
				self._teams[self.playerwl[player]] = self._teams[player]
			
			self._teams[self._loser] = self._teams["lose"]
			self._teams[self._winner] = self._teams["win"]
			
			return self._teams
	
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
			for player in ("p1","p2"):
				self._leads[self.playerwl[player]] = self._leads[player]
			self._leads[self._loser] = self._leads["lose"]
			self._leads[self._winner] = self._leads["win"]
			return self._leads
			
	@property
	def moves(self):
		try:
			return self._moves
		except:
			self._moves = self.log.parse_moves(self.teams)
			for player in ("p1","p2"):
				self._moves[self.playerwl[player]] = self._moves[player]
			self._moves[self._loser] = self._moves["lose"]
			self._moves[self._winner] = self._moves["win"]
			return self._moves
					
	# Refactor in other classes
	def combos(self, n):
		""" Returns all possible combinations of n Pokemon for both teams. """
		return {"win":list(combinations(self.teams["win"], n)),
				"lose":list(combinations(self.teams["lose"], n))}
				
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
		#a = r.teams_from_preview()
		b = r.moves

if __name__ == "__main__":
	import replay_compile
	l = [replay_compile.open_replay("http://replay.pokemonshowdown.com/smogtours-ou-39893") for i in range(0,500)]
	profile.run('main(l)', sort="tottime")
	