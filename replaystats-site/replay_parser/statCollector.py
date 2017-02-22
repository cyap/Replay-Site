import operator
from collections import Counter
from itertools import chain, combinations

from replay import Replay

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
	teams = chain.from_iterable([replay.teams[key] for replay in replays])
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
	# replay.moves = {win = team, lose = team}
	# team = [pokemon:moveset, pokemon2:moveset]
		# Create move counter
	return {pokemon: Counter(chain.from_iterable([
				replay.get_moves()["win"][pokemon]
			  + replay.get_moves()["lose"][pokemon] for replay in replays]))
				for pokemon in pokemonList}
	# check if pokemon in teams -> sets?
	# [iterable of moves]
	# return {pokemon:moveCounter, pokemon:moveCounter}

def move_wins(replays, pokemonList):
	return {pokemon: Counter(chain.from_iterable([
		replay.get_moves()["win"][pokemon] for replay in replays]))
		for pokemon in pokemonList}
	
def format_combo(pairing):
	return str(pairing).strip("frozenset(").strip(")").replace("'","")
			
def pretty_print(cname, cwidth, usage, wins, total, hide = 1):
	header = (
#		"[B]Sample Text:[/B]\n"
#		"[HIDE]"+hide * ("[CODE]") +
		"+ ---- + {2} + --- + -------- + ------- +\n"
		"| Rank | {0}{1} | Use |  Usage % |  Win %  |\n"
		"+ ---- + {3} + --- + -------- + ------- +"
		).format(cname, " " * (cwidth - len(cname)), "-" * cwidth, "-" * cwidth)
	
	body = ""
	for i, elemUse in enumerate(usage.most_common()):
		element = elemUse[0]
		uses = elemUse[1]
		userate = 100 * float(uses)/total
		winrate = 100 * float(wins[element])/uses
		body += "| {0} | {1} | {2} | {3}{4:.2f}%  | {5}{6:.2f}% |\n".format(
				str(i+1) + " " * (4 - len(str(i+1))),
				element + " " * (cwidth - len(element)), 
				" " * (3 - len(str(uses))) + str(uses), 
				" " * (3-len(str(int(userate)))), userate,
				" " * (3-len(str(int(winrate)))), winrate)
	footer = "[/CODE]"+("[/HIDE]") * hide
	
	print header
	print body
	return header + "\n" + body
#	print footer

def stats_from_text(text):
	rows = text.split("\n")[3:] # TODO: Account for header
	split_row = rows[0].split("|")
	total = round(int(split_row[3].strip()) / (float(split_row[4].strip().strip("%"))/100))

	return {"usage": Counter({split_row[2].strip(): int(split_row[3].strip()) for
			split_row in (row.split("|") for row in rows)}),
			"wins": Counter({split_row[2].strip():
				int(round(int(split_row[3].strip())
				* float(split_row[5].strip().strip("%"))/100)) for split_row in (row.split("|") for row in rows)}),
			"total":total}
			
			#"total": next(int(split_row[3].strip()) / int(split_row[4].strip()) for split_row in (rows[0].split("|")))}
			
			
			
			
			
			