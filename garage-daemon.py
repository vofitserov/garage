#!/usr/bin/env python3

import signal
import sys
import traceback
import logging

from daemon import runner

from config import *
from door import *
from httpserver import *
from twitterserver import *
from tesla import *

# Named global logger from config
logger = logging.getLogger("garage")

class GarageDaemon:
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/var/log/garage-daemon.out'
        self.stderr_path = '/var/log/garage-daemon.err'
        self.pidfile_path = PIDFILE
        self.pidfile_timeout = 10
        return
    
    def run(self):
        # signal handler can be set only in main thread
        signal.signal(signal.SIGTERM, self.shutdown)    
        signal.signal(signal.SIGINT, self.shutdown)    

        self.door = GarageDoor()
        self.garage = TeslaGarage(TESLA_CREDS)
        
        self.httpserver = HTTPDoorController(self.door)
        self.httpserver.setDaemon(True)
        self.httpserver.start()

        self.httpwatcher = HTTPDoorWatcher()
        self.httpwatcher.setDaemon(True)
        self.httpwatcher.start()
        
        # Twitter Streaming API is discountinued.
        self.twitterserver = TwitterStreamer(self.door, self.garage)
        self.twitterserver.setDaemon(True)
        self.twitterserver.start()

        self.twitternotifier = TwitterNotifier(self.door)
        self.twitternotifier.setDaemon(True)
        self.twitternotifier.start()

        # join() with is_alive() is only way catch signals
        while self.httpserver.is_alive():
            self.httpserver.join(2**31)
            pass
            
        logger.critical("staring door shutdown, gpio cleanup")
        self.door.shutdown()
        return

    def shutdown(self, signum, frame):
        logger.critical("starting shutdown by %d" % signum)
        self.httpserver.shutdown()
        logger.critical("finished shutdown by %d" % signum)
        return
    
try:
    garage_daemon = GarageDaemon()
    if sys.argv[1] == "test":
        stderrHandler = logging.StreamHandler(sys.stderr)
        logger.addHandler(stderrHandler)
        logger.info("running in test mode, logging to stderr")
        garage_daemon.run()
    else:
        daemon_runner = runner.DaemonRunner(garage_daemon)
        daemon_runner.daemon_context.files_preserve = [handler.stream]
        daemon_runner.do_action()
        pass
    
except Exception as e:
    logger.error("failed: \"%s\"" % str(e))
    pass

