import os

from django.test import TestCase
from rsite import views
from rsite.replay_parser import replay_compile
from rsite.replay_parser.replay import Log, Replay

class ReplayTest(TestCase):

	def __init__(self, *args, **kwargs):
		super(TestCase, self).__init__(*args, **kwargs)
		self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))

		# Replay 1
		log = Log(open(os.path.join(self.BASE_DIR, "mock_replay1.txt"), "r").readlines())
		self.replay1 = replay_compile.initialize_replay(log)
	
	def test_players(self):
		self.assertEqual(self.replay1.players[0], "get backer")
		self.assertEqual(self.replay1.players[1], "crashinboombang")
	
	def test_winner(self):
		self.assertEqual(self.replay1.winner, "get backer")
	
	def test_set_winner(self):
		self.replay1.winner = "crashinboombang"
		self.assertEqual(self.replay1.winner, "crashinboombang")
		self.assertEqual(self.replay1.loser, "get backer")
		
		# Tie
		self.replay1.winner = ""
		self.assertEqual(self.replay1.winner, "")
		self.assertEqual(self.replay1.loser, "")
		
		# Invalid winner
	
	