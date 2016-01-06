
import logging
import threading

import time
import RPi.GPIO as GPIO

from config import *

# Named global logger from config
logger = logging.getLogger("garage")

class GarageDoor:
    def __init__(self):
        # Use this lock to protect last known state of the door
        # for update() function called from GIO
        self.lock = threading.Lock()
        self.last_opened = 0
        self.last_closed = 0
        self.last_notified = 0
        self.last_silenced = 0
        logger.info("initializing GPIO in BCM mode.")
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RED_LED, GPIO.OUT)
        GPIO.setup(GREEN_LED, GPIO.OUT)
        GPIO.setup(RELAY, GPIO.OUT)
        GPIO.output(RELAY, True)
        GPIO.output(RED_LED, True)
        GPIO.output(GREEN_LED, True)
        # If connected to the ground, use pull up resistor.
        GPIO.setup(SENSOR, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # If the door is closed, assume the censor is working.
        if self.is_closed():
            logger.info("door is closed on init, assume sensor is working and initialized.")
            self.initialized = True
            pass
        if self.is_opened():
            logger.info("door is opened on init, wait until see update from sensor.")
            self.initialized = False
            pass
        GPIO.add_event_detect(SENSOR, GPIO.BOTH,
            callback=lambda channel: self.update(), bouncetime=100)
        return

    def shutdown(self):
        GPIO.output(RED_LED, False)
        GPIO.output(GREEN_LED, False)
        GPIO.cleanup()
        return
    
    def status(self):
        message = []
        with self.lock:
            now = time.time()
            if not self.initialized:
                message.append("sensor is not initialized.")
                pass
            if self.is_closed():
                message.append("door was closed %d secs ago" %
                               int(now - self.last_closed))
                pass
            if self.is_opened():
                message.append("door was opened %d secs ago" %
                               int(now - self.last_opened))
                pass
            if self.last_closed > self.last_opened:
                message.append("last time door was opend for %d secs" %
                               (self.last_closed - self.last_opened))
                pass
            if self.last_notified != 0 and self.last_notified < now:
                message.append("notified %d secs ago" %
                               int(now - self.last_notified))
                pass
            if self.last_silenced != 0 and self.last_silenced > now:
                message.append("silenced for %d secs" %
                               int(self.last_silenced - now))
                pass
            pass
        return "<br>\n".join(message)
    
    def update(self):
        with self.lock:
            now = time.time()
            self.initialized = True
            if self.is_opened():
                self.last_opened = now
                logger.info("door was opened, last closed %d secs ago" %
                            int(now - self.last_closed))
                GPIO.output(RED_LED, True)
                GPIO.output(GREEN_LED, False)
            else:
                self.last_closed = now
                logger.info("door was closed, last opened %d secs ago" %
                            int(now - self.last_opened))
                GPIO.output(RED_LED, False)
                GPIO.output(GREEN_LED, True)
            pass
        return

    def is_opened(self):
        if GPIO.input(SENSOR) == 1:
            return True
        return False
    
    def is_closed(self):
        if GPIO.input(SENSOR) == 0:
            return True
        return False
    
    def open(self):
        with self.lock:
            now = time.time()
            if self.is_opened():
                return "Garage door is already opened."
            if not self.initialized:
                return "Garage sensor is not initialized. Open door manualy."
            logger.info("door is opening, last closed %d secs ago" %
                        int(now - self.last_closed))
            pass
        GPIO.output(RELAY, False)
        time.sleep(1)
        GPIO.output(RELAY, True)
        return "Garage door is openning..."

    def close(self):
        with self.lock:
            now = time.time()
            if self.is_closed():
                return "Garage door is already closed."
            if not self.initialized:
                return "Garage sensor is not initialized. Close door manualy."
            logger.info("door is closing, last opened %d secs ago" %
                        int(now - self.last_opened))
            pass
        GPIO.output(RELAY, False)
        time.sleep(1)
        GPIO.output(RELAY, True)
        return "Garage door is closing..."

    # True if opened for too long
    def check(self):
        with self.lock:
            now = time.time()
            if not self.initialized:
                return False
            if self.is_opened() and now - self.last_opened > MAX_OPEN:
                return True
            pass
        return False

    def message(self):
        reply = ""
        with self.lock:
            if self.initialized and self.is_opened():
                now = time.time()
                period = int((now - self.last_opened)/60)
                reply = "Garage door was opened for %d minutes!" % (period)
                pass
            pass
        return reply
        
    # True if notification is recorded, False is silenced or recently notified
    def notify(self):
        with self.lock:
            now = time.time()
            if now < self.last_silenced:
                return False
            if now - self.last_notified > NOTIFY:
                self.last_notified = now
                logger.info("notification recorded")
                return True
            pass
        return False

    def silence(self):
        reply = ""
        with self.lock:
            now = time.time()
            self.last_silenced = max(self.last_silenced, now) + SILENCE
            logger.info("silenced for %d secs" % int(now - self.last_silenced))
            reply = "Notifications are silenced for %d min, until %s." % \
                    (int(self.last_silenced - now)/60,
                    time.asctime(time.localtime(self.last_silenced)))
            pass
        return reply
