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
		if "thread_submit" in request.POST:
			url = request.POST["url"]
			replays = replayCompile.replays_from_thread(url)
		if "range_submit" in request.POST:
			if not request.POST["tier"]:
				tier = "gen7pokebankou"
			else:
				tier = request.POST["tier"]
			replays = replayCompile.replays_from_range(
			range(int(request.POST["start"]),int(request.POST["end"])),
			tier = tier)
		
		# Stats
		usage = statCollector.usage(replays)
		wins = statCollector.wins(replays)
		total = (sum(usage.values())/6)
		
		# API request to match Pokemon w/dex number corresponding to sprite filename

		usage_table = [(element[0], 
						element[1], 
						"{0:.2f}%".format(100 * float(element[1])/total),
						"{0:.2f}%".format(100 * float(wins[element[0]])/element[1]),
						)
						for element in usage.most_common()]
						
		whitespace_table = [(
						entry[0] + " " * (18 - len(entry[0])), 
						str(entry[1]) + " " * (3 - len(str(entry[1]))), 
						str(entry[2]) + " " * (6 - len(str(entry[2]))),
						str(entry[3]) + " " * (7 - len(str(entry[3]))),
						str(i+1) + " " * (4-len(str(i+1)))
						)
						for i, entry in enumerate(usage_table)]
		'''
		whitespace = [(
					  " " * (22 - len(entry[0])),
					  " " * (3 - len(str(entry[1]))),
					  " " * (3 - len(str(entry[2]))),
					  " " * (3 - len(str(entry[3])))
					  ) for entry in usage_table]'''
					  
		return render(request, "stats.html", {"usage_table" : usage_table,
											  "whitespace" : whitespace_table})


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