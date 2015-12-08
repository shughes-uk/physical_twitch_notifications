import logging
import os
import time
import sys
import argparse
import webcolors
from devices import Hue, KankunSocket
from yaml import load
from pprint import pformat
from twitchchat import twitch_chat
from twitcher import twitcher

logger = logging.getLogger("ptn")


class ptn(object):

    def __init__(self, test=False):
        logger.info("ptn starting up")
        subs = ['on_follower', 'on_subscriber', 'on_start_streaming', 'on_stop_streaming', 'on_follower_count']
        self.twitchchat = None
        self.twitcher = None
        self.test_mode = test
        self.subscriptions = {}
        for sub in subs:
            self.subscriptions[sub] = []
        self.devices = []
        self.config = self.loadconfig()

    def start(self):
        if self.twitchchat:
            self.twitchchat.start()
        if self.twitcher:
            self.twitcher.start()

    def stop(self):
        if self.twitchchat:
            self.twitchchat.stop()
        if self.twitcher:
            self.twitcher.stop()

    def loadconfig(self):
        logger.info("Loading configuration from config.txt")
        config = None
        if os.path.isfile("config.txt"):
            config = load(open("config.txt", 'r'))
            if self.test_mode:
                from twitch.api import v3 as twitch
                featured_stream = twitch.streams.featured(limit=1)['featured'][0]
                self.load_twitcher(featured_stream['stream']['channel']['name'])
                self.load_twitchchat(config['twitch_username'], config['twitch_oauth'],
                                     featured_stream['stream']['channel']['name'])
            else:
                self.load_twitchchat(config['twitch_username'], config['twitch_oauth'], config['twitch_channel'])
                self.load_twitcher(config['twitch_channel'])
            self.load_devices(config['devices'])
            self.setup_subscriptions()
        else:
            logger.critical("config.txt doesn't exist, please create it, refer to config_example.txt for reference")
            sys.exit()
        logger.info("Configuration loaded")
        return config

    def load_twitcher(self, channel):
        self.twitcher = twitcher([channel])

    def load_twitchchat(self, username, oauth, channel):
        self.twitchchat = twitch_chat(username, oauth, [channel])

    def setup_subscriptions(self):
        if self.subscriptions['on_follower'] or self.subscriptions['on_follower_count']:
            self.twitcher.subscribe_new_follow(self.on_follower)
        if self.subscriptions['on_subscriber']:
            self.twitchchat.subscribeNewSubscriber(self.on_subscriber)
        if self.subscriptions['on_start_streaming']:
            self.twitcher.subscribe_streaming_start(self.started_streaming)
        if self.subscriptions['on_stop_streaming']:
            self.twitcher.subscribe_streaming_stop(self.stopped_streaming)

    def handle_action(self, device, cfg):
        if cfg['action'].keys()[0] == 'flash':
            f_config = cfg['action']['flash']
            c1 = webcolors.name_to_rgb(f_config['color_1'])
            c2 = webcolors.name_to_rgb(f_config['color_2'])
            count = f_config['times_to_flash']
            speed = f_config['flash_speed']
            device.flash(c1, c2, count, speed)

    def started_streaming(self, streamer_name):
        for device, cfg in self.subscriptions['on_start_streaming']:
            self.handle_action(device, cfg)

    def stopped_streaming(self, streamer_name):
        logger.info(pformat(args))
        logger.info('stopped streaming')

    def on_follower(self, followerset, streamername, total):
        for device, cfg in self.subscriptions['on_follower_count']:
            logger.info(pformat(cfg))
            if total >= cfg['count'] and not cfg['triggered']:
                self.handle_action(device, cfg)
                cfg['triggered'] = True
                break
        for device, cfg in self.subscriptions['on_follower']:
            self.handle_action(device, cfg)

    def on_subscriber(self, channel, subscriber, months):
        logger.info(pformat(args))
        logger.info('new subscriber')

    def load_devices(self, devicecfg):
        for devicename in devicecfg:
            if devicecfg[devicename]["type"] == "kankun_plug_socket":
                self.configure_kankun(devicecfg[devicename])
            elif devicecfg[devicename]['type'] == 'hue':
                self.configure_phue(devicecfg[devicename])

    def configure_kankun(self, kankuncfg):
        kankunsocket = KankunSocket(kankuncfg["ip"])
        self.configure_subscriptions(kankunsocket, kankuncfg['subscriptions'])
        self.devices.append(kankunsocket)

    def configure_phue(self, phuecfg):
        phue = Hue(phuecfg['ip'], phuecfg['hue_name'])
        self.configure_subscriptions(phue, phuecfg['subscriptions'])
        self.devices.append(phue)

    def configure_subscriptions(self, device, subcfg):
        for subscription in subcfg:
            if subscription == "on_subscriber":
                self.subscriptions['on_subscriber'].append((device, subcfg[subscription]))
            elif subscription == "on_follower":
                self.subscriptions['on_follower'].append((device, subcfg[subscription]))
            elif subscription == "on_start_streaming":
                self.subscriptions['on_start_streaming'].append((device, subcfg[subscription]))
            elif subscription == "on_stop_streaming":
                self.subscriptions['on_stop_streaming'].append((device, subcfg[subscription]))
            elif subscription == "on_follower_count":
                self.subscriptions['on_follower_count'].append((device, subcfg[subscription]))

# 'main'
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", help="Subscribe to featured channel to aid testing", action="store_true")
    parser.add_argument('-d',
                        '--debug',
                        help="Enable debugging statements",
                        action="store_const",
                        dest="loglevel",
                        const=logging.DEBUG,
                        default=logging.INFO,)
    args = parser.parse_args()
    logging.basicConfig(
        level=args.loglevel,
        format='%(asctime)s.%(msecs)d %(levelname)s %(name)s : %(message)s',
        datefmt='%H:%M:%S')
    ptn = ptn(args.test)
    ptn.start()
    try:
        while True:
            time.sleep(0.2)
    finally:
        ptn.stop()
