
from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer
from SocketServer import ThreadingMixIn

import urlparse
import threading

from config import *
from door import *

# Named global logger from config
logger = logging.getLogger("garage")

html = """
<!DOCTYPE html>
<html>
<meta name="viewport" content="width=device-width, initial-scale=1">
<head>
<meta http-equiv="refresh" content="10;url=/" />
<style>
.button {
  background-color: #00bfff;
  border: none;
  color: white;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 20px;
  margin: 4px 2px;
  cursor: pointer;
  width: 160px; 
  height: 60px;
}
</style>
</head>
<body>
<center>
<h1>%s</h1>
<form action="/">
  <input type="submit" class="button" name="action" value="Open"><br><br>
  <input type="submit" class="button" name="action" value="Close"><br><br>
  <input type="submit" class="button" name="action" value="Refresh"><br><br>
</form>
<br>
%s
</center>
</body>
</html>
"""

class HTTPDoorHandler(BaseHTTPRequestHandler):
    def respond(self, message):
        # Instance of global GarageDoor object is on server.
        door = self.server.door
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html % (message, door.status()))
        logger.info("do_GET done: %s" % self.path)
        return

    def redirect(self):
        # Respond with temporary redirect so browser continue sending requests. 
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()
        return
    
    def log_message(self, format, *args):
        return logger.info(self.address_string() + " - " + (format % args))

    def do_GET(self):
        logger.info("do_GET started: %s" % self.path)
        # Instance of global GarageDoor object is on server.
        door = self.server.door
        parsed = urlparse.urlparse(self.path)
        if parsed.path != '/':
            self.send_response(404)
            self.end_headers()
            logger.info("do_GET returned 404.")
            return
        params = urlparse.parse_qs(parsed.query)
        action = params["action"][0].lower() if "action" in params else ""
        if action == "open":
            door.open()
            return self.redirect()
        elif action == "close":
            door.close()
            return self.redirect()
        if door.is_opened():
            state = "opened."
        else:
            state = "closed."            
        logger.info("do_GET before respond: %s" % self.path)
        return self.respond("Garage door is " + state)
    pass

class HTTPDoorServer(ThreadingMixIn, HTTPServer):
    def __init__(self, door, address, handler_class):
        HTTPServer.__init__(self, address, handler_class)
        self.door = door
        return

class HTTPDoorController(threading.Thread):
    def __init__(self, door):
        threading.Thread.__init__(self)
        logger.info("created http door controller")
        self.door = door
        return
    
    def run(self):
        logger.info("starting HTTP server: %s:%d" % (HTTP_HOST, HTTP_PORT))
        self.httpserver = HTTPDoorServer(self.door, ("", HTTP_PORT), HTTPDoorHandler)
        logger.info("starting serve forever...")
        self.httpserver.serve_forever()
        logger.info("...done serve forever")
        return

    def shutdown(self):
        self.httpserver.shutdown()
        return
