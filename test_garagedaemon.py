import unittest
from mock import MagicMock
from mock import patch

MockRPi = MagicMock()
MockLogging = MagicMock()
MockTime = MagicMock()
modules = {
    "RPi": MockRPi,
    "RPi.GPIO": MockRPi.GPIO,
#    "logging" : MockLogging,
#    "logging.handlers" : MockLogging.handlers,
#    "logging.handlers.RotatingFileHandler" : MockLogging.handlers.RotatingFileHandler,
    "time" : MockTime
}

patcher = patch.dict("sys.modules", modules)
patcher.start()

import garagedaemon
import config
import RPi.GPIO as GPIO

class TestGarageDaemon(unittest.TestCase):
    def setUp(self):
        MockRPi.GPIO.input.return_value = 0
        MockTime.time.return_value = 10000000
        config.HTTP_HOST = "localhost"
        config.HTTP_PORT = 8080
        config.LOGFILE = "garagedaemon.log"
        return

    def runTest(self):
        garagedaemon.main(["test", "test"])
        MockRPi.GPIO.setmode.assert_called_once_with(GPIO.BCM)
        return

    def tearDown(self):
        return

if __name__ == '__main__':
    unittest.main()
