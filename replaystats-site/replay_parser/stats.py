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

def get_data(teams):
	data = Counter()
	map(lambda x:
		operator.setitem(data, x, data.get(x, 0) + 1), teams)
	return data
	
def usage(replays):
	teams = chain.from_iterable([replay.teams["win"]
							   + replay.teams["lose"] 
							   for replay in replays])
	return Counter(teams)

def usage2(replays, key):
	teams = chain.from_iterable([replay.teams.get(key, {}) for replay in replays])
	#printteams
	return Counter(teams)

def wins(replays):
	teams = chain.from_iterable([replay.teams["win"] for replay in replays])
	return Counter(teams)
	
def wins2(replays, key):
	teams = chain.from_iterable([replay.teams.get(key, {}) for replay in replays if replay.teams.get(key, {}) == replay.teams["win"]])
	return Counter(teams)
	
def combos(replays, size = 2, cutoff = 0):

	#combos = chain.from_iterable(list(combinations(replay.teams["win"], size)) 
	#							+ list(combinations(replay.teams["lose"],size))
	#							  for replay in replays)

	uncounted_combos = chain.from_iterable(chain.from_iterable(
			 replay.combos(size)[team] for team in ("win","lose")) 
			 for replay in replays)

	combos = Counter((format_combo(frozenset(combination)) 
					for combination in uncounted_combos))
	if cutoff:
		combos = Counter({combo:use for combo,use in combos.items() 
						  if use > cutoff})
	
	for combo in list(combos.keys()):
		for pokemon in AGGREGATED_FORMS:
			if pokemon in combo:
				for form in AGGREGATED_FORMS[pokemon]:
					if pokemon.split("-")[0] + form in combo:
						del(combos[combo])
	'''
	for pokemon in AGGREGATED_FORMS:
		for form in AGGREGATED_FORMS[pokemon]:
			try:
				if pokemon == "Rotom-Appliance":
					del(combos[frozenset((pokemon, form))])
				else:
					del(combos[frozenset((pokemon, pokemon.split("-")[0] + form))])
			except:
				pass'''
	
	# REFACTOR
	return combos


def combo_wins(replays, size = 2):
	combos = chain.from_iterable((list(combinations(replay.teams["win"], size))
								  for replay in replays))
	return Counter((format_combo(frozenset(combination)) 
					for combination in combos))
def leads(replays, doubles=False):
	##printlen(replays)
	if not doubles:
		leads = chain.from_iterable((replay.leads["win"], 
									replay.leads["lose"])
									  for replay in replays)
	else:
		leads = chain.from_iterable(replay.leads["win"] + replay.leads["lose"] for replay in replays)
	
	##printleads
								  
	#a = list(leads)
	##printlen(a)
	#l = Counter(a)
	##printsum(l.values())
	return Counter(leads)
	
def lead_wins(replays, doubles=False):
	if not doubles:
		leads = (replay.leads["win"] for replay in replays)
	else:
		leads = chain.from_iterable(replay.leads["win"] for replay in replays)
	return Counter(leads)

def moves(replays, pokemonList):
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
		replay.moves["win"].get(pokemon, []) + replay.moves["lose"].get(pokemon, [])
		for replay in replays))
		for pokemon in pokemonList}

def move_wins(replays, pokemonList):
	return {pokemon: Counter(chain.from_iterable([
		replay.moves["win"].get(pokemon, []) for replay in replays]))
		for pokemon in pokemonList}
	
def format_combo(combo):
	return combo
	
def format_combo2(combo):
	return ' / '.join(pokemon for pokemon in combo)
	
def teammates(replays, filter=None):
	tm = {}
	teams = (filter,) if filter else ("win", "lose")
	# Assign teams to each Pokemon
	for replay in replays:
		#for team in (replay.teams["win"], replay.teams["lose"]): 
		#for team in filter or ("win", "lose"):
		for team in teams:
			for pokemon in replay.teams[team]:
				tm[pokemon] = tm.get(pokemon, Counter()) + Counter(replay.teams[team])
	
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
	
	#return sum((sum((Counter({pokemon: team for pokemon in team}) for team in replay.teams.values()), Counter()) for replay in replays), Counter())

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
		"+ ---- + {2} + --- + ------- + ------- +\n"
		"| Rank | {0}{1} | Use | Usage % |  Win %  |\n"
		"+ ---- + {2} + --- + ------- + ------- +\n"
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
				" " * (3 - len(str(uses))) + str(uses), 
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
		"+ ---- + {2} + --- + ------- + ------- +\n"
		"| Rank | {0}{1} | Use | Usage % |  Win %  |\n"
		"+ ---- + {2} + --- + ------- + ------- +\n"
		).format(cname, " " * (cwidth - len(cname)), "-" * cwidth)
		
	body = "\n".join(
		"| {0} | {1} | {2} | {3}{4:.2f}% | {5}{6:.2f}% |".format(
			row.rank + " " * (4 - len(row.rank)),
			row.element + " " * (cwidth - len(row.element)),
			" " * (3 - len(str(row.uses))) + str(row.uses), 
			" " * (3-len(str(int(row.userate)))), row.userate,
			" " * (3-len(str(int(row.winrate)))), row.winrate
		) for row in rows
	)

	return header + body

def stats_from_text(text):
	try:
		rows = text.split("\n")[3:] # TODO: Account for header
		split_row = rows[0].split("|")
		total = round(int(split_row[3].strip()) /
			(float(split_row[4].strip().strip("%"))/100))
		
		return {"usage": Counter({
					split_row[2].strip(): int(split_row[3].strip()) for
					split_row in (row.split("|") for row in rows)}),
				"wins": Counter({
					split_row[2].strip(): int(round(int(split_row[3].strip())
					* float(split_row[5].strip().strip("%"))/100)) for split_row
					in (row.split("|") for row in rows)}),
				"total":total}
	except:
		return {"usage": Counter(), "wins": Counter(), "total": 0}
			
			#"total": next(int(split_row[3].strip()) / int(split_row[4].strip()) for split_row in (rows[0].split("|")))}
			
			
			