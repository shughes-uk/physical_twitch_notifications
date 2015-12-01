import logging
import os
import sys
from devices import Hue, KankunSocket
from yaml import load
from pprint import pformat
from twitchchat import twitch_chat
import twitch_handler

logger = logging.getLogger("sub_alert")


class ptn(object):
    def __init__(self):
        logger.info("Sub_alerter starting up")
        subs = ['on_follower', 'on_subscriber', 'on_start_streaming',
                'on_stop_streaming']
        self.subscriptions = {}
        for sub in subs:
            self.subscriptions[sub] = []
        self.devices = []
        self.config = self._loadconfig()
        self.twitchchat = None
        self.twitchapihandler = None

    def _loadconfig(self):
        logger.info("Loading configuration from config.txt")
        config = None
        if os.path.isfile("config.txt"):
            # try:
            config = load(open("config.txt", 'r'))
            self.load_twitchchat(config['twitch_username'],
                                 config['twitch_oauth'],
                                 config['twitch_channel'])
            self.load_twitch_handler(config['twitch_channel'])
            self.load_devices(config['devices'])
            # except Exception, e:
            #     logger.critical("Problem loading configuration file, try deleting config.txt and starting again")
            #     raise e
        else:
            logger.critical(
                "config.txt doesn't exist, please create it, refer to config_example.txt for reference")
            sys.exit()
        logger.info("Configuration loaded")
        return config

    def load_twitch_handler(self, channel):
        self.twitchapi_handler = twitch_handler.TwitchHandler([channel])

    def load_twitchchat(self, username, oauth, channel):
        self.twitchchat = twitch_chat(username, oauth, [channel])

    def setup_onfollower(self):
        if self.subscriptions['on_follower']:
            self.twitchapi_handler.subscribe_new_follow(self.on_follower)
        if self.subscriptions['on_subscription']:
            self.twitchchat.subscribeNewSubscriber(self.on_subscriber)
        if self.subscriptions['on_start_streaming']:
            self.twitchapi_handler.subscribe_streaming_start(
                self.started_streaming)
        if self.subscriptions['on_stop_streaming']:
            self.twitchapi_handler.subscribe_streaming_stop(
                self.stopped_streaming)

    def started_streaming(self, name):
        pass

    def stopped_streaming(self, name):
        pass

    def on_follower(self):
        pass

    def load_devices(self, devicecfg):
        for devicename in devicecfg:
            if devicecfg[devicename]["type"] == "kankun_plug_socket":
                device = self.configure_kankun(devicecfg[devicename])
                self.devices.append(device)
            elif devicecfg[devicename]['type'] == 'hue':
                device = self.configure_phue(devicecfg[devicename])
                self.devices.append(device)

    def configure_kankun(self, kankuncfg):
        kankunsocket = KankunSocket(kankuncfg["ip"])
        self.configure_subscriptions(kankunsocket, kankuncfg['subscriptions'])

    def configure_phue(self, phuecfg):
        phue = Hue(phuecfg['ip'], phuecfg['hue_name'])
        self.configure_subscriptions(phue, phuecfg['subscriptions'])

    def configure_subscriptions(self, device, subcfg):
        for subscription in subcfg:
            if subscription == "on_subscriber":
                self.subscriptions['on_subscriber'].append((
                    device, subcfg[subscription]))
            elif subscription == "on_follower":
                self.subscriptions['on_follower'].append((
                    device, subcfg[subscription]))
            elif subscription == "on_start_streaming":
                self.subscriptions['on_start_streaming'].append((
                    device, subcfg[subscription]))
            elif subscription == "on_stop_streaming":
                self.subscriptions['on_stop_streaming'].append((
                    device, subcfg[subscription]))

# 'main'
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s.%(msecs)d %(levelname)s %(name)s : %(message)s",
        datefmt="%H:%M:%S")
    ptn = ptn()
    while True:
        pass
