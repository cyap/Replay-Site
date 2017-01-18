from itertools import groupby, chain, repeat
import operator

from django.http import HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.shortcuts import redirect

from replay_parser import replayCompile, statCollector

AGGREGATED_FORMS = {"Arceus-*", "Pumpkaboo-*"}

def index(request):
	if request.method == "GET":
		return render(request, "index.html")
		
	if request.method == "POST":
		if "link_submit" in request.POST:
			urls = request.POST["replay_urls"].split("\n")
			replays = replayCompile.replays_from_links(urls)
		else:
			if not request.POST["tier"]:
				tiers = ["gen7pokebankou"]
			else:
				tiers = request.POST["tier"].split(",")
			if "thread_submit" in request.POST:
				url = request.POST["url"]
				replays = replayCompile.replays_from_thread(url, tiers=tiers)
			elif "range_submit" in request.POST:
				replays = replayCompile.replays_from_range(
				range(int(request.POST["start"]),int(request.POST["end"])),
				tiers=tiers)
		# Stats
		usage_table = usage(replays)
		whitespace_table = whitespace(usage_table)
		return render(request, "stats.html", {"usage_table" : usage_table,
											  "whitespace" : whitespace_table})

def spl_index(request):
	if request.method == "GET":
		return render(request, "spl_index.html")
		
	if request.method == "POST":
		urls = request.POST["replay_urls"].split("\n")
		replays = replayCompile.replays_from_links(urls)
		moves = [replay.get_moves() for replay in replays]
		
		# Overall Stats
		usage_table = usage(replays)
		whitespace_table = whitespace(usage_table)
		
		# Raw
		raw = (
			"\n\n---\n\n".join([
			"\n\n".join([
			player.capitalize() + ": " + replay.playerwl[player] + "\n"
			+ "\n".join([pokemon + ": " 
			+ " / ".join([move for move in replay.moves[player][pokemon]])
			for pokemon in replay.moves[player]])
			for player in ("win","lose")])
			for replay in replays]))
		row_count = len(replays) * 18 - 2
		
		# Set not removing duplicates
		return render(request, "spl_stats.html", {
					"usage_table" : usage_table,
					"whitespace" : whitespace_table,
					"replays" : replays,
					"raw":raw,
					"row_count":row_count})

def usage(replays):
	usage = statCollector.usage(replays)
	wins = statCollector.wins(replays)
	total = len(replays) * 2
	
	sorted_usage = sorted(usage.most_common(), 
						  key=lambda x: (usage[x[0]], float(wins[x[0]])/x[1]),
						  reverse=True)
	print sum(usage.values())
	
	# Calculate rank? Accumulate the length of the groups preceding the group
	'''
	rankings = chain.from_iterable(
			   ((rank, len(element[1])) for rank, element in
			   enumerate(groupby(usage.most_common(), lambda x: x[1]), 1)))'''
			   
	# Number of Pokemon with same ranking
	counts = [len(list(element[1])) for element in groupby(
			 [poke for poke in sorted_usage if poke[0] not in AGGREGATED_FORMS],
			 lambda x: x[1])]
	# Translate to rankings
	unique_ranks = accumulate([1] + counts[:-1:])
	# Unpack rankings
	rankings = chain.from_iterable([rank for i in xrange(0,count)] 
									for rank, count in zip(unique_ranks, counts))
	
	return [(element[0], 
			 element[1], 
			 "{0:.2f}%".format(100 * float(element[1])/total),
			 "{0:.2f}%".format(100 * float(wins[element[0]])/element[1]),
			 str(next(rankings)) if element[0] not in AGGREGATED_FORMS else "-"
			 )
			 for i, element in enumerate(sorted_usage)]

def whitespace(usage_table):
	return [(
			entry[0] + " " * (18 - len(entry[0])), 
			" " * (3 - len(str(entry[1]))) + str(entry[1]), 
			" " * (7 - len(str(entry[2]))) + str(entry[2]),
			" " * (7 - len(str(entry[3]))) + str(entry[3]),
			entry[4] + " " * (4-len(entry[4]))
			)
			for rank, entry in enumerate(usage_table, 1)]
	
def accumulate(iterable, func=operator.add):
	''' Raw code for accumulate function (not available prior to Python 3 '''
	it = iter(iterable)
	total = next(it)
	yield total
	for element in it:
		total = func(total, element)
		yield total
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
'''
def index(request):
	if request.method == "GET":
		return render(request, "index.html")

	if request.method == "POST":
		start = request.POST["start"]
		end = request.POST["end"]
		url = request.POST["url"]
		rng = range(int(start), int(end))
		pairings = tournament.parsePairings(url = url)
		participants = tournament.participantsFromPairings(pairings)
		tour = tournament.Tournament(
			   replayCompile.replaysFromRange(rng), pairings, participants)
		replays = tour.matchTournament()
		matches = tour.pairingReplayMap
		return render(request, "results.html", {
		#return redirect('/replays/', {
			"start" : start,
			"end" : end,
			"url" : url,
			#"pairings" : pairings,
			"participants" : participants,
			"matches" : [(str(pairing).strip("frozenset"), 
						  matches[pairing][0].number, 
						  matches[pairing][0].players,
						  matches[pairing][1],
						  matches[pairing][0].url) if pairing in matches 
						  else (
						  (str(pairing).strip("frozenset")), "", "", "No match found") 
						  for pairing in pairings]
		})'''