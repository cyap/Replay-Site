import operator
from collections import Counter, namedtuple
from itertools import accumulate, chain, combinations, groupby

from .replay import Replay

ROTOM_FORMS = ["-Wash", "-Heat", "-Mow", "-Fan", "-Frost"]
PUMPKIN_FORMS = ["", "-Large", "-Super", "-Small"]
ARCEUS_FORMS = ["", "-Bug", "-Dark", "-Dragon", "-Electric", "-Fairy", "-Fighting", "-Fire", "-Flying", "-Ghost", "-Grass", "-Ground", "-Ice", "-Poison", "-Psychic", "-Rock", "-Steel", "-Water"]
AGGREGATED_FORMS = {"Arceus-*":ARCEUS_FORMS, 
					"Pumpkaboo-*":PUMPKIN_FORMS, 
					"Gourgeist-*":PUMPKIN_FORMS, 
					"Rotom-Appliance":ROTOM_FORMS}
# Separate responsibilities: for filtering teams and running data on teams
# Port to database

#def get_data(teams):
#	data = Counter()
#	map(lambda x:operator.setitem(data, x, data.get(x, 0) + 1), teams)
#	return data

def aggregate_wins(replays, key):
	wins = []
	ties = []
	for replay in replays:
		try:
			wins += getattr(replay, key)[replay.name_to_num(replay.winner)]
		except:
			ties += getattr(replay, key)["p1"]
			ties += getattr(replay, key)["p2"]
	tie_counter = Counter(ties)
	for k, v in tie_counter.items():
		tie_counter[k] = v * .5
	return Counter(wins) + tie_counter
	
def usage(replays):
	teams = chain.from_iterable([replay.teams["p1"]
							   + replay.teams["p2"] 
							   for replay in replays])
	return Counter(teams)

def usage2(replays, key):
	teams = chain.from_iterable([replay.teams.get(replay.name_to_num(key), {})
			for replay in replays])
	return Counter(teams)

def wins(replays):
	return aggregate_wins(replays, "teams")
	
def wins2(replays, key):
	teams = chain.from_iterable([replay.teams.get(key, {}) for replay in replays if replay.teams.get(key, {}) == replay.teams.get("win", [])])
	return Counter(teams)
	
def combos(replays, size = 2, cutoff = 0):

	uncounted_combos = chain.from_iterable(chain.from_iterable(
			 replay.combos(size)[team] for team in ("p1","p2")) 
			 for replay in replays)

	combos = Counter((format_combo(combination) 
					for combination in uncounted_combos))
	if cutoff:
		combos = Counter({combo:use for combo,use in combos.items() 
						  if use >= cutoff})
	
	for combo in list(combos.keys()):
		for pokemon in AGGREGATED_FORMS:
			if pokemon in combo:
				for form in AGGREGATED_FORMS[pokemon]:
					if pokemon.split("-")[0] + form in combo:
						del(combos[combo])
	
	# REFACTOR
	return combos


def combo_wins(replays, size = 2):
	wins = []
	ties = []
	for replay in replays:
		combos = replay.combos(size)
		try:
			wins += combos[replay.name_to_num(replay.winner)]
		except:
			ties += combos["p1"]
			ties += combos["p2"]
	tie_counter = Counter(map(format_combo, ties))
	for k, v in tie_counter.items():
		tie_counter[k] = v * .5
	return Counter(map(format_combo, wins)) + tie_counter
					
def leads(replays):
	leads = chain.from_iterable(
			replay.leads["p1"] 
			+ replay.leads["p2"] for replay in replays)
	return Counter(leads)
	
def lead_wins(replays):
	return aggregate_wins(replays, "leads")

def moves(replays, pokemon_list):
	# Create move counter
	'''
	moves = {}
	for replay in replays:
		win = replay.moves["win"]
		lose = replay.moves["lose"]
		for pokemon in pokemonList:
			moves[pokemon] = (moves.get(pokemon, Counter()) +
				(Counter(chain.from_iterable(
				[replay.moves["win"].get(pokemon, [])
			   + replay.moves["lose"].get(pokemon, [])]))))
	return moves
	'''	
	
	# Sum lists
	return {pokemon: Counter(chain.from_iterable(
		replay.moves["p1"].get(pokemon, []) 
		+ replay.moves["p2"].get(pokemon, [])
		for replay in replays))
		for pokemon in pokemon_list}

