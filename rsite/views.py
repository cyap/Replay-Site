from itertools import chain
from collections import Counter
import re
import datetime

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import RequestContext
from django.views.decorators.csrf import ensure_csrf_cookie

from .forms import ThreadForm, RangeForm, OptionsPane
from .replay_parser import replay_compile, stats, tournament, replay

from rq import Queue
from worker import conn

q = Queue(connection=conn)
result = []

TIERS = ["RBY","GSC","ADV","DPP","BW","ORAS","SM"]
COL_WIDTH = 23
	
def index(request):
	if request.method == "GET":
		# Forms
		thread_form = ThreadForm(auto_id=True)
		range_form = RangeForm()
		options_pane = OptionsPane()
		return render(request, "index.html", {
			"thread_form":thread_form,
			"range_form":range_form,
			"options_pane":options_pane
		})
		
	if request.method == "POST":
		# Check from which form
		
		# Resubmission
		if "rep_submit" in request.POST:
		
			# For calls made from tournament_matching page
			replays = replay_compile.replays_from_links(
				request.POST.getlist("replay_urls"))

		elif "resubmit" in request.POST:
			# For calls made from resubmission page

			# Replays resubmitted via form
			saved_replay_urls = set(request.POST.getlist("replay_urls"))
			
			# Designate changed results in HTML (i.e. change name)
			modified_replay_urls = set(request.POST.keys())
			
			# TODO:
			# aesthetics
			# name to designate winner
			# (eventual) trigger flag based on modification: alternating class?
			
			# 2. Exclude from list (and not in changed_replays)
			replays = []
			for replay in request.session["replays"]:
				if replay.url.strip() in saved_replay_urls:
					if replay.url in modified_replay_urls:
					# Reconstruct Replay objects with new winner
						pnum = int(request.POST[replay.url])
						replay.winner = replay.players[pnum-1] if pnum else ""
					replays.append(replay)
			
			# Newly submitted replays
			# TODO: refactor to use new method
			
			urls = request.POST["new_urls"].splitlines()
			logs = replay_compile.logs_from_links(urls)
			request.POST = request.session["form"]

		else:
			# Thread Form
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
						range=range(int(start), int(end)), 
						tier=tier,
						server=server
						)
						for start, end, tier, server in zip(
							request.POST.getlist("range_start"),
							request.POST.getlist("range_end"),
							request.POST.getlist("range_tiers"),
							request.POST.getlist("server")))))
			# Links
			urls = request.POST["replay_urls"].splitlines()
			link_logs = replay_compile.logs_from_links(urls)
						
			logs = thread_replays + range_replays + link_logs
			
			replays = []
			
		if "rep_submit" not in request.POST:
			invalid_replays = "\n".join(set(urls) - {log.url for log in logs})
			print(invalid_replays)
		
			for log in logs:
				try:
					replay = replay_compile.initialize_replay(log, log.url)
					if replay:
						replays.append(replay)
				except replay_compile.NoWinnerError:
					# No winner: Default to tie
					replay = replay_compile.initialize_replay(log, log.url, wnum=0)
					# TODO: refactor to handle no player error
					if replay:
						replays.append(replay)
				except replay_compile.NoPlayerError:
					# no players
					pass
		else:
			invalid_replays = []
		
			
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
		ties = [replay for replay in replays if not replay.winner]
		
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
		missing_text = ""
		for replay in replays:
			for num, player in enumerate(("p1", "p2")):
				if len(replay.teams[player]) < 6:
					missing_text += ("[*][I]Missing {0} Pokemon from {1}.[/I]\n"
					.format(6-len(replay.teams[player]), replay.players[num]))
		# Refactor - players.keys()

		if missing_text:
			missing_text = "\n[LIST]\n" + missing_text + "[/LIST]"
		
		# Usage rawtext
		usage_whitespace = (sprite_header + "\n[CODE]\n" +
			stats.pretty_print("Pokemon", 18, usage, wins, total)
			+ "[/CODE]" + missing_text)
			
		# Advanced stats
		
		# Moves
		if "moves_check" in request.POST:
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
			teammates_rows = {
				pokemon:stats.generate_rows(
					teammates.get(pokemon, Counter()),
					teammate_wins.get(pokemon, Counter()), 
					uses)
				for pokemon, uses in usage.most_common()}
			
			# Refactor to allow for customizable column name
			#usage_dict = {}
			#for row in usage_table:
				#usage_dict[row[1]] = row
			usage_formatted = list(stats.generate_rows(
				usage, wins, total, lambda x: "["+x+"]"))
			usage_dict = {pokemon[1]: row 
				for row, pokemon in zip(usage_formatted, usage_table)}
			
			moves_whitespace = "\n\n".join(
				stats.print_table("Pokemon", COL_WIDTH, [usage_dict[pokemon]]) 
				+ "\n"
				+ stats.print_table("Moves", COL_WIDTH, move_rows.get(
					pokemon, [])) + "\n"
				+ stats.print_table("Teammates", 
					COL_WIDTH, teammates_rows[pokemon])
				for i, (pokemon, uses) in enumerate(usage.most_common())
				) #if pokemon in move_rows)

		else:
			moves_whitespace = ""

		# Items
		
		# Leads
		
		if "leads_check" in request.POST:
			# Change to tier from replay
			format = "DOUBLES" in tier_label
			leads = stats.aggregate_forms(
				stats.leads(replays), gen_num, True)
			lead_wins = stats.aggregate_forms(
				stats.lead_wins(replays), gen_num, True)
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
		else:
			leads_rawtext = ""
		
		combos_rawtext = ""
		if "combos_check" in request.POST:
		 
			# Combos
			for i in range(2,7):
				try:
					combos = stats.combos(replays, i, 
						float(request.POST["cutoff"])/100 * total)
				except:
					combos = stats.combos(replays, i)
				
				if "numeric_cutoff" in request.POST:
					try:
						cutoff = combos.most_common()[
							int(request.POST["numeric_cutoff"])-1][1]
						#cutoff = combos.most_common()[
						#	min(len(combos.most_common()), 100)][1]
						combos = Counter(
							{combo:use for combo,use in combos.items() 
							if use >= cutoff})
					except:
						pass
						#combos = stats.combos(replays, i, 0.02 * total)
				
				combo_wins = stats.combo_wins(replays, i)
				rows = list(stats.generate_rows(
					combos, combo_wins, total, stats.format_combo2))
				longest = len(max([row.element for row in rows],
					key=str.__len__, default="Thundurus-Therian"))
				combos_rawtext += (
					stats.print_table("Combos of " + str(i), longest, rows) 
					+ "\n\n")

		# Replay pane
		pairings = [(replay, replay.players[0] 
				   + " vs. " 
				   + replay.players[1])
				   for replay in replays]
		
		replay_rawtext = "\n".join(replay.url for replay in replays)
		
		# Caching
		request.session["form"] = request.POST
		request.session["replays"] = replays
		
		return render(request, "stats.html", 
					 {"usage_table":usage_table,
					  "net_mons":sum(usage.values()),
					  "net_replays":len(replays),
					  "tier_label":tier_label,
					  "moves_whitespace":moves_whitespace,
					  "usage_whitespace":usage_whitespace,
					  "pairings":pairings,
					  "combos_rawtext":combos_rawtext,
					  "leads_rawtext":leads_rawtext,
					  "replay_rawtext":replay_rawtext,
					  "invalid_replays":invalid_replays,
					  })
					  

