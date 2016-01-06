#!/usr/bin/env python

import signal

from daemon import runner

from config import *
from door import *
from httpserver import *
from twitterserver import *

# Named global logger from config
logger = logging.getLogger("garage")

def shutdown_handler(signum, frame):
    logger.critical("starting shutdown by %d" % signum)
    garage_daemon.shutdown()
    logger.critical("finished shutdown by %d" % signum)
    return

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
        signal.signal(signal.SIGTERM, shutdown_handler)    
        signal.signal(signal.SIGINT, shutdown_handler)    

        self.door = GarageDoor()
        
        self.httpserver = HTTPDoorController(self.door)
        self.httpserver.setDaemon(True)
        self.httpserver.start()

        self.twitterserver = TwitterServer(self.door)
        self.twitterserver.setDaemon(True)
        self.twitterserver.start()

        self.twitternotifier = TwitterNotifier(self.door)
        self.twitternotifier.setDaemon(True)
        self.twitternotifier.start()

        # join() with is_alive() is only way catch signals
        while self.httpserver.is_alive():
            self.httpserver.join(2**31)
            pass
            
        self.door.shutdown()
        return
    
    def shutdown(self):
        self.httpserver.shutdown()
        return

try:
    garage_daemon = GarageDaemon()

    #garage_daemon.run()

    daemon_runner = runner.DaemonRunner(garage_daemon)
    daemon_runner.daemon_context.files_preserve = [handler.stream]
    daemon_runner.do_action()
except Exception as e:
    logger.error("failed: \"%s\"" % str(e))
    pass