def move_wins(replays, pokemon_list):
	win_counter = {pokemon:Counter() for pokemon in pokemon_list}
	tie_counter = {pokemon:Counter() for pokemon in pokemon_list}
	for replay in replays:
		try:
			moves = replay.moves[replay.name_to_num(replay.winner)]
			for pokemon in moves:
				win_counter.get(pokemon, Counter()).update(moves.get(pokemon, []))
		except:
			p1_moves = replay.moves["p1"]
			for pokemon in p1_moves:
				tie_counter.get(pokemon, Counter()).update(p1_moves.get(pokemon, []))
			p2_moves = replay.moves["p2"]
			for pokemon in p2_moves:
				tie_counter.get(pokemon, Counter()).update(p2_moves.get(pokemon, []))
				
	for counter in tie_counter.values():
		for key in counter:
			counter[key] *= 0.5
	
	return {pokemon:win_counter[pokemon] + tie_counter[pokemon] 
			for pokemon in pokemon_list}
	
def format_combo(combo):
	return combo
	
def format_combo2(combo):
	return ' / '.join(pokemon for pokemon in combo)
	
def teammates(replays, filter=None):
	tm = {}
	if filter == "win":
		wins = {}
		ties = {}
		for replay in replays:
			try:
				for pokemon in replay.teams[replay.name_to_num(replay.winner)]:
					wins[pokemon] = (wins.get(pokemon, Counter()) +
						Counter(replay.teams[replay.name_to_num(replay.winner)]))
			except:
				for player in ("p1", "p2"):
					for pokemon in replay.teams[player]:
						ties[pokemon] = (ties.get(pokemon, Counter()) +
							Counter(replay.teams[player]))
		for pokemon in ties:
			for key in ties[pokemon]:
				ties[pokemon][key] *= 0.5
		pokemon_list = set(wins.keys()) | set(ties.keys())
		tm = {poke:wins.get(poke, Counter()) + ties.get(poke, Counter())
			for poke in pokemon_list}
	else:
		for replay in replays:
			for player in ("p1", "p2"):
				for pokemon in replay.teams[player]:
					tm[pokemon] = (tm.get(pokemon, Counter()) +
						Counter(replay.teams[player]))
	# Delete own Pokemon
	for pokemon in tm:
		del(tm[pokemon][pokemon])
	# Delete alternate forms
	for pokemon in AGGREGATED_FORMS:
		for form in AGGREGATED_FORMS[pokemon]:
			try:
				del(tm[pokemon][pokemon.split("-")[0]+form])
				del(tm[pokemon.split("-")[0]+form][pokemon])
			except:
				pass
	return aggregate_forms(tm)

def aggregate_forms(data, generation="4", counter=False):
	if generation == "4":
		default = 0 if counter else Counter()
		data["Rotom-Appliance"] = sum((data.get("Rotom"+form, default) 
			for form in ROTOM_FORMS), default)
		if data["Rotom-Appliance"] == 0:
			del(data["Rotom-Appliance"])
		#else:
			#data["Rotom-Appliance"] = sum((data.get(form, Counter()) 
				#for form in ROTOM_FORMS), Counter())
			#data["Rotom-Appliance"] = reduce(lambda x,y: x+y, 
				#(data.get(form, Counter()) for form in ROTOM_FORMS))
	else:
		# TODO: Try / catch with +=
		if not counter:
			for pokemon in AGGREGATED_FORMS:
				if pokemon != "Rotom-Appliance":
					data[pokemon] = sum(
						(data.get(pokemon.split("-")[0] + form, Counter())
						for form in AGGREGATED_FORMS[pokemon]), Counter())			
	return data

			
