""" Module used to generate stats for weekly tournament circuit. """

import replay_compile
import statCollector
import tournament
import profile

""" List of known alternate accounts. Fed as input to ensure proper matching."""

alts = {"frenzied":"toxzn", 
		"plasma boss":"toxzn",
		"freezing gene":"flamingvictini",
		"stolen sentiments":"flamingvictini",
		"alepipluprevenge":"prague kick",
		"time between us":"aruyre",
		"natoo06":"welli0u",
		"mushmunkey":"zepherox",
		"gorgie":"floppy",
		"wrist game kobe":"pdc",
		"dans la legende":"welli0u",
		"eternal god zamasu":"blackoblivion",
		"sorrowinthenight":"empo",
		"sm hero eternal":"eternal spirit",
		"went down spinning":"mael",
		"testiclebasket":"toxzn",
		"assasin hit":"blackoblivion",
		"how to be sure":"mael",
		"secret vulpix":"-snow",
		"costa":"c05ta",
		"eo":"eo ut mortus",
		"sperl":"axel\xe2\x84\xa2"
		}
		
""" URLs, replay ranges, and replays to be omitted for each individual tournament, with indices corresponding to tournament number.
"""

urls = [
"http://www.smogon.com/forums/threads/ou-circuit-week-1-saturday"
"-won-by-tokyo-tom.3587889/",
"http://www.smogon.com/forums/threads/ou-circuit-week-1-sunday"
"-won-by-mix.3587954/",
"http://www.smogon.com/forums/threads/ou-circuit-week-2-saturday"
"-won-by-praj-pran.3588603/",
"http://www.smogon.com/forums/threads/ou-circuit-week-2-sunday"
"-won-by-rare-poison.3588678/",
"http://www.smogon.com/forums/threads/ou-circuit-week-3-saturday"
"-won-by-updated-kanto.3589343/",
"http://www.smogon.com/forums/threads/ou-circuit-week-3-"
"sunday-won-by-praj-pran.3589417/",
"http://www.smogon.com/forums/threads/ou-circuit-week-4-saturday"
"-won-by-specterito.3589993/",
"http://www.smogon.com/forums/threads/ou-circuit-week-4-sunday-"
"won-by-flcl.3590052/"]
	
ranges = [xrange(217028,217106), xrange(217387,217476), xrange(219328,219468),
		  xrange(219962,220073), xrange(222612,222710), xrange(223116,223193),
		  xrange(224853,224951), xrange(225295,225365)]

omissions = [None, (217448, 217469), None, None, None, (223142, 223148),
			 None, (225301,)]

def tour(url = None, rng = None, omitReplays = None):
	""" Parse thread URL for tour pairings and match to replays in range.
	
	Additional "omitReplays" argument specifies which replays, if any, should be
	discluded from the range. This is to be done in the event of multiple
	replays featuring the same two players, in which case the replay to be
	counted for the tournament is indeterminable without further
	scrutinization.
	"""
	
	pairings = tournament.parse_pairings(url = url)
	players = tournament.participants_from_pairings(pairings)
	replays = replay_compile.replays_from_range(rng)
	tour = tournament.Tournament(replays, pairings, players, alts)
	if omitReplays:
		tour.filter_replays_by_number(*omitReplays)
	return tour.match_tournament()
	

def basic_stats(replay_list):
	""" Function to calculate and print out basic stats. """
	usage = statCollector.usage(replay_list)
	wins = statCollector.wins(replay_list)
	totalTeams = (sum(usage.values())/6)
	statCollector.pretty_print("Pokemon", 18, usage,wins,totalTeams)
	
def extended_stats(replay_list, usage = None):
	""" Function to calculate and print out extended stats. """
	if not usage:
		usage = statCollector.usage(replay_list)
	
	# Combinations
	combos = statCollector.combos(replay_list, cutoff = 5)
	combowins = statCollector.combo_wins(replay_list)
	for i in xrange(2,7):
		combos = statCollector.combos(replay_list, size = i, cutoff = 4)
		combowins = statCollector.combo_wins(replay_list, size = i)

		length = len(sorted(combos, key=len, reverse = True)[0]) + 2
		statCollector.pretty_print("Combinations of "+str(i), length,
									combos,combowins,totalTeams)

	# Moves
	moves = statCollector.moves(replay_list, usage.keys())
	move_wins = statCollector.move_wins(replay_list, usage.keys())

	for pokemon in usage.most_common():
		statCollector.pretty_print(pokemon[0], 22, 
		moves[pokemon[0]], move_wins[pokemon[0]], usage[pokemon[0]], hide = 1)


def main():
	# Net stats
	netResults = [tour(urls[i], ranges[i], omissions[i]) for i in xrange(0,8)]
	[basic_stats(netResults[i] | netResults[i+1]) for i in xrange(0,8,2)]
	RL = reduce((lambda x,y: x|y), netResults)
	basic_stats(RL)
	#printout(RL)

if __name__ == "__main__":
	#main()
	profile.run('main()')