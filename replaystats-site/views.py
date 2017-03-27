from itertools import groupby, chain, repeat
from collections import Counter
import operator
import re
import profile

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import RequestContext

from replay_parser import replay_compile, stats, tournament, circuitTours

AGGREGATED_FORMS = {"Arceus-*", "Pumpkaboo-*", "Gourgeist-*", "Rotom-Appliance"}
TIERS = ["RBY","GSC","ADV","DPP","BW","ORAS","SM"]
COL_WIDTH = 23

def index2(request):
	profile.runctx('index2(request)', globals(), locals(), sort="tottime")
	#return index2(request)
	return render(request, "index.html")
	
def index(request):
	if request.method == "GET":
		return render(request, "index.html")
		
	if request.method == "POST":
		# Check from which form
		
		# Resubmission
		if "resubmit" in request.POST or "rep_submit" in request.POST:
			# Save new replays
			replays = replay_compile.replays_from_links(
				request.POST.getlist("replay_urls"))
				
			# TODO: Change to saving replay objects and filtering
			if "resubmit" in request.POST:				
				request.POST = request.session["form"]
			
			print request.POST.getlist("replay_urls")
			
		else:
			# Thread
			thread_replays = list(
				chain.from_iterable(
					(replay_compile.replays_from_thread(
						threadurl=threadurl, 
						tiers=({tier.strip() for tier in tiers.split(",")} 
								if tiers else {"gen7pokebankou"}), 
						start=int(start or 1), 
						end=int(end) if end else None)
						for threadurl, tiers, start, end in zip(
							request.POST.getlist("thread_url"),
							request.POST.getlist("thread_tiers"),
							request.POST.getlist("thread_start"),
							request.POST.getlist("thread_end")))))
			# Range
			range_replays = list(
				chain.from_iterable(
					(replay_compile.replays_from_range(
						range=range(int(start), int(end)), tier=tier)
						for start, end, tier in zip(
							request.POST.getlist("range_start"),
							request.POST.getlist("range_end"),
							request.POST.getlist("range_tiers")))))
			# Links
			link_replays = list(replay_compile.replays_from_links(
				request.POST["replay_urls"].split("\n")))
			
			# Aggregate replays
			#replays = thread_replays | link_replays | range_replays
			replays = thread_replays + link_replays + range_replays
			
		# Refactor
		tiers = {tier.strip() for tier in 
				 request.POST.get("thread_tiers", "gen7pokebankou")
				 .split(",")}
		
		# Tier
		# move to replays
		try:
			gen_num = next((char for char in min(tiers) if char.isdigit()), 6)
			name = min(tiers).split(gen_num)[1].split("pokebank")[-1].upper()
			tier_label = TIERS[int(gen_num)-1] + " " + name
		except:
			tier_label = "???"
			
		# Usage from text
		usage_from_text = [stats.stats_from_text(submission) 
			for submission in request.POST.getlist("stats_usage")]
			
		cumulative_usage = {
			"usage": sum((d["usage"] for d in usage_from_text), Counter()),
			"wins": sum((d["wins"] for d in usage_from_text), Counter()),
			"total": sum((d["total"] for d in usage_from_text))
			}
			
		# Usage view
		usage = (stats.aggregate_forms(
					stats.usage(replays), gen_num, True) 
					+ cumulative_usage["usage"])
		wins = (stats.aggregate_forms(
					stats.wins(replays), gen_num, True) 
					+ cumulative_usage["wins"])
		total = len(replays) * 2 + cumulative_usage["total"]
		
		usage_table = list(stats.generate_rows(usage, wins, total))
		
		# Sprites
		# Throw error if no replays found
		try:
			sprite_name = usage_table[0][1].lower().replace(" ","_")
		except:
			sprite_name = "pikachu"
		sprite_header = (
			"[IMG]http://www.smogon.com/dex/media/sprites/xyicons/"
			"{0}.png[/IMG] [B]{1}[/B] "
			"[IMG]http://www.smogon.com/dex/media/sprites/xyicons/"
			"{0}.png[/IMG]"
			).format(sprite_name, tier_label)
			
		# Missing Pokemon
		missing = chain.from_iterable(
			(((replay.playerwl[wl], 6-len(replay.teams[wl])) 
			for wl in ("win","lose") if len(replay.teams[wl]) < 6) 
			for replay in replays))
		
		missing_text = "\n".join(
			"[*][I]Missing {0} Pokemon from {1}.[/I]"
			.format(miss[1], miss[0]) for miss in missing)
			
		if missing_text:
			missing_text = "\n[LIST]" + missing_text + "\n[/LIST]"
		
		# Usage rawtext
		usage_whitespace = (sprite_header + "\n[CODE]\n" +
			stats.pretty_print("Pokemon", 18, usage, wins, total)
			+ "[/CODE]" + missing_text)
		# Advanced stats
		
		# Moves
		if True:
			moves = stats.aggregate_forms(
				stats.moves(replays, usage.keys()),gen_num)
			move_wins = stats.aggregate_forms(
				stats.move_wins(replays, usage.keys()), gen_num)
				
			# From submission
			if False:
				# for each submission
				
				# Parse text -> list of {Pokemon:"usage","wins","total"}
				moves_from_text = [{
					chart.split("\n")[1].split("|")[2].strip(" "): # pokemon
					stats.stats_from_text(chart)
					for chart in re.split(
						"\\r\\n\\r\\n|\\n\\n", submission.strip())
				} for submission in request.POST.getlist("stats_moves")]
				
				# List of Pokemon parsed
				pokemon_set = set(chain.from_iterable(dict.keys() 
					for dict in moves_from_text))
				
				# Merge all dictionaries
				# List of dicts -> one dict of {Pokemon:attributes}
				cumulative_moves = {}
				for pokemon in pokemon_set:
					net_move_usage = sum((dict.get(
						pokemon, {"usage":Counter()})["usage"]
						for dict in moves_from_text), Counter())
					net_move_wins = sum((dict.get(
						pokemon, {"wins":Counter()})["wins"]
						for dict in moves_from_text), Counter())
					net_move_totals = sum((dict.get(
						pokemon, {"total":0})["total"]
						for dict in moves_from_text))
					cumulative_moves[pokemon] = {
						"usage":net_move_usage, 
						"wins":net_move_wins, 
						"total":net_move_totals
					}
					'''
					cumulative_moves[pokemon] = {
						"usage":sum((d.get("usage", Counter()) 
							for d in moves_from_text), Counter()),
						"wins":sum((d.get("wins", Counter()) 
							for d in moves_from_text), Counter()),
						"total":sum((d.get("total",0) for d in moves_from_text))
					}'''
				
				# Merge each attribute dictionary with dictionary from replays
				moves = ({key:value["usage"] 
					for key,value in cumulative_moves.iteritems()})
				move_wins = ({key:value["wins"] 
					for key,value in cumulative_moves.iteritems()})
				
			# TODO
			# Change pokemon list and total variables
			# Sort by lookup?
			#pokemon_list = usage.most_common() 
			# + ((pokemon, moves[pokemon]["total"]) for pokemon in pokemon_set)
			
			'''
			moves_whitespace = "\n".join(
				(stats.pretty_print(pokemon, COL_WIDTH, moves[pokemon],
				move_wins[pokemon], uses) for pokemon, uses 
				in usage.most_common() if moves[pokemon]))
				#in pokemon_list if moves[pokemon]))'''
			
			move_rows = {pokemon:stats.generate_rows(
				moves[pokemon], move_wins[pokemon], uses) 
				for pokemon, uses in usage.most_common() if moves[pokemon]}
			
			# Teammates
			teammates = stats.teammates(replays)
			teammate_wins = stats.teammates(replays, "win")
			teammates_rows = {pokemon:stats.generate_rows(
				teammates.get(pokemon, Counter()), teammate_wins.get(pokemon, Counter()), uses)
				for pokemon, uses in usage.most_common()}
				
			'''
			teammates_whitespace = "\n\n".join(stats.print_table(
				pokemon, COL_WIDTH, teammates_rows[pokemon]) 
				for pokemon, uses in usage.most_common() 
				if pokemon in teammates_rows)
			print teammates_whitespace
				
			
			moves_whitespace = "\n\n".join(stats.print_table(
				pokemon, COL_WIDTH, move_rows[pokemon]) 
				for pokemon, uses in usage.most_common() 
				if pokemon in move_rows)
			'''
			
			# Refactor to allow for customizable column name
			#usage_dict = {}
			#for row in usage_table:
				#usage_dict[row[1]] = row
			usage_formatted = list(stats.generate_rows(usage, wins, total, lambda x: "["+x+"]"))
			usage_dict = {pokemon[1]: row for row, pokemon in zip(usage_formatted, usage_table)}
			
			moves_whitespace = "\n\n".join(
				stats.print_table("Pokemon", COL_WIDTH, [usage_dict[pokemon]]) 
				+ "\n"
				+ stats.print_table("Moves", COL_WIDTH, move_rows.get(
					pokemon, [])) + "\n"
				+ stats.print_table("Teammates", 
					COL_WIDTH, teammates_rows[pokemon])
				for i, (pokemon, uses) in enumerate(usage.most_common())
				)
				#if pokemon in move_rows)

		else:
			moves_whitespace = ""

		# Items
		
		# Leads
		
		# Change to tier from replay
		format = "DOUBLES" in tier_label
		leads = stats.aggregate_forms(stats.leads(replays, format), gen_num, True)
		lead_wins = stats.aggregate_forms(stats.lead_wins(replays, format), gen_num, True)
		
		leads_rows = stats.generate_rows(leads, lead_wins, total)
		try:
			lead_sprite = leads_rows[0][1].lower().replace(" ","_")
		except:
			lead_sprite = "pikachu"
		sprite_header = (
			"[IMG]http://www.smogon.com/dex/media/sprites/xyicons/"
			"{0}.png[/IMG] [B]{1}[/B] "
			"[IMG]http://www.smogon.com/dex/media/sprites/xyicons/"
			"{0}.png[/IMG]"
			).format(lead_sprite, tier_label)
		leads_rawtext = (sprite_header 
			+ "\n[CODE]\n{0}[/CODE]".format(
			stats.print_table("Leads", COL_WIDTH,leads_rows)))
		
		
		# Combos
		combo_rawtext = ""
		# Change to user input
		for i in xrange(2,7):
			
			# List index error
			try:
				combos = stats.combos(replays, i)
				cutoff = combos.most_common()[
					min(len(combos.most_common()), 150)][1]
				combos = Counter({combo:use for combo,use in combos.iteritems() 
						  if use > cutoff})
			except:
				combos = stats.combos(replays, i, 0.02 * total)
				
			combo_wins = stats.combo_wins(replays, i)
			rows = list(stats.generate_rows(
				combos, combo_wins, total, stats.format_combo2))
			longest = len(max([row.element for row in rows] or ["Thundurus-Therian"], key=str.__len__))
			combo_rawtext += (
				stats.print_table("Combos of " + str(i), longest, rows) 
				+ "\n\n")

		# Replay pane
		pairings = [(replay, tournament.format_name(replay.players[0]) 
				   + " vs. " 
				   + tournament.format_name(replay.players[1]))
				   for replay in replays]
		
		replay_rawtext = "\n".join(replay.url for replay in replays)
		
		
		request.session["form"] = request.POST
		return render(request, "stats.html", 
					 {"usage_table":usage_table,
					  "net_mons":sum(usage.values()),
					  "net_replays":len(replays),
					  "missing":missing,
					  "tier_label":tier_label,
					  "moves_whitespace":moves_whitespace,
					  "usage_whitespace":usage_whitespace,
					  "pairings":pairings,
					  "combo_rawtext":combo_rawtext,
					  "leads_rawtext":leads_rawtext,
					  "replay_rawtext":replay_rawtext})

