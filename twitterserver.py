import logging
import threading
import time
import os
import sys
import signal
import random

from config import *
from door import *

from twitter import *

# Named global logger from config
logger = logging.getLogger("garage")

def read_token_file(filename):
    access_file = open(filename, "r")
    access_token = access_file.readline().strip("\n")
    access_secret = access_file.readline().strip("\n")
    access_file.close()
    return (access_token, access_secret)

class TwitterNotifier(threading.Thread):
    def __init__(self, door):
        threading.Thread.__init__(self)
        logger.info("twitter creating notifier for %s using %s" %
                    (TWITTER_ACCOUNT, TWITTER_CREDS))
        (self.oauth_token, self.oauth_secret) = read_token_file(TWITTER_CREDS)
        self.door = door
        self.twitter = Api(consumer_key=CONSUMER_KEY,
                           consumer_secret=CONSUMER_SECRET,
                           access_token_key=self.oauth_token,
                           access_token_secret=self.oauth_secret,
                           sleep_on_rate_limit=True)
        return

    def notify(self):
        if self.door.check() and self.door.notify():
            reply = self.door.message()
            logger.info("twitter sending to %s \"%s\"" %
                        (TWITTER_ACCOUNT, reply))
            self.twitter.PostDirectMessage(
                screen_name=TWITTER_ACCOUNT,
                text=reply + " Reply \"close\" or \"stop\" to this message.")
            pass
        return

    def run(self):
        logger.info("twitter checking door every %d seconds" %
                    TWITTER_NOTIFY)
        while True:
            try:
                time.sleep(TWITTER_NOTIFY)
                self.notify()
            except Exception as e:
                logger.error("twitter exception: " + str(e))
                logger.info("twitter notifier sleeping 10 minutes after the error")
                time.sleep(TWITTER_BREAK)
                pass
            pass
        return

class TwitterKiller(threading.Thread):
    def run(self):
        logger.critical("twitter asked to kill the server")
        time.sleep(3)
        # if this will not kill it, the os._exit() will
        os.kill(os.getpid(), signal.SIGTERM)
        time.sleep(10)
        os._exit(-1)
        return

class TwitterStreamer(threading.Thread):
    def __init__(self, door, garage):
        threading.Thread.__init__(self)
        logger.info("twitter creating streamer for %s using %s" %
                    (TWITTER_ACCOUNT, TWITTER_CREDS))
        (self.oauth_token, self.oauth_secret) = read_token_file(TWITTER_CREDS)
        self.door = door
        self.tesla = None
        self.garage = garage
        self.twitter = Api(consumer_key=CONSUMER_KEY,
                           consumer_secret=CONSUMER_SECRET,
                           access_token_key=self.oauth_token,
                           access_token_secret=self.oauth_secret,
                           sleep_on_rate_limit=True)
        self.account_user_id  = self.twitter.GetUser(screen_name=TWITTER_ACCOUNT).id
        logger.info("twitter expecting messages from %s" % self.account_user_id)
        messages = self.twitter.GetDirectMessagesEventsList()
        self.ids = [m.id for m in messages]
        logger.info("twitter seen ids: %s" % str(self.ids[0:3]))
        return

    def run(self):
        logger.info("twitter checking commands every %d seconds" %
                    TWITTER_LISTEN)
        while True:
            try:
                # sleep on start up, otherwise we'll hang in dns
                time.sleep(TWITTER_LISTEN)
                self.listen()
                pass
            except Exception as e:
                logger.error("twitter exception: " + str(e))
                logger.info("twitter server sleeping 10 minutes after the error")
                time.sleep(TWITTER_BREAK)
                pass
            pass
        return

    def get_tesla(self):
        if self.tesla: return self.tesla
        try:
            logger.info("twitter tesla getting token for garage")
            token = self.garage.get_token()
            logger.info("twitter tesla got %s token" % token.access_token)
            vehicles = self.garage.get_vehicles()
            logger.info("twitter tesla got %d vehicles" % len(vehicles))
            self.tesla = vehicles[0]
        except Exception as e:
            logger.error("twitter tesla exception: " + str(e))
            logger.info("twitter tesla sleeping 10 minutes after the error")
            time.sleep(TWITTER_BREAK)
            pass
        return self.tesla if self.tesla else TeslaUnknown()

    def on_direct_message(self, status):
        text = status.text.lower().replace("\n", " ")
        sender_id = status.sender_id
        logger.info("twitter got direct message: \"%s\" from \"%s\""
                    % (text, sender_id))
        if sender_id != self.account_user_id:
            logger.info("twitter message from \"%s\" is ignored, expecting only \"%s\"" % (sender_id, self.account_user_id))
            return
        reply = "Unrecognized command, try \"status\" or \"help\""
        if text.find("close") == 0:
            reply = self.door.close()
            pass
        if text.find("stop") == 0 or text.find("silence") == 0:
            reply = self.door.silence()
            pass
        if text.find("status") == 0:
            reply = self.door.status().replace("<br>", ", ")
            pass
        if text.find("drive") == 0:
            reply = self.get_tesla().drive().replace("<br>", ", ")
            pass
        if text.find("charge") != -1 and text.find("debug") != -1:
            reply = self.get_tesla().debug()
            pass
        if text.find("charge") == 0:
            reply = self.get_tesla().charge().replace("<br>", ", ")
            pass
        if text.find("help") == 0:
            reply = "Available commands are: close, stop/silence, status, drive or charge."
            pass
        if text.find("awesome") != -1 or text.find("awsome") != -1:
            reply = "You sure are awesome!"
            pass
        if text.find("say") != -1:
            reply = random.choice(self.phrases)
            pass
        if text.find("quitquitquit") == 0:
            reply = "Killing server right now."
            killer = TwitterKiller()
            killer.setDaemon(True)
            killer.start()
            pass
        self.twitter.PostDirectMessage(reply, user_id=sender_id)
        return

    def listen(self):
        messages = self.twitter.GetDirectMessagesEventsList()
        for m in messages:
            if m.id not in self.ids:
                self.on_direct_message(m)
                pass
            pass
        self.ids = [m.id for m in messages]
        logger.info("twitter seen ids: %s" % str(self.ids[0:3]))
        return
