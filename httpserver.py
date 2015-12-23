
from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer

import urlparse

from config import *
from door import *

# Named global logger from config
logger = logging.getLogger("garage")

html = """
<!DOCTYPE html>
<html>
<body>

<h1>%s</h1>

<form action="/">
  <input type="submit" name="action" value="Open">
  <input type="submit" name="action" value="Close">
  <input type="submit" name="action" value="Refresh">
</form>

<br>
<br>
%s

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
        self.wfile.close()
        return

    def log_message(self, format, *args):
        return logger.info(self.address_string() + " - " + (format % args))
    
    def do_GET(self):
        # Instance of global GarageDoor object is on server.
        door = self.server.door
        parsed = urlparse.urlparse(self.path)
        if parsed.path != '/':
            self.send_response(404)
            self.end_headers()
            return
        params = urlparse.parse_qs(parsed.query)
        action = params["action"][0].lower() if "action" in params else ""
        if action == "open":
            return self.respond(door.open())
        elif action == "close":
            return self.respond(door.close())
        if door.is_opened():
            state = "opened."
        else:
            state = "closed."            
        return self.respond("Garage door is " + state)

class HTTPDoorServer(HTTPServer):
    def __init__(self, door, address, handler_class):
        HTTPServer.__init__(self, address, handler_class)
        self.door = door
        return
    
