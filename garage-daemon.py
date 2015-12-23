#!/usr/bin/env python

from daemon import runner

from config import *
from door import *
from httpserver import *

# Named global logger from config
logger = logging.getLogger("garage")

class GarageDaemon:
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/var/log/garage-daemon.out'
        self.stderr_path = '/var/log/garage-daemon.err'
        self.pidfile_path = PIDFILE
        self.pidfile_timeout = 5
        return
    
    def run(self):
        try:
            door = GarageDoor()
            logger.info("starting HTTP server: %s:%d" % (HTTP_HOST, HTTP_PORT))
            server = HTTPDoorServer(door, ("", HTTP_PORT), HTTPDoorHandler)
            server.serve_forever()
        except Exception as e:
            logger.error("failed to start server: \"%s\"" % str(e))
        return

garage_daemon = GarageDaemon()
garage_daemon.run()

#daemon_runner = runner.DaemonRunner(garage_daemon)
#daemon_runner.daemon_context.files_preserve = [handler.stream]
#daemon_runner.do_action()

