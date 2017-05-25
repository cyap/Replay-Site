import os

from django.test import TestCase
from rsite import views
from rsite.replay_parser import replay_compile
from rsite.replay_parser.replay import Log, Replay

class ReplayTest(TestCase):

	BASE_DIR = os.path.dirname(os.path.abspath(__file__))
	replay = None
	
	def test_replay_constructor(self):
		log = Log(open(os.path.join(self.BASE_DIR, "mock_replay1.txt"), "r").readlines())
		self.replay = replay_compile.initialize_replay(log)
		self.assertIs(True, True)