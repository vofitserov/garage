import sys
import logging
import logging.handlers

# daemon log and lock
LOGFILE = "/var/log/garaged.log"

# answers for command "say"
SAY_PHRASES = "/home/pi/garage/phrases.txt"

# http host and port to start http server
HTTP_HOST = ""  # "garage.local"
HTTP_PORT = 80

# telegram bot
TELEGRAM_FILE = "/home/pi/garage/telegramdoor.token"
TELEGRAM_TOKEN = open(TELEGRAM_FILE, "r").readline().strip()
TELEGRAM_USERID = 524269296

# GPIO inputs/outputs
RED_LED = 17  # lights up when door is open
GREEN_LED = 4  # lights up when door is closed
SENSOR = 22  # input for magnetic sensor
RELAY = 5  # output for 1 second relay

# how long garage door could remain opened
MAX_OPEN = 30 * 60  # 30 min

# send notification every N seconds.
NOTIFY = 10*60  # 10 min

# silence notifications for N seconds each time.
SILENCE = 2*60*60  # 2 hours

# Local http server watcher
LOCAL_CHECK = 600
LOCAL_HOST = "garage.local"

logger = logging.getLogger("garage")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
