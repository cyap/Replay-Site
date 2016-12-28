import operator
from collections import Counter
from itertools import chain, combinations

from replay import replay

# Separate responsibilities: for filtering teams and running data on teams
# Port to database

def getData(teams):
	data = Counter()
	map(lambda x:
		operator.setitem(data, x, data.get(x, 0) + 1), teams)
	return data
	
def usage(replays):
	teams = chain.from_iterable([replay.teams["win"]
							   + replay.teams["lose"] 
							   for replay in replays])
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

	combos = Counter((formatCombo(frozenset(combination)) 
					for combination in combos))
	if cutoff:
		combos = Counter({combo:use for combo,use in combos.iteritems() 
						  if use > cutoff})
	return combos


def comboWins(replays, size = 2):
	combos = chain.from_iterable((list(combinations(replay.teams["win"], size))
								  for replay in replays))
	return Counter((formatCombo(frozenset(combination)) 
					for combination in combos))
def leads(replays):
	leads = chain.from_iterable((replay.getLeads()["win"], 
								replay.getLeads()["lose"])
								  for replay in replays)
	return Counter(leads)
	
def leadWins(replays):
	leads = (replay.getLeads()["win"] for replay in replays)
	return Counter(leads)

def moves(replays, pokemonList):
	# replay.moves = {win = team, lose = team}
	# team = [pokemon:moveset, pokemon2:moveset]
		# Create move counter
	return {pokemon: Counter(chain.from_iterable([
				replay.getMoves()["win"][pokemon]
			  + replay.getMoves()["lose"][pokemon] for replay in replays]))
				for pokemon in pokemonList}
	# check if pokemon in teams -> sets?
	# [iterable of moves]
	# return {pokemon:moveCounter, pokemon:moveCounter}

def moveWins(replays, pokemonList):
	return {pokemon: Counter(chain.from_iterable([
		replay.getMoves()["win"][pokemon] for replay in replays]))
		for pokemon in pokemonList}
	
def formatCombo(pairing):
	return str(pairing).strip("frozenset(").strip(")").replace("'","")
			
def prettyPrint(cname, cwidth, usage, wins, total, hide = 1):
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
	return header + "\n" + body
	print header
	print body
#	print footer
		