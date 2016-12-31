from django.http import HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.shortcuts import redirect

from replay_parser import replayCompile, statCollector
#replayCompile
#import statCollector

def index(request):
	if request.method == "GET":
		return render(request, "index.html")
		
	if request.method == "POST":
		urls = request.POST["replay_urls"].split("\n")
		replays = replayCompile.replays_from_links(urls)
	
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
		return render(request, "spl_stats.html", {
					"usage_table" : usage_table,
					"whitespace" : whitespace_table,
					"replays" : replays})
		#for replay in replays:
	'''
	- Enter list of URLs
	- Return:
		- URL: URL
		- Player1: Team, Moves
		- Player2: Team, Moves
			- Refactor replay to decide player name
			- Refactor tour matching to call format method
	- Overall:
		- Usage stats
			- Pokemon used
			- Combinations used'''



def usage(replays):
	usage = statCollector.usage(replays)
	wins = statCollector.wins(replays)
	total = (sum(usage.values())/6)
	return [(element[0], 
			 element[1], 
			 "{0:.2f}%".format(100 * float(element[1])/total),
			 "{0:.2f}%".format(100 * float(wins[element[0]])/element[1]),
			 )
			 for element in usage.most_common()]

def whitespace(usage_table):
	return [(
			entry[0] + " " * (18 - len(entry[0])), 
			str(entry[1]) + " " * (3 - len(str(entry[1]))), 
			str(entry[2]) + " " * (6 - len(str(entry[2]))),
			str(entry[3]) + " " * (7 - len(str(entry[3]))),
			str(i+1) + " " * (4-len(str(i+1)))
			)
			for i, entry in enumerate(usage_table)]
	
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