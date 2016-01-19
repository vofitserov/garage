
import logging
import threading
import time
import os
import sys

from config import *
from door import *

from twitter import *

# Named global logger from config
logger = logging.getLogger("garage")

class TwitterNotifier(threading.Thread):
    def __init__(self, door):
        threading.Thread.__init__(self)
        logger.info("twitter creating notifier for %s using %s" %
                    (TWITTER_ACCOUNT, TWITTER_CREDS))
        (self.oauth_token, self.oauth_secret) = read_token_file(TWITTER_CREDS)
        self.door = door
        self.auth = OAuth(
            self.oauth_token, self.oauth_secret,
            CONSUMER_KEY, CONSUMER_SECRET)
        self.twitter = Twitter(auth=self.auth)
        return
    
    def notify(self):
        if self.door.check() and self.door.notify():
            reply = self.door.message()
            logger.info("twitter sending to %s \"%s\"" %
                    (TWITTER_ACCOUNT, reply))
            self.twitter.direct_messages.new(
                user = TWITTER_ACCOUNT,
                text = reply + " Reply \"close\" or \"stop\" to this message.")
        return
    
    def run(self):
        logger.info("twitter checking door every %d seconds" %
                    TWITTER_CHECK)
        while True:
            try:
                self.notify()
                time.sleep(TWITTER_CHECK)
            except TwitterHTTPError as e:
                logger.error(str(e))
                logger.info("twitter notifier sleeping 10 minutes after the error")
                time.sleep(10*60)
                pass
            pass
        return
        
class TwitterServer(threading.Thread):
    def __init__(self, door):
        threading.Thread.__init__(self)
        logger.info("twitter creating server for %s using %s" %
                    (TWITTER_ACCOUNT, TWITTER_CREDS))
        (self.oauth_token, self.oauth_secret) = read_token_file(TWITTER_CREDS)
        self.door = door
        self.auth = OAuth(
            self.oauth_token, self.oauth_secret,
            CONSUMER_KEY, CONSUMER_SECRET)
        self.twitter_userstream = TwitterStream(
            auth=self.auth,
            domain='userstream.twitter.com')
        self.twitter = Twitter(auth=self.auth)
        return

    def run(self):
        logger.info("twitter checking commands every %d seconds" %
                    TWITTER_CHECK)
        while True:
            try:
                self.listen()
                time.sleep(TWITTER_CHECK)
            except TwitterHTTPError as e:
                logger.error(str(e))
                logger.info("twitter server sleeping 10 minutes after the error")
                time.sleep(10*60)
                pass
            pass
        return

    def listen(self):
        for msg in self.twitter_userstream.user():
            if 'direct_message' not in msg:
                logger.info("twitter stream got: " + str(msg))
                continue
            # logger.info("twitter stream got: " + str(msg))
            text = msg['direct_message']['text'].lower().replace("\n", " ")
            screen_name = msg['direct_message']['sender']['screen_name']
            logger.info("twitter got direct message: \"%s\" from \"@%s\""
                        % (text, screen_name))
            if screen_name != TWITTER_ACCOUNT:
                logger.info("twitter message from \"@%s\" is ignored." % screen_name)
                continue
            reply = "Unrecognized command, try \"status\" or \"help\""
            if text.find("close") == 0:
                reply = self.door.close()
                pass
            if text.find("stop") == 0 or text.find("silence") == 0:
                reply = self.door.silence()
                pass
            if text.find("status") == 0:
                reply = self.door.status().replace("<br>", " ")
                pass
            if text.find("help") == 0:
                reply = "Available commands are: close, stop/silence, status."
                pass
            if text.find("quitquitquit") == 0:
                self.twitter.direct_messages.new(
                    user=TWITTER_ACCOUNT, text = "Killing server right now.")
                logger.critical("twitter asked to kill the server")
                os._exit(1)
                pass
            self.twitter.direct_messages.new(
                user=TWITTER_ACCOUNT, text = reply)
            pass
        return