def spl_index(request):
	if request.method == "GET":
		return render(request, "spl_index.html")
		
	if request.method == "POST":
		moves_tables = []
		if "link_submit" in request.POST:
			urls = request.POST["replay_urls"].splitlines()
			replays = replay_compile.replays_from_links(urls)
			choice = None
			template = "spl_stats.html"

			raw = ""
			for replay in replays:
				for player in replay.players:
					raw += (player + ":\n")
					for pokemon in replay.teams[replay.name_to_num(player)]:
						raw += (pokemon + ": ")
						raw += " / ".join(replay.moves[player].get(pokemon, [])) + "\n"
					raw += "\n"
			
			moves = [replay.moves for replay in replays]
			
			# Unpack dicts
			
			# [{p1:{pokemon:{moves}}}]
			'''
			for replay in replays:
				for player in replay.players:
					movesets = replay.moves[replay.name_to_num(player)].items()
					moves_tables.append({player: movesets})'''
			for replay in replays:
				table = {}
				match = {replay.url:table}
				for player in replay.players:
					movesets = replay.moves[replay.name_to_num(player)].items()
					table[player] = movesets
				moves_tables.append(match)

			#print(moves_tables)
			pairings = None
			usage_whitespace = ""
			
		else:
			tier = request.POST["tier"]
			player = request.POST["player"].split("[self]")[0].strip().upper()
			replays = replay_compile.replays_from_user(player, tier=tier)
			
			pairings = []
			moves = []
			choice = player
			for i, replay in enumerate(replays):
				try:
					player_num = replay.name_to_num(player)
				except:
					# Breaks if player name has special characters
					exp = re.compile(".*?".join(player))
					for p in replay.players:
						if exp.match(p):
							replay._players[player] = replay._players[p]
					# One-time case where replay mapped to two completely different players
					try:
						player_num = replay.name_to_num(player)
					except:
						replays[i] = None
						continue


				move_list = replay.moves.get(player_num)
				pairing = {"replay":replay, "moves":move_list}
				moves.append(move_list)
				pairings.append(pairing)

			replays = list(filter(None, replays))

			template = "scout_stats.html"
			
			gen_num = next((char for char in min(request.POST["tier"]) if char.isdigit()), 6)
			usage = stats.aggregate_forms(stats.usage2(replays, choice),
					gen_num, True)

			wins = stats.wins2(replays, choice)
			total = len(replays)
			
			usage_whitespace = stats.pretty_print("Pokemon", 18, usage, wins, total)
			
			
			raw = (
			"\n\n---\n\n".join([
			choice + "\n"
			+ "\n".join([pokemon + ": " 
			+ " / ".join([
			move for move in 
			(replay.moves.get(replay.name_to_num(choice)))[pokemon]])
			for pokemon in replay.moves.get(replay.name_to_num(choice))])
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
					"moves_tables":moves_tables,
					"pairings":pairings,
					"choice":choice,
					"usage_whitespace":usage_whitespace})

def tour_worker(request):
	if request.method == "GET":
		return render(request, "indextour.html")
	elif request.method == "POST":
		url = request.POST["url"]
		rng = range(int(request.POST["start"]),int(request.POST["end"]))
		tier = request.POST["tier"]
		#tour_match.delay(rng, url, tier)
		return render(request, "buffer.html")
		
		#return render(request, "indextour.html")
	#q = Queue(connection=conn)
	#result = q.enqueue(tour_index, request)
	#return render(request, "indextour.html")
	
def tour_match(range, url, tier):
	pairings = tournament.parse_pairings(url=url)
	participants = tournament.participants_from_pairings(pairings)
	replays = sum((replay_compile.replays_from_range(rng, tier=tier) 
		for tier in tier.split(",")), [])
	replays2 = []
	for replay in replays:
		try:
			rep = replay_compile.initialize_replay(replay, replay.url)
			if rep:
				replays2.append(rep)
		except:
			pass
	replays = replays2
	tour = tournament.Tournament(set(replays), pairings, participants)
	replays = tour.match_tournament()
	matches = tour.pairingReplayMap
	unmatched_replays = tour.unmatchedReplays
	
		
	# Replays
	formatted_matches = [(" vs. ".join(player for player in pairing),
						 matches[pairing][0], # replay
						 matches[pairing][1]) # filter
						 if pairing in matches
						 else 
						 (" vs. ".join(player for player in pairing),
						  "", "no match")
						 for pairing in pairings]
	options_pane = OptionsPane()
	return render(request, "tour_match.html", {
		"start":start,
		"end":end+1,
		"url":url,
		"participants" : participants,
		"matches" : formatted_matches,
		"unmatched_replays":unmatched_replays,
		"options_pane":options_pane,
	})

def tour_index(request):	
	if request.method == "GET":
		return render(request, "indextour.html")

	elif request.method == "POST":
		url = request.POST["url"]
		rng = range(int(request.POST["start"]),int(request.POST["end"]))

		# Cached
		if False:
			pass
		#if (url in request.session and request.session[url].get("range") == rng
		#and "clear" not in request.POST):
		#	participants = request.session[url]["participants"]
		#	pairings = request.session[url]["pairings"]
		#	matches = request.session[url]["matches"]
		#	unmatched_replays = request.session[url]["unmatched_replays"]
		#	replays = request.session[url]["replays"]

		else:
			# Not cached
			pairings = tournament.parse_pairings(url=url)
			participants = tournament.participants_from_pairings(pairings)
			server = request.POST["server"]
			replays = sum((replay_compile.replays_from_range(rng, tier=tier, server=server) 
				for tier in request.POST["tier"].split(",")), [])
			replays2 = []
			for replay in replays:
				try:
					rep = replay_compile.initialize_replay(replay, replay.url)
					if rep:
						replays2.append(rep)
				except:
					pass
			replays = replays2
			
	# Caching
	
	# minus start date
	key = ''.join(map(str, datetime.datetime.now().timetuple()))
	
	request.session[url] = {}
	request.session[key] = {}
	request.session[key]['url'] = url
	request.session[key]["range"] = rng
	request.session[key]["pairings"] = pairings
	request.session[key]["replays"] = replays
	request.session[key]["participants"] = participants
	return redirect('/buffer?key=' + key)
	
def buffer(request):

	key = request.GET['key']
	url, rng, pairings, replays, participants = (request.session[key]['url'],
		request.session[key]['range'], 
		request.session[key]['pairings'], 
		request.session[key]['replays'],
		request.session[key]['participants'])
		
	# return buffer
	tour = tournament.Tournament(set(replays), pairings, participants)
	replays = tour.match_tournament()
	matches = tour.pairingReplayMap
	unmatched_replays = tour.unmatchedReplays

	# Caching
	request.session[url]["matches"] = matches
	request.session[url]["unmatched_replays"] = unmatched_replays
	
	# Replays
	request.session["replays"] = replays | unmatched_replays

	formatted_matches = [(" vs. ".join(player for player in pairing),
						 matches[pairing][0], # replay
						 matches[pairing][1]) # filter
						 if pairing in matches
						 else 
						 (" vs. ".join(player for player in pairing),
						  "", "no match")
						 for pairing in pairings]
	options_pane = OptionsPane()
	return render(request, "tour_match.html", {
		#"start":request.POST["start"],
		#"end":request.POST["end"],
		#"url":request.POST["url"],
		'start': rng[0],
		'end': rng[-1],
		'url': url,
		"participants" : participants,
		"matches" : formatted_matches,
		"unmatched_replays":unmatched_replays,
		"options_pane":options_pane,
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
	matched_replays = [replay for replay in request.session["replays"] 
		if replay.url in matched_urls]
	
	# Change such that only URLs are being passed to the template
	
	request.session[url]["matches"] = {pairing: (replay, filter) for pairing, replay, filter in zip(request.POST.getlist("pairings[]"), matched_replays, request.POST.getlist("filters[]"))}
	#request.session.save()
	
	return HttpResponse('ok')
	
def update_stats(request):
	if not request.is_ajax() or not request.method=='POST':
		return HttpResponseNotAllowed(['POST'])
	return HttpResponse('ok')