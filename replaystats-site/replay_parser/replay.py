import re
from collections import namedtuple, defaultdict
from itertools import combinations, islice
import profile

FORMS = {"Genesect","Keldeo","Gastrodon","Magearna","Silvally","Groudon",
		 "Kyogre"}
COUNTED_FORMS = {"Arceus-*", "Pumpkaboo-*", "Rotom-Appliance"}

class Log:
	def __init__(self, text):
		self.text = text
	
	def parse_players(self):
		""" Return dict with formatted player names. """
		players = (line for line in self.text if
				   line.startswith("|player"))
		p1 = next(players).split("|")[3].lower()
		p2 = next(players).split("|")[3].lower()
		Players = namedtuple('Players', 'p1 p2')
		return Players(p1, p2)
	
	def parse_winner(self):
		""" Parse replay for winner, declared at the bottom of replay. """
		return (next(line for line in reversed(self.text) 
									if line.startswith("|win"))
									.split("|")[2].split("<")[0]).lower()
		
	def parse_generation(self):
		""" Return int/string representing generation. """
		# Handle output
		return next(line.split("|")[2]
					for line in self.text 
					if line.startswith("|gen"))
	
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
		limit = len([poke for poke in teams["p1"] + teams["p2"] 
				if poke in COUNTED_FORMS])
		if limit > 0:
			return self.parse_teams_from_scan(6 + limit, teams)
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
	
	def parse_leads(self):
		leads = {"p1":None,"p2":None}
		'''
		for line in self.text:
			if leads["win"] and leads["lose"]:
				return leads
			if line.startswith("|switch"):
				ll = line.split("|")
				player = ll[2].split("a:")[0]
				poke = format_pokemon(ll[3].split(",")[0])
				leads[self.wl[player]] = poke'''
		leads["p1"] = next(line for line in self.text if
						   line.startswith("|switch"))
		leads["p2"] = next(line for line in self.text if
						   line.startswith("|switch"))
		return leads
	
	def parse_moves(self, teams):
		moves = {"p1":{pokemon: [] for pokemon in teams["p1"]},
				 "p2":{pokemon: [] for pokemon in teams["p2"]}}
		nicknames = {"p1":{},"p2":{}}
		for line in self.text:
			if line.startswith("|move"):
				ll = line.split("|")
				p = ll[2]
				# Glitch in replay formatting
				if re.match("p[12]{1}:", p):
					p = p.replace(":","a:")
				player = p.split("a:")[0]
				pokemon = nicknames[player][p]
				move = ll[3]
				moveset = moves[player][pokemon]
				if move not in moveset:
					moveset.append(move)
			if line.startswith("|switch") or line.startswith("|drag"):
				ll= line.split("|") 
				player = ll[2].split("a:")[0]
				nickname = ll[2]
				pokemon = format_pokemon(ll[3].split(",")[0])
				if nickname not in nicknames[player]:
					nicknames[player][nickname] = pokemon 
					moves[player][nicknames[player][nickname]] = []
		return moves

	def parse_turn_count(self):
		""" Find last line marking a turn. Number corresponds to turn count. """
		return int(next(line for line in reversed(self.text) 
						if line.startswith("|turn"))
						.split("|")[2])
	
	def move_in_replay(self, move):
		""" Return boolean indicating if move was used in match. """
		m = re.compile("\|move\|.*\|{0}\|.*".format(move))
		return next((True for line in self.text 
					 if m.match(line)), False)
					 
class Replay:

	def __init__(self, log, players, winner, url=None, number=None, tier="gen7ou"):
		self.log = log
		self._players = players
		self._winner = winner
		
		# Optional args
		self.url = url
		self.number = number
		self.tier = tier

		# Refactor to properties
		#self.leads = None
		#self.moves = None
		
	def __repr__(self):
		return self.players.__str__()
	
	@property
	def players(self):
		""" Return dict with formatted player names. """
		try:
			return self._players
		except:
			self._players = self.log.parse_players()
			return self._players
		
	@property
	def playerwl(self):	
		""" Parse replay for winner, declared at the bottom of replay. """
		try:
			return self._playerwl
		except:
			win_index = self.players.index(self._winner)
			self._loser = self.players[win_index-1]
			return {"win":self._winner, 
					"lose":self._loser,
					"p"+str(win_index + 1):"win", 
					"p"+str((win_index + 1) % 2 + 1):"lose"}
		
	def generation(self):
		""" Return int/string representing generation. """
		# Handle output
		return next(line.split("|")[2]
					for line in self.text 
					if line.startswith("|gen"))
	@property
	def teams(self):
		try:
			return self._teams
		except:
			# Generations 1-4: No team preview; must parse entire log for teams
			if re.compile(".*gen[1-4].*").match(self.tier):
				teams = self.log.parse_teams_from_scan()
			# Generation 5+: Team preview
			else:
				teams = self.log.parse_teams_from_preview()
			self._teams = teams
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
			self._leads = self.log.parse_leads()
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
		a = r.teams_from_preview()
		b = r.get_moves()

if __name__ == "__main__":
	l = [replay("http://replay.pokemonshowdown.com/smogtours-ou-39893") for i in xrange(0,100)]
	profile.run('main(l)')
	