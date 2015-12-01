import math
import phue
from time import sleep
from hue_helper import ColorHelper
import logging
import threading


class Device(object):
    def __init__(self):
        super(Device, self).__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.allowed_actions = []
        self.lock = threading.Lock()
        self.flashlock = threading.Lock()

    def start(self):
        raise Exception("Function not implemented, whoops")

    def stop(self):
        raise Exception("Function not implemented, whoops")


class RGBLight(Device):
    @property
    def current_color():
        raise Exception("Current color not implemented")

    def set_color(self, color):
        raise Exception("Function not implemented , whoops")

    def flash(self,
              color_1,
              color_2,
              ntimes=10,
              interval=0.2,
              nonblocking=False):
        if nonblocking:
            t = threading.Thread(target=self.flash,
                                 args=(color_1, color_2, ntimes, interval))
            t.start()
            return
        else:
            with self.flashlock:
                old_color = self.current_color
                for x in range(ntimes):
                    self.set_color(color_1)
                    sleep(interval)
                    self.set_color(color_2)
                    sleep(interval)
                self.set_color(old_color)


class PlugSocket(Device):
    def turn_on(self):
        raise Exception("Function not implemented , whoops")

    def turn_off(self):
        raise Exception("Function not implemented , whoops")


class KankunSocket(PlugSocket):
    def __init__(self, ip):
        super(KankunSocket, self).__init__()


class Hue(RGBLight):
    def __init__(self, ip, name):
        super(Hue, self).__init__()
        phue.logger.setLevel(logging.INFO)
        self.allowed_actions = ["flash", "set_color"]
        self.bridge = phue.Bridge(ip=ip, config_file_path='.hue_config')
        self.current_phue_status = {}
        self.chelper = ColorHelper()
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
        return self._XYtoRGB(self.light.xy[0], self.light.xy[1],
                             self.light.brightness)

    def flash(self,
              color_1,
              color_2,
              ntimes=2,
              interval=0.2,
              nonblocking=False):
        if nonblocking:
            t = threading.Thread(target=self.flash,
                                 args=(color_1, color_2, ntimes, interval))
            t.start()
            return
        else:
            with self.flashlock:
                # store the old state
                old_rgb = self.current_color
                old_brightness = self.light.brightness
                try:
                    # flash a bunch
                    for x in range(ntimes):
                        self.set_color(rgb=color_1, brightness=254)
                        sleep(interval)
                        self.set_color(rgb=color_2, brightness=254)
                        sleep(interval)
                finally:
                    # reset to old states
                    sleep(0.3)
                    self.set_color(rgb=old_rgb, brightness=old_brightness)

    def start(self):
        pass

    def stop(self):
        pass

    def set_color(self, rgb=None, xy=None, brightness=None):
        with self.lock:
            self.light.transitiontime = 0
            if rgb:
                self.light.xy = self._RGBtoXY(rgb[0], rgb[1], rgb[2])
            elif xy:
                self.light.xy = xy
            self.light.brightness = brightness or 254

    def _enhancecolor(self, normalized):
        if normalized > 0.04045:
            return math.pow((normalized + 0.055) / (1.0 + 0.055), 2.4)
        else:
            return normalized / 12.92

    def _XYtoRGB(self, x, y, brightness):
        return self.chelper.getRGBFromXYAndBrightness(x, y, brightness)

    def _RGBtoXY(self, r, g, b):
        return self.chelper.getXYPointFromRGB(r, g, b)
