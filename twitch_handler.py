from twitch.api import v3 as twitch
import threading
import logging
from time import sleep


class TwitchHandler(object):

    def __init__(self, name_list):
        super(TwitchHandler, self).__init__()
        self.logger = logging.getLogger("TwitchHandler")
        self.follower_cache = {}
        self.thread = threading.Thread(target=self.run)
        self.running = False
        self.follower_callbacks = []
        self.streaming_callbacks = []
        self.online_status = {}
        for name in name_list:
            if twitch.streams.by_channel(name).get("stream"):
                self.online_status[name] = True
            else:
                self.online_status[name] = False
            self.follower_cache[name] = twitch.follows.by_channel(name, limit=1)

    def subscribe_new_follow(self, callback):
        self.follower_callbacks.append(callback)

    def subscribe_streaming_status(self, callback):
        self.streaming_callbacks.append(callback)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def run(self):
        self.logger.info("Starting twitch api polling")
        self.running = True
        if self.streaming_callbacks or self.follower_callbacks:
            while self.running:
                self.check_streaming()
                if self.follower_callbacks:
                    self.check_followers()
                sleep(60)

        else:
            self.logger.critical("Not starting, no callbacks registered")

    def check_streaming(self):
        for name in self.streamers:
            result = twitch.streams.by_channel.get("stream")
            if result:
                if not self.streamers[name]:
                    self.streamers[name] = True
                    for callback in self.streaming_callbacks:
                        callback(name, True)
            elif self.streamers[name]:
                self.streamers[name] = False
                for callback in self.streaming_callbacks:
                    callback(name, False)

    def check_followers(self):
        for name in self.streamers:
            lastfollower = twitch.follows.by_channel(name, limit=1)
            if lastfollower != self.follower_cache[name]:
                self.follower_cache[name] = lastfollower
                for callback in self.follower_callbacks:
                    callback(lastfollower, name)

    def stop(self):
        self.logger.info("Attempting to stop twitch api polling")
        self.running = False
        if self.thread.is_alive():
            self.thread.join()
