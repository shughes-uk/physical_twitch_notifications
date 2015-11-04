import logging
import os
import sys
from devices import Hue, KankunSocket
from yaml import load
logger = logging.getLogger("sub_alert")


class ptn(object):

    def __init__(self):
        logger.info("Sub_alerter starting up")
        self.config = self._loadconfig()
        self.twitchchat = None
        self.twitchapi = None

    def _loadconfig(self):
        logger.info("Loading configuration from config.txt")
        config = None
        if os.path.isfile("config.txt"):
            try:
                config = load(open("config.txt", 'r'))
                print config
                self.load_devices(config['devices'])
            except Exception, e:
                logger.critical("Problem loading configuration file, try deleting config.txt and starting again")
                raise e
        else:
            logger.critical("config.txt doesn't exist, please create it, refer to config_example.txt for reference")
            sys.exit()
        logger.info("Configuration loaded")
        return config

    def load_devices(self, devicecfg):
        for devicename in devicecfg:
            if devicecfg[devicename]["type"] == "kankun_plug_socket":
                device = self.configure_kankun(devicecfg[devicename])

    def configure_kankun(self, kankuncfg):
        kankunsocket = KankunSocket(kankuncfg["ip"])
        for subscription in kankuncfg['subscriptions']:
            if subscription == "on_subscriber":
                pass

# 'main'
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s.%(msecs)d %(levelname)s %(name)s : %(message)s",
                        datefmt="%H:%M:%S")
    ptn = ptn()
