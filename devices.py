import phue
from time import sleep
import logging
import threading
import colorhelp
import urllib
import json
import blinkytape
from datetime import timedelta, datetime
RGB_OFF = (0, 0, 0)


class Device(object):

    def __init__(self):
        super(Device, self).__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.action_queue = []
        self.action_thread = None
        self.lock = threading.Lock()

    def start(self):
        raise Exception("Function not implemented, whoops")

    def stop(self):
        raise Exception("Function not implemented, whoops")

    def queue_action(self, target, *args):
        if self.action_thread:
            self.action_queue.append(threading.Thread(target=target, args=args))
        else:
            self.action_thread = threading.Thread(target=target, args=args)
            self.action_thread.start()


def pop_action(f):

    def wrapper(self, *args, **kwargs):
        self.logger.debug("Calling {0}".format(f.__name__))
        f(self, *args, **kwargs)
        if self.action_queue:
            self.action_thread = self.action_queue.pop(0)
            self.action_thread.start()
        else:
            self.action_thread = None

    return wrapper


class PlugSocket(Device):

    def turn_on(self):
        raise Exception("Function not implemented , whoops")

    def turn_off(self):
        raise Exception("Function not implemented , whoops")


class KankunSocket(PlugSocket):

    def __init__(self, ip):
        super(KankunSocket, self).__init__()
        self.ip = ip
        self.timer = threading.Timer(10, self.turn_on)

    @property
    def on_status(self):
        url = "http://{0}/cgi-bin/json.cgi?get=state".format(self.ip)
        response = urllib.urlopen(url)
        data = json.load(response)
        if data['state'] == 'on':
            return True
        else:
            return False

    def _turn_on(self):
        if not self.on_status:
            self.logger.info("Socket[{0}] turning on".format(self.ip))
            url = "http://{0}/cgi-bin/json.cgi?set=on".format(self.ip)
            urllib.urlopen(url)

    def _turn_off(self):
        if self.on_status:
            self.logger.info("Socket[{0}] turning off".format(self.ip))
            url = "http://{0}/cgi-bin/json.cgi?set=off".format(self.ip)
            urllib.urlopen(url)

    def turn_on(self):
        self.queue_action(self.do_turn_on)

    @pop_action
    def do_turn_on(self):
        self._turn_on()

    def turn_off(self):
        self.queue_action(self.do_turn_off)

    @pop_action
    def do_turn_off(self):
        self._turn_off()

    def turn_off_timer(self, duration):
        self.queue_action(self.do_turn_off_timer, duration)

    def do_turn_off_timer(self, duration):
        if self.timer.is_alive():
            self.timer.cancel()
        self.timer = threading.Timer(duration, self.turn_on_callback)
        self.timer.daemon = True
        self.timer.start()
        self.do_turn_off()

    @pop_action
    def turn_on_callback(self):
        self.do_turn_on()

    def turn_on_timer(self, duration):
        self.queue_action(self.do_turn_on_timer, duration)

    def do_turn_on_timer(self, duration):
        if self.timer.is_alive():
            self.timer.cancel()
        self.timer = threading.Timer(duration, self.turn_off_callback)
        self.timer.daemon = True
        self.timer.start()
        self.do_turn_on()

    @pop_action
    def turn_off_callback(self):
        self.do_turn_off()


class RGBLight(Device):

    def __init__(self):
        super(RGBLight, self).__init__()
        self.flashlock = threading.Lock()

    @property
    def current_color():
        raise Exception("Current color not implemented")

    def _set_color():
        raise Exception("Set color not implemented")

    def set_color(self, color):
        self.queue_action(self.do_set_color, color)

    @pop_action
    def do_set_color(self, color):
        self._set_color(color)

    def flash(self, color_1, color_2, ntimes=10, interval=0.2):
        self.queue_action(self.do_flash, color_1, color_2, ntimes, interval)

    @pop_action
    def do_flash(self, color_1, color_2, ntimes=10, interval=0.2):
        with self.flashlock:
            old_color = self.current_color
            for x in range(ntimes):
                self._set_color(color_1)
                sleep(interval)
                self._set_color(color_2)
                sleep(interval)
            self._set_color(old_color)


class BlinkyTape(RGBLight):

    def __init__(self, port):
        super(BlinkyTape, self).__init__()
        self.btape = blinkytape.BlinkyTape(port)
        self.c_color = (0, 0, 0)
        self.set_color(RGB_OFF)

    def light_wave(self, color1, color2, duration):
        self.queue_action(self.do_light_wave, color1, color2, duration)

    @pop_action
    def do_light_wave(self, color1, color2, duration):
        with self.lock:
            stoptime = datetime.now() + timedelta(seconds=duration)
            c1_pcount = 60
            c2_pcount = 0
            reverse = False
            while datetime.now() < stoptime:
                for x in range(c1_pcount):
                    self.btape.sendPixel(color1[0], color1[1], color1[2])
                for x in range(c2_pcount):
                    self.btape.sendPixel(color2[0], color2[1], color2[2])
                self.btape.show()
                if c2_pcount == 60:
                    reverse = True
                elif c1_pcount == 60:
                    reverse = False
                if reverse:
                    c2_pcount -= 1
                    c1_pcount += 1
                else:
                    c2_pcount += 1
                    c1_pcount -= 1
            self.btape.displayColor(self.c_color[0], self.c_color[1], self.c_color[2])

    @property
    def current_color(self):
        return self.c_color

    def _set_color(self, rgb):
        with self.lock:
            self.btape.displayColor(rgb[0], rgb[1], rgb[2])
            self.c_color = rgb


class Hue(RGBLight):

    def __init__(self, ip, name):
        super(Hue, self).__init__()
        phue.logger.setLevel(logging.INFO)
        self.bridge = phue.Bridge(ip=ip, config_file_path='.hue_config')
        self.light = None
        self.bridge.get_light_objects(mode='id')
        for light in self.bridge.lights_by_id.values():
            if light.name.lower() == name:
                self.light = light
                break
        if not self.light:
            raise Exception("Light with id {0} not found".format(name))

    @property
    def current_color(self):
        return colorhelp.colorFromXY(self.light.xy)

    @pop_action
    def do_flash(self, color_1, color_2, ntimes=2, interval=0.2):
        with self.flashlock:
            # store the old state
            old_rgb = self.current_color
            old_brightness = self.light.brightness
            try:
                self.logger.debug("Flashing")
                # flash a bunch
                for x in range(ntimes):
                    self._set_color(rgb=color_1, brightness=254)
                    sleep(interval)
                    self._set_color(rgb=color_2, brightness=254)
                    sleep(interval)
            finally:
                # reset to old states
                self.logger.debug("Attempting reset to old state rgb :{0}, brightness:{1}".format(old_rgb,
                                                                                                  old_brightness))
                while self.current_color != old_rgb:
                    sleep(0.3)
                    self._set_color(rgb=old_rgb, brightness=old_brightness)

    def start(self):
        pass

    def stop(self):
        pass

    def _set_color(self, rgb=None, xy=None, brightness=None):
        with self.lock:
            self.light.transitiontime = 0
            x, y = colorhelp.calculateXY(rgb[0], rgb[1], rgb[2])
            self.light.xy = (x, y)
            self.light.brightness = 254
