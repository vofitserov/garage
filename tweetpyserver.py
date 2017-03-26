
import logging
import threading
import time
import os
import sys
import signal
import random

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
        self.stream_ping = time.time()
        return
    
    def notify(self):
        if self.door.check() and self.door.notify():
            reply = self.door.message()
            logger.info("tweetpy sending to %s \"%s\"" %
                    (TWITTER_ACCOUNT, reply))
            self.twitter.send_direct_message(
                screen_name = TWITTER_ACCOUNT,
                text = reply + " Reply \"close\" or \"stop\" to this message.")
            pass
        if time.time() - self.stream_ping > TWITTER_PING:
            reply = "ping"
            logger.info("tweetpy sending to %s \"%s\"" %
                    (TWITTER_MONITOR, reply))
            self.twitter.send_direct_message(
                screen_name = TWITTER_MONITOR, text = reply)
            self.stream_ping = time.time()
            pass
        return
    
    def run(self):
        logger.info("tweetpy checking door every %d seconds" %
                    TWITTER_NOTIFY)
        logger.info("tweetpy pinging stream every %d seconds" %
                    TWITTER_PING)
        while True:
            try:
                self.notify()
                time.sleep(TWITTER_NOTIFY)
            except Exception as e:
                logger.error("tweetpy exception: " + str(e))
                logger.info("tweetpy notifier sleeping 10 minutes after the error")
                time.sleep(TWITTER_BREAK)
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
        return self.server.on_direct_message(status)

    def on_connect(self):
        self.server.on_connect()
        return

    def on_disconnect(self, notice):
        logger.info("tweetpy on_disconnect")
        return False
    
    def on_timeout(self):
        logger.info("tweetpy on_timeout")
        return False

    def keep_alive(self):
        # logger.info("tweetpy keep_alive")
        return True
    
    def on_error(self, status):
        logger.info("tweetpy on_error: " + str(status))
        return False
    
    def on_status(self, status):
        logger.info("tweetpy on_status: " + str(status))
        return

    def on_exception(self, exception):
        logger.info("tweetpy on_exception: " + str(exception))
        return

    def on_delete(self, status_id, user_id):
        logger.info("tweetpy on_delete: " + str(status_id))
        return

    def on_event(self, status):
        logger.info("tweetpy on_event: " + str(status))
        return

    def on_limit(self, track):
        logger.info("tweetpy on_limit: " + str(track))
        return

class TeslaUnknown:
    def drive(self):
        return "tesla drive status is unknown"
    def charge(self):
        return "tesla charge status is unknown"

class TweetpyStreamer(threading.Thread):
    def __init__(self, door, garage):
        threading.Thread.__init__(self)
        logger.info("tweetpy creating server for %s using %s" %
                    (TWITTER_ACCOUNT, TWITTER_CREDS))
        (self.oauth_token, self.oauth_secret) = read_token_file(TWITTER_CREDS)
        self.door = door
        self.tesla = None
        self.garage = garage
        self.auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        self.auth.set_access_token(self.oauth_token, self.oauth_secret)
        self.twitter = API(self.auth)
        self.listener = TweetpyListener(self)
        self.phrases = open(TWITTER_PHRASES).readlines()
        logger.info("tweetpy loaded %d phrases" % len(self.phrases))
        return

    def run(self):
        while True:
            try:
                logger.info("tweetpy checking commands every %d seconds" %
                            TWITTER_CHECK)
                # sleep on start up, otherwise we'll hang in dns
                time.sleep(TWITTER_CHECK)
                self.listen()
                pass
            except Exception as e:
                logger.error("tweetpy exception: " + str(e))
                logger.info("tweetpy server sleeping 10 minutes after the error")
                time.sleep(TWITTER_BREAK)
                pass
            pass
        return

    def get_tesla(self):
        if self.tesla: return self.tesla
        try:
            logger.info("tweetpy tesla getting token for garage")
            token = self.garage.get_token()
            logger.info("tweetpy tesla got %s token" % token.access_token)
            vehicles = self.garage.get_vehicles()
            logger.info("tweetpy tesla got %d vehicles" % len(vehicles))
            self.tesla = vehicles[0]
        except Exception as e:
            logger.error("tweetpy tesla exception: " + str(e))
            logger.info("tweetpy tesla sleeping 10 minutes after the error")
            time.sleep(TWITTER_BREAK)
            pass
        return self.tesla if self.tesla else TeslaUnknown()

    def on_connect(self):
        logger.info("tweetpy successfully connected.")
        self.last_connected = time.time()
        pass
    
    def on_direct_message(self, status):
        text = status.direct_message['text'].lower().replace("\n", " ")
        screen_name = status.direct_message['sender_screen_name']
        logger.info("tweetpy got direct message: \"%s\" from \"@%s\""
                    % (text, screen_name))
        if screen_name != TWITTER_ACCOUNT:
            logger.info("tweetpy message from \"@%s\" is ignored." % screen_name)
            if time.time() - self.stream_start > TWITTER_PING:
                logger.info("tweetpy got ping, closing stream.")
                return False
            return True
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
        if text.find("drive") == 0:
            reply = self.get_tesla().drive().replace("<br>", " ")
            pass
        if text.find("charge") == 0:
            reply = self.get_tesla().charge().replace("<br>", " ")
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
            self.twitter.send_direct_message(
                user=TWITTER_ACCOUNT, text = "Killing server right now.")
            logger.critical("tweetpy asked to kill the server")
            # if this will not kill it, the os._exit() will
            os.kill(os.getpid(), signal.SIGTERM)
            time.sleep(10)
            os._exit(-1)
            pass
        self.twitter.send_direct_message(
            screen_name=TWITTER_ACCOUNT, text=reply)
        return True
        
    def listen(self):
        self.stream = Stream(self.auth, self.listener, timeout=300.0)
        self.stream_start = time.time()
        self.stream.userstream()
        return
