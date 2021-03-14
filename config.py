
import logging
import logging.handlers

# daemon log and lock
LOGFILE = "/var/log/garage-daemon.log"
PIDFILE = "/var/run/garage-daemon.pid"

# http host and port to start http server
HTTP_HOST = "" # "garage.local"
HTTP_PORT = 80

# GPIO inputs/outputs
RED_LED = 17  # lights up when door is open
GREEN_LED = 4 # lights up when door is closed
SENSOR = 22   # input for magnetic sensor
RELAY = 5     # output for 1 second relay 

# produced by twitter-oauth.py
TWITTER_CREDS = "/usr/share/garage/twitter.oauth"
TWITTER_PHRASES = "/usr/share/garage/phrases.txt"
# FosterCityGarageDoor twitter app
CONSUMER_KEY = "VhYw8id8h1TLp4EnL7bRPBnRa"
CONSUMER_SECRET = "v6myWEFUaRJgUB7e05kPwmRnq60CUZ8RyHYOoe0imFP6KQReC0"
TWITTER_ACCOUNT = "vofitserov"
# Check for twitter command every N seconds
TWITTER_LISTEN = 120
# Sleep in case we got twitter error (rate limit)
TWITTER_BREAK = 10*60
# Check for twitter notification every 60 seconds
TWITTER_NOTIFY = 60

TWITTER_MONITOR = "fostercitydoor"

# how long garage door could remain opened
MAX_OPEN = 30*60 # 30 min

# send notification every N seconds.
NOTIFY = 10*60 # 10 min

# silence notifications for N seconds each time.
SILENCE = 2*60*60 # 2 hours

# Tesla login and keys
TESLA_CREDS = "/usr/share/garage/tesla.oauth"

# Local http server watcher
LOCAL_CHECK = 600
LOCAL_HOST = "garage.local"

logger = logging.getLogger("garage")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

handler = logging.handlers.RotatingFileHandler(
                  LOGFILE, maxBytes=100000, backupCount=5)

handler.setFormatter(formatter)
logger.addHandler(handler)

