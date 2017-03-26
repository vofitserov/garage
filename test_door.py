
import unittest
from mock import MagicMock
from mock import patch

MockRPi = MagicMock()
MockLogging = MagicMock()
MockTime = MagicMock()
modules = {
    "RPi": MockRPi,
    "RPi.GPIO": MockRPi.GPIO,
    "logging" : MockLogging,
    "logging.handlers" : MockLogging.handlers,
    "time" : MockTime
}

patcher = patch.dict("sys.modules", modules)
patcher.start()

from door import *

class TestGarageDoor(unittest.TestCase):
    def setUp(self):
        MockRPi.GPIO.input.return_value = 0
        MockTime.time.return_value = 10000000
        self.door = GarageDoor()
        return

    def runTest(self):
        MockRPi.GPIO.setmode.assert_called_once_with(GPIO.BCM)
        self.assertFalse(self.door.check())
        status = self.door.status()
        print status
        self.assertEqual(status, "door was closed 10000000 secs ago")
        return

    def tearDown(self):
        self.door.shutdown()
        self.door = None
        return

if __name__ == '__main__':
    unittest.main()
