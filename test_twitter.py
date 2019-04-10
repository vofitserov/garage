
import unittest
from mock import patch
from mock import MagicMock

MockLogging = MagicMock()
MockDoor = MagicMock()
MockDoorModule = MagicMock()

modules = {
    "door" : MockDoorModule,
    "logging" : MockLogging,
    "logging.handlers" : MockLogging.handlers,
}

patcher = patch.dict("sys.modules", modules)
patcher.start()

import config
config.TWITTER_CREDS = "twitter.oauth"

from twitterserver import *

class TestTwitterSteamer(unittest.TestCase):
    def setUp(self):
        self.twitterstreamer = TwitterStreamer(MockDoor)
        return

    def runTest(self):
        self.twitterstreamer.listen()
        return

    def tearDown(self):
        self.twitterstreamer = None
        return

# class TestTwitterNotifier(unittest.TestCase):
#     def setUp(self):
#         MockDoor.check.return_value = True
#         MockDoor.notify.return_value = True
#         MockDoor.message.return_value = "test"
#         self.twitternotifier = TwitterNotifier(MockDoor)
#         return
#
#     def runTest(self):
#         self.twitternotifier.notify()
#         return
#
#     def tearDown(self):
#         self.twitternotifier = None
#         return

if __name__ == '__main__':
    unittest.main()
