from itertools import groupby, chain, repeat
import operator

from django.http import HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.shortcuts import redirect

from replay_parser import replayCompile, statCollector, tournament, circuitTours

AGGREGATED_FORMS = {"Arceus-*", "Pumpkaboo-*", "Rotom-Appliance"}
TIERS = ["RBY","GSC","ADV","DPP","BW","ORAS","SM"]

def index(request):
	if request.method == "GET":
		return render(request, "index2.html")
		
	if request.method == "POST":
		# Thread
		replays_from_thread = set(
			chain.from_iterable(
				(replayCompile.replays_from_thread(
					threadurl=threadurl, 
					tiers=({tier.strip() for tier in tiers.split(",")} 
						if tiers else {"gen7pokebankou"}), 
					start=int(start or 1), 
					end=int(end) if end else None)
					for threadurl, tiers, start, end in zip(
						request.POST.getlist("thread_url"),
						request.POST.getlist("thread_tiers"),
						request.POST.getlist("thread_start"),
						request.POST.getlist("thread_end")
					)
				)
			)
		)
		# Range
		replays_from_range = set(
			chain.from_iterable(
				(replayCompile.replays_from_range(
					range=range(int(start), int(end)), tier=tier)
					for start, end, tier in zip(
						request.POST.getlist("range_start"),
						request.POST.getlist("range_end"),
						request.POST.getlist("range_tiers")
					)
				)
			)
		)
		# Links
		replays_from_links = replayCompile.replays_from_links(
			request.POST["replay_urls"].split("\n")
		)

		# Stats
		cumulative = reduce(
			(lambda x,y: 
				{
				"usage":x["usage"] + y["usage"],
				"wins":x["wins"] + y["wins"],
				"total":x["total"] + y["total"]
				}
			), (statCollector.stats_from_text(text) 
				for text in request.POST.getlist("stats"))
		)
		
		# Aggregate replays
		replays = replays_from_thread | replays_from_links | replays_from_range
		
		#tiers = {}
		tiers=({tier.strip() for tier in request.POST["thread_tiers"].split(",")} 
					if request.POST["thread_tiers"] else {"gen7pokebankou"})
					
		# Refactor
		# Rotom method should go in .replay
		# For tier display: calculate / autofill in form
		
		# Tier
		# move to replays
		try:
			gen_num = next((char for char in min(tiers) if char.isdigit()), 6)
			tier_name = min(tiers).split(gen_num)[1].split("pokebank")[-1].upper()
			tier_label = TIERS[int(gen_num)-1] + " " + tier_name
		except:
			tier_label = "???"
			
		# Usage
		usage = statCollector.usage(replays)
		wins = statCollector.wins(replays)
		total = len(replays) * 2
		
		# Handling gen 4 rotom forms
		if "gen4ou" in tiers:
			usage.update(list(chain.from_iterable(
			("Rotom-Appliance" for i in range(usage[poke]))
			for poke in usage if poke.startswith("Rotom-"))))
		
			wins.update(list(chain.from_iterable(
			("Rotom-Appliance" for i in range(wins[poke]))
			for poke in usage if poke.startswith("Rotom-"))))
			
		# Adding cumulative stats
		if cumulative:
			usage.update(cumulative["usage"])
			wins.update(cumulative["wins"])
			total += cumulative["total"]
		
		usage_table = usage_view(usage, wins, total)
		
		sprite_header = (
			"[IMG]http://www.smogon.com/dex/media/sprites/xyicons/"
			"{0}.png[/IMG][B]{1}[/B]"
			"[IMG]http://www.smogon.com/dex/media/sprites/xyicons/"
			"{0}.png[/IMG]"
			).format(usage_table[0][0], tier_label)
		# Missing Pokemon
		missing = chain.from_iterable(
			(((replay.playerwl[wl],6-len(replay.teams[wl])) 
			for wl in ("win","lose") if len(replay.teams[wl]) < 6) 
			for replay in replays))
		missing_whitespace = ("\n[LIST]" + "\n".join(
				 "[*][I]Missing {0} Pokemon from {1}.[/I]"
				 .format(miss[1], miss[0]) for miss in missing) + "\n[/LIST]" 
				 if set(missing) else "")

		usage_whitespace = (sprite_header + "\n[CODE]\n" +
			statCollector.pretty_print("Pokemon", 18, usage, wins, total)
			+ "[/CODE]" + missing_whitespace)

		# Advanced stats
		# if advanced stats:
		# Counter of moves
		moves = statCollector.moves(replays, usage.keys())
		move_wins = statCollector.move_wins(replays, usage.keys())

		moves_whitespace = "\n".join(
			(statCollector.pretty_print(pokemon, 23, moves[pokemon],
			move_wins[pokemon], uses) for pokemon, uses 
			in usage.most_common()))

		return render(request, "stats.html", 
					 {"usage_table" : usage_table,
					  "net_mons" : sum(usage.values()),
					  "net_replays" : len(replays),
					  "missing":missing,
					  "tier_label":tier_label,
					  "moves_whitespace":moves_whitespace,
					  "usage_whitespace":usage_whitespace})

