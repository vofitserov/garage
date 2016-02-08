
import logging
import threading
import time
import os
import sys

from config import *
from door import *

from tweepy import *

# Named global logger from config
logger = logging.getLogger("garage")

def read_token_file(filename):
    access_file = open(filename, "r")
    access_token = access_file.readline().strip("\n")
    access_secret = access_file.readline().strip("\n")
    access_file.close()
    return (access_token, access_secret)

class TweetpyNotifier(threading.Thread):
    def __init__(self, door):
        threading.Thread.__init__(self)
        logger.info("tweetpy creating notifier for %s using %s" %
                    (TWITTER_ACCOUNT, TWITTER_CREDS))
        (self.oauth_token, self.oauth_secret) = read_token_file(TWITTER_CREDS)
        self.door = door
        self.auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        self.auth.set_access_token(self.oauth_token, self.oauth_secret)
        self.twitter = API(self.auth)
        return
    
    def notify(self):
        if self.door.check() and self.door.notify():
            reply = self.door.message()
            logger.info("tweetpy sending to %s \"%s\"" %
                    (TWITTER_ACCOUNT, reply))
            self.twitter.send_direct_message(
                screen_name = TWITTER_ACCOUNT,
                text = reply + " Reply \"close\" or \"stop\" to this message.")
        return
    
    def run(self):
        logger.info("tweetpy checking door every %d seconds" %
                    TWITTER_CHECK)
        while True:
            try:
                self.notify()
                time.sleep(TWITTER_CHECK)
            except TweepError as e:
                logger.error(str(e))
                logger.info("tweetpy notifier sleeping 10 minutes after the error")
                time.sleep(10*60)
                pass
            pass
        return

class TweetpyListener(StreamListener):
    """ A listener handles tweets that are received from the stream.
    This is a basic listener that just prints received tweets to stdout.
    """
    def __init__(self, server):
        StreamListener.__init__(self)
        self.server = server
        return

    def on_direct_message(self, status):
        self.server.handle_message(status)
        return True

    def on_connect(self):
        logger.info("tweetpy successfully connected.")
        return
        
    def on_error(self, status):
        raise TweepError("listener error: %s" % str(status))
        return False

class TweetpyServer(threading.Thread):
    def __init__(self, door):
        threading.Thread.__init__(self)
        logger.info("tweetpy creating server for %s using %s" %
                    (TWITTER_ACCOUNT, TWITTER_CREDS))
        (self.oauth_token, self.oauth_secret) = read_token_file(TWITTER_CREDS)
        self.door = door
        self.auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        self.auth.set_access_token(self.oauth_token, self.oauth_secret)
        self.twitter = API(self.auth)
        return

    def run(self):
        while True:
            try:
                logger.info("tweetpy checking commands every %d seconds" %
                            TWITTER_CHECK)
                self.listen()
                logger.info("tweetpy sleeping after listen")
                time.sleep(TWITTER_CHECK)
            except TweepError as e:
                logger.error(str(e))
                logger.info("tweetpy server sleeping 10 minutes after the error")
                time.sleep(10*60)
                pass
            pass
        return

    def handle_message(self, status):
        text = status.direct_message['text'].lower().replace("\n", " ")
        screen_name = status.direct_message['sender_screen_name']
        logger.info("tweetpy got direct message: \"%s\" from \"@%s\""
                    % (text, screen_name))
        if screen_name != TWITTER_ACCOUNT:
            logger.info("tweetpy message from \"@%s\" is ignored." % screen_name)
            return
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
            self.twitter.send_direct_message(
                user=TWITTER_ACCOUNT, text = "Killing server right now.")
            logger.critical("tweetpy asked to kill the server")
            os._exit(1)
            pass
        self.twitter.send_direct_message(
            screen_name=TWITTER_ACCOUNT, text=reply)
        return
        
    def listen(self):
        listener = TweetpyListener(self)
        self.stream = Stream(self.auth, listener)
        self.stream.userstream()
        return