def pretty_print(cname, cwidth, usage, wins, total):
	header = (
		"+ ---- + {2} + ---- + ------- + ------- +\n"
		"| Rank | {0}{1} | Use  | Usage % |  Win %  |\n"
		"+ ---- + {2} + ---- + ------- + ------- +\n"
		).format(cname, " " * (cwidth - len(cname)), "-" * cwidth)
		
	body = ""
	# Sort by usage, then by win %
	# Option: Sort by name as third tiebreaker
	sorted_usage = sorted(usage.most_common(), 
					  key=lambda x: (usage[x[0]], float(wins[x[0]])/x[1]),
					  reverse=True)
	# Calculating the rankings
	# Number of Pokemon with same ranking
	counts = [len(list(element[1])) for element in groupby(
		 [poke for poke in sorted_usage if poke[0] not in AGGREGATED_FORMS],
		 lambda x: x[1])]
	# Translate to rankings
	unique_ranks = accumulate([1] + counts[:-1:])

	# Unpack rankings
	rankings = chain.from_iterable([rank for i in range(0,count)] 
		for rank, count in zip(unique_ranks, counts))
						  
	for i, elemUse in enumerate(sorted_usage):
		element = elemUse[0]
		uses = elemUse[1]
		userate = 100 * float(uses)/total
		winrate = 100 * float(wins[element])/uses
		rank = str(next(rankings)) if element not in AGGREGATED_FORMS else "-"
		
		body += "| {0} | {1} | {2} | {3}{4:.2f}% | {5}{6:.2f}% |\n".format(
				rank + " " * (4 - len(rank)),
				str(element) + " " * (cwidth - len(str(element))), 
				" " * (4 - len(str(uses))) + str(uses), 
				" " * (3-len(str(int(userate)))), userate,
				" " * (3-len(str(int(winrate)))), winrate
				)
	return header + body

def generate_rows(usage, wins, total, func=str):
	
	Row = namedtuple("Row", 'rank, element, uses, userate, winrate')
	# Rankings
	
	# Sort by usage, then by win %
	# Option: Sort by name as third tiebreaker
	sorted_usage = sorted(usage.most_common(), 
					  key=lambda x: (usage[x[0]], float(wins[x[0]])/x[1]),
					  reverse=True)
					  
	# Calculating the rankings
	# Number of Pokemon with same ranking
	counts = [len(list(element[1])) for element in groupby(
		 [poke for poke in sorted_usage if poke[0] not in AGGREGATED_FORMS],
		 lambda x: x[1])]
		 
	# Translate to rankings
	unique_ranks = accumulate([1] + counts[:-1:])

	# Unpack rankings
	rankings = chain.from_iterable([rank for i in range(0,count)] 
		for rank, count in zip(unique_ranks, counts))
	
	return [
		Row(
			"-" if elem_use[0] in AGGREGATED_FORMS else str(next(rankings)), 
			#names[elem_use[0]],
			#str(elem_use[0]),
			func(elem_use[0]),
			elem_use[1],
			100 * float(elem_use[1])/total,
			100 * float(wins[elem_use[0]])/elem_use[1]
		)
		for i, elem_use in enumerate(sorted_usage)]
	
def print_table(cname, cwidth, rows):

	# Row: (rank, element, usage, use %, win %)
	header = (
		"+ ---- + {2} + ---- + ------- + ------- +\n"
		"| Rank | {0}{1} | Use  | Usage % |  Win %  |\n"
		"+ ---- + {2} + ---- + ------- + ------- +\n"
		).format(cname, " " * (cwidth - len(cname)), "-" * cwidth)
		
	body = "\n".join(
		"| {0} | {1} | {2} | {3}{4:.2f}% | {5}{6:.2f}% |".format(
			row.rank + " " * (4 - len(row.rank)),
			row.element + " " * (cwidth - len(row.element)),
			" " * (4 - len(str(row.uses))) + str(row.uses), 
			" " * (3-len(str(int(row.userate)))), row.userate,
			" " * (3-len(str(int(row.winrate)))), row.winrate
		) for row in rows
	)

	return header + body

def stats_from_text(text):
	""" Convert text stat output back to counters """
	
	# TODO: Change to loop so invalid rows can be thrown out
	
	# Find where stats start
	total = 0
	rows = text.splitlines()
	for i, row in enumerate(rows):
		try:
			first_row = row.split("|")
			total = round(int(first_row[3].strip()) /
					(float(first_row[4].strip().strip("%"))/100))
			rows = rows[i:]
			break
		except:
			pass
			
	return {"usage": Counter({
				split_row[2].strip(): int(split_row[3].strip()) for
				split_row in (row.split("|") for row in rows)}),
			"wins": Counter({
				split_row[2].strip(): int(round(int(split_row[3].strip())
				* float(split_row[5].strip().strip("%"))/100)) for split_row
				in (row.split("|") for row in rows)}),
			"total":total}
			
	
			