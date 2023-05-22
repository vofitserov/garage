#!/usr/bin/env python3

import signal
import sys
import time
import traceback
import logging

from config import *
from door import *
from httpserver import *
from telegramdoor import *

# Named global logger from config
logger = logging.getLogger("garage")


class GarageDaemon:
    def __init__(self):
        return
    
    def run(self, test = False):
        # signal handler can be set only in main thread
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)

        self.door = GarageDoor()

        self.httpserver = HTTPDoorController(self.door)
        self.httpserver.setDaemon(True)
        self.httpserver.start()

        self.httpwatcher = HTTPDoorWatcher()
        self.httpwatcher.setDaemon(True)
        self.httpwatcher.start()

        self.bot = TelegramDoorController(self.door)
        self.bot.setDaemon(True)
        self.bot.start()


        # join() with is_alive() is only way catch signals
        while self.httpserver.is_alive():
            self.httpserver.join(10)
            if test: break
            pass

        logger.critical("starting server shutdown")
        self.httpserver.shutdown()
        logger.critical("starting telegram bot shutdown")
        self.bot.shutdown()
        logger.critical("staring door shutdown, gpio cleanup")
        self.door.shutdown()
        time.sleep(10)
        logger.critical("the end")
        return

    def shutdown(self, signum, frame):
        logger.critical("starting shutdown by %d" % signum)
        self.httpserver.shutdown()
        logger.critical("finished shutdown by %d" % signum)
        return


def main(argv):
    test = "test" in argv or "unittest" in sys.modules
    if not test:
        handler = logging.handlers.RotatingFileHandler(LOGFILE, maxBytes=100000, backupCount=5)
        logger.addHandler(handler)
        logger.info("logging to " + LOGFILE)
    else:
        logger.info("running in test mode, logging to stderr only")
        pass
    try:
        garage_daemon = GarageDaemon()
        garage_daemon.run(test)
    except Exception as e:
        logger.error("failed: \"%s\"" % str(e))
        return -1
    return 0


if __name__ == '__main__':
    main(sys.argv)