def spl_index(request):
	if request.method == "GET":
		return render(request, "spl_index.html")
		
	if request.method == "POST":
		if "link_submit" in request.POST:
			urls = request.POST["replay_urls"].split("\n")
			replays = replayCompile.replays_from_links(urls)
			choice = None
			template = "spl_stats.html"
			
			raw = (
			"\n\n---\n\n".join([
			"\n\n".join([
			player.capitalize() + ": " + replay.playerwl[player] + "\n"
			+ "\n".join([pokemon + ": " 
			+ " / ".join([move for move in replay.moves[player][pokemon]])
			for pokemon in replay.moves[player]])
			for player in ("win","lose")])
			for replay in replays]))
			moves = [replay.moves for replay in replays]
			pairings = None
			
		else:
			replays = replayCompile.replays_from_user(request.POST["player"],
					  tier=request.POST["tier"])
			choice = request.POST["player"].lower()
			moves = [replay.moves.get(choice) or replay.moves.get("p1" if replay.playerwl["p1"] == choice else "p2") for replay in replays]
			
			pairings = [{"replay":replay, "moves":replay.moves.get(choice) or replay.moves.get("p1" if replay.playerwl["p1"] == choice else "p2")} for replay in replays]
			template = "scout_stats.html"
			
			raw = (
			"\n\n---\n\n".join([
			choice + "\n"
			+ "\n".join([pokemon + ": " 
			+ " / ".join([move for move in (replay.moves.get(choice) or replay.moves.get("p1" if replay.playerwl["p1"] == choice else "p2"))[pokemon]])
			for pokemon in replay.moves.get(choice) or replay.moves.get("p1" if replay.playerwl["p1"] == choice else "p2")])
			for replay in replays]))

		# Overall Stats
		#usage_table = usage(replays)
		usage_table = usage(replays, key = choice)
		whitespace_table = whitespace(usage_table)
		
		# Raw original
		row_count = len(replays) * 18 - 2
		
		# Set not removing duplicates
		#return render(request, "spl_stats.html", {
		
		return render(request, template, {
					"usage_table" : usage_table,
					"whitespace" : whitespace_table,
					"replays" : replays,
					"raw":raw,
					"row_count":row_count,
					"moves":moves,
					"pairings":pairings,
					"choice":choice})


def usage_view(counter, wins, total):
	''' Given a Counter, translate to format for HTML presentation'''
	
	# Sort by usage, then by win %
	# Option: Sort by name as third tiebreaker
	sorted_usage = sorted(counter.most_common(), 
						  key=lambda x: (counter[x[0]], float(wins[x[0]])/x[1]),
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
	
	# refactor to dict for clarity
	return [(
		element[0], 
		element[1], 
		"{0:.2f}%".format(100 * float(element[1])/total),
		"{0:.2f}%".format(100 * float(wins[element[0]])/element[1]),
		str(next(rankings)) if element[0] not in AGGREGATED_FORMS else "-")
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
	''' Raw code for accumulate function (not available prior to Python 3) '''
	it = iter(iterable)
	total = next(it)
	yield total
	for element in it:
		total = func(total, element)
		yield total

def usage(replays, tiers = [], cumulative = None, key = None):
	# For scouting
	if key:
		usage = statCollector.usage2(replays, key)
	else:
		usage = statCollector.usage(replays)
		
	# Separate
	wins = statCollector.wins(replays)
	total = len(replays) * 2
	
	# For scouting
	for pokemon in usage.most_common():
		print pokemon[0], pokemon[1], pokemon[1]*100/total
	
	# Handling gen 4 rotom forms
	if "gen4ou" in tiers:
		usage.update(list(chain.from_iterable(
		("Rotom-Appliance" for i in range(usage[poke]))
		for poke in usage if poke.startswith("Rotom-"))))
		
		wins.update(list(chain.from_iterable(
		("Rotom-Appliance" for i in range(wins[poke]))
		for poke in usage if poke.startswith("Rotom-"))))
	
	# Adding cumulative stats
	if cumulative:
		usage.update(cumulative["usage"])
		wins.update(cumulative["wins"])
		total += cumulative["total"]
	
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
	
	return {'usage': [(
		element[0], 
		element[1], 
		"{0:.2f}%".format(100 * float(element[1])/total),
		"{0:.2f}%".format(100 * float(wins[element[0]])/element[1]),
		str(next(rankings)) if element[0] not in AGGREGATED_FORMS else "-")
		for i, element in enumerate(sorted_usage)],
			 'net_mons':sum(usage.values()),
			 'net_replays':len(replays)
		}


def tour_index(request):	
	if request.method == "GET":
		return render(request, "indextour.html")

	if request.method == "POST":
		if "replay_submit" in request.POST:
			replay_urls = set(request.POST.getlist("replays"))
			print replay_urls
			replays = set(replay for replay in request.session["replays"] if replay.url in replay_urls)
			# change to dict
			tiers = []
			try:
				gen_num = next((char for char in min(tiers) 
					if char.isdigit()), 6)
				tier_name = (min(tiers).split(gen_num)[1]
					.split("pokebank")[-1].upper())
				tier_label = TIERS[int(gen_num)-1] + " " + tier_name
			except:
				tier_label = "???"
		
			# Stats
			cumulative = (statCollector.stats_from_text(request.POST["stats"]) 
						  if "stats" in request.POST and request.POST["stats"]
						  else None)
			missing = chain.from_iterable((((
				replay.playerwl[wl],6-len(replay.teams[wl])) 
				for wl in ("win","lose") if len(replay.teams[wl]) < 6) 
				for replay in replays))
			usage_table = usage(replays, tiers, cumulative)
			whitespace_table = whitespace(usage_table['usage'])
			
			
			return render(request, "stats.html", 
						 {"usage_table" : usage_table['usage'],
						  "whitespace" : whitespace_table,
						  "net_mons" : usage_table['net_mons'],
						  "net_replays" : usage_table['net_replays'],
						  "missing":missing,
						  "tier_label":tier_label})
			
		else:
			start = request.POST["start"]
			end = request.POST["end"]
			url = request.POST["url"]
			rng = range(int(start), int(end))
			pairings = tournament.parse_pairings(url = url)
			participants = tournament.participants_from_pairings(pairings)
			tiers = ["gen7oususpecttest", "gen7ou"]
			replays = set()
			for tier in tiers:
				replays = replays | replayCompile.replays_from_range(rng, tier=tier) 
			tour = tournament.Tournament(
				   replays, pairings,
				   participants)
			replays = tour.match_tournament()
			request.session["replays"] = replays | tour.unmatchedReplays
			print request.session["replays"]
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
							  else ((str(pairing).strip("frozenset")), 
							  "", "", "no match") 
							  for pairing in pairings],
				"unmatched_replays":tour.unmatchedReplays
		})