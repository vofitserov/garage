
import logging


LOGFILE = "/var/log/garage-daemon.log"
PIDFILE = "/var/run/garage-daemon.pid"
HTTP_HOST = "" # "garage.local"
HTTP_PORT = 80
RED_LED = 17
GREEN_LED = 4
SENSOR = 22

logger = logging.getLogger("garage")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.FileHandler(LOGFILE)

#handler = logging.handlers.RotatingFileHandler(
#                  LOGFILE, maxBytes=100000, backupCount=5)

handler.setFormatter(formatter)
logger.addHandler(handler)

