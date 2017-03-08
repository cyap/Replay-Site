import operator
from collections import Counter
from itertools import chain, combinations, groupby

from replay import Replay

AGGREGATED_FORMS = {"Arceus-*", "Pumpkaboo-*", "Gourgeist-*" "Rotom-Appliance"}
ROTOM_FORMS = ["Rotom-Wash", "Rotom-Heat", "Rotom-Mow", "Rotom-Fan", "Rotom-Frost"]
PUMPKIN_FORMS = ["", "-Large", "-Super", "-Small"]
ARCEUS_FORMS = ["", "-Bug", "-Dark", "-Dragon", "-Electric", "-Fairy", "-Fighting", "-Fire", "-Flying", "-Ghost", "-Grass", "-Ground", "-Ice", "-Poison", "-Psychic", "-Rock", "-Steel", "-Water"]
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
	print teams
	return Counter(teams)

def wins(replays):
	teams = chain.from_iterable([replay.teams["win"] for replay in replays])
	return Counter(teams)
	
def combos(replays, size = 2, cutoff = 2):

	#combos = chain.from_iterable(list(combinations(replay.teams["win"], size)) 
	#							+ list(combinations(replay.teams["lose"],size))
	#							  for replay in replays)

	uncounted_combos = chain.from_iterable(chain.from_iterable(
			 replay.combos(size)[team] for team in ("win","lose")) 
			 for replay in replays)

	combos = Counter((format_combo(frozenset(combination)) 
					for combination in uncounted_combos))
	if cutoff:
		combos = Counter({combo:use for combo,use in combos.iteritems() 
						  if use > cutoff})
	return combos


def combo_wins(replays, size = 2):
	combos = chain.from_iterable((list(combinations(replay.teams["win"], size))
								  for replay in replays))
	return Counter((format_combo(frozenset(combination)) 
					for combination in combos))
def leads(replays):
	leads = chain.from_iterable((replay.get_leads()["win"], 
								replay.get_leads()["lose"])
								  for replay in replays)
	return Counter(leads)
	
def lead_wins(replays):
	leads = (replay.get_leads()["win"] for replay in replays)
	return Counter(leads)

def moves(replays, pokemonList):
	# Create move counter
	return {pokemon: Counter(chain.from_iterable([
						replay.moves["win"].get(pokemon, [])
					  + replay.moves["lose"].get(pokemon, []) for replay in replays]))
						for pokemon in pokemonList}
	#return {key: value for key, value in unfiltered_moves.iteritems() if value} 

def move_wins(replays, pokemonList):

	
	return {pokemon: Counter(chain.from_iterable([
		replay.moves["win"].get(pokemon, []) for replay in replays]))
		for pokemon in pokemonList}
	#return {key: value for key, value in unfiltered_moves.iteritems() if value} 
	
def format_combo(pairing):
	return str(pairing).strip("frozenset(").strip(")").replace("'","")
	
	
def aggregate_forms(data, generation="4", counter=False):
	if generation == "4":
		if counter:
			data.update(list(chain.from_iterable(
				("Rotom-Appliance" for i in range(data[poke]))
				for poke in data if poke.startswith("Rotom-"))))
		else:
			data["Rotom-Appliance"] = reduce(lambda x,y:x+y, (data.get(form, Counter()) 
				for form in ROTOM_FORMS))
	else:
	# TODO: Try / catach with +=
		if not counter:
			data["Gourgeist-*"] = reduce(lambda x,y: x+y, 
				(data.get("Gourgeist"+form, Counter()) for form in PUMPKIN_FORMS))
			data["Pumpkaboo-*"] = reduce(lambda x,y: x+y, 
				(data.get("Pumpkaboo"+form, Counter()) for form in PUMPKIN_FORMS))
			data["Arceus-*"] = reduce(lambda x,y: x+y, 
				(data.get("Arceus"+form, Counter()) for form in ARCEUS_FORMS))
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
	rankings = chain.from_iterable([rank for i in xrange(0,count)] 
		for rank, count in zip(unique_ranks, counts))
						  
	for i, elemUse in enumerate(sorted_usage):
		element = elemUse[0]
		uses = elemUse[1]
		userate = 100 * float(uses)/total
		winrate = 100 * float(wins[element])/uses
		ranking = str(next(rankings)) if element not in AGGREGATED_FORMS else "-"
		
		body += "| {0} | {1} | {2} | {3}{4:.2f}% | {5}{6:.2f}% |\n".format(
				ranking + " " * (4 - len(ranking)),
				element + " " * (cwidth - len(element)), 
				" " * (3 - len(str(uses))) + str(uses), 
				" " * (3-len(str(int(userate)))), userate,
				" " * (3-len(str(int(winrate)))), winrate
				)
	return header + body

def stats_from_text(text):
	try:
		rows = text.split("\n")[3:] # TODO: Account for header
		split_row = rows[0].split("|")
		total = round(int(split_row[3].strip()) / (float(split_row[4].strip().strip("%"))/100))
		return {"usage": Counter({split_row[2].strip(): int(split_row[3].strip()) for
				split_row in (row.split("|") for row in rows)}),
				"wins": Counter({split_row[2].strip():
					int(round(int(split_row[3].strip())
					* float(split_row[5].strip().strip("%"))/100)) for split_row in (row.split("|") for row in rows)}),
				"total":total}
	except:
		return {"usage": Counter(), "wins": Counter(), "total": 0}
			
			#"total": next(int(split_row[3].strip()) / int(split_row[4].strip()) for split_row in (rows[0].split("|")))}
			
def accumulate(iterable, func=operator.add):
	''' Raw code for accumulate function (not available prior to Python 3) '''
	it = iter(iterable)
	total = next(it)
	yield total
	for element in it:
		total = func(total, element)
		yield total
			
			
			
			