def spl_index(request):
	if request.method == "GET":
		return render(request, "spl_index.html")
		
	if request.method == "POST":
		if "link_submit" in request.POST:
			urls = request.POST["replay_urls"].split("\n")
			replays = replay_compile.replays_from_links(urls)
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
			replays = replay_compile.replays_from_user(
				request.POST["player"].replace(" ", "+"),
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
		
		# Raw original
		row_count = len(replays) * 18 - 2
		
		# Set not removing duplicates
		#return render(request, "spl_stats.html", {
		
		return render(request, template, {
					"replays" : replays,
					"raw":raw,
					"row_count":row_count,
					"moves":moves,
					"pairings":pairings,
					"choice":choice})
					
def tour_index(request):	
	if request.method == "GET":
		return render(request, "indextour.html")

	'''
	if "replay_submit" in request.POST:
			replay_urls = set(request.POST.getlist("replays"))
			print replay_urls
			replays = set(replay for replay in request.session["replays"] if replay.url in replay_urls)
	'''
	if request.method == "POST":
		url = request.POST["url"]
		rng = range(int(request.POST["start"]),int(request.POST["end"]))
	
		# Cached
		if url in request.session and request.session[url].get("range") == rng:
			participants = request.session[url]["participants"]
			pairings = request.session[url]["pairings"]
			matches = request.session[url]["matches"]
			unmatched_replays = request.session[url]["unmatched_replays"]
			replays = request.session[url]["replays"]

		else:
			# Not cached
			pairings = tournament.parse_pairings(url=url)
			participants = tournament.participants_from_pairings(pairings)
			tiers = request.POST["tier"].split(",")
			replays = []
			for tier in tiers:
				replays = (replays + 
					replay_compile.replays_from_range(rng, tier=tier))
			tour = tournament.Tournament(set(replays), pairings, participants)

			replays = tour.match_tournament()
			matches = tour.pairingReplayMap
			unmatched_replays = tour.unmatchedReplays
		
			# Caching
			request.session[url] = {}
			request.session[url]["range"] = rng
			request.session[url]["pairings"] = pairings
			request.session[url]["participants"] = participants
			request.session[url]["replays"] = replays
			request.session[url]["matches"] = matches
			request.session[url]["unmatched_replays"] = unmatched_replays
			
		# Replays
		request.session["replays"] = replays | unmatched_replays
		formatted_matches = [(str(pairing).strip("frozenset"), # pairing
							 matches[pairing][0], # replay
							 matches[pairing][1]) # filter
							 if pairing in matches
							 else 
							 (str(pairing).strip("frozenset"), "", "no match")
							 for pairing in pairings]

		return render(request, "results.html", {
			"start":request.POST["start"],
			"end":request.POST["end"],
			"url":request.POST["url"],
			"participants" : participants,
			"matches" : formatted_matches,
			"unmatched_replays":unmatched_replays
		})

def update_session(request):
	if not request.is_ajax() or not request.method=='POST':
		return HttpResponseNotAllowed(['POST'])
		
	# matches: {pairing: (replay, filter)}
	# unmatched replays: replay objects
	url = request.POST.getlist("url")[0]
	
	unmatched_replays = set(request.POST.getlist("unmatched_replays[]"))
	request.session[url]["unmatched_replays"] = set(replay for replay 
		in request.session["replays"] if replay.url in unmatched_replays)
		
	matched_urls = set(request.POST.getlist("matches[]"))
	print "urls:", matched_urls
	matched_replays = [replay for replay in request.session["replays"] 
		if replay.url in matched_urls]
	
	# Change such that only URLs are being passed to the template
	
	#print matched_replays
	request.session[url]["matches"] = {pairing: (replay, filter) for pairing, replay, filter in zip(request.POST.getlist("pairings[]"), matched_replays, request.POST.getlist("filters[]"))}
	#print request.session[url]["matches"]
	#request.session.save()
	
	return HttpResponse('ok')