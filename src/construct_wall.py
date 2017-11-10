from ctypes import *
from PIL import Image
import os
from sys import argv
from tempfile import NamedTemporaryFile
from threading import Timer


def get_bounds(monitors):
    return min(monitors, key=lambda x: x.x1).x1, min(monitors, key=lambda x: x.y1).y1, \
           max(monitors, key=lambda x: x.x2).x2, max(monitors, key=lambda x: x.y2).y2


def offset(bounds, dx, dy):
    bounds = list(bounds)
    bounds[0] += dx
    bounds[2] += dx
    bounds[1] += dy
    bounds[3] += dy
    return tuple(bounds)


class Desktop:

    def __init__(self, monitors):
        self.count = len(monitors)
        bounds = get_bounds(monitors)
        offset_x = - bounds[0]
        offset_y = - bounds[1]
        bounds = offset(bounds, offset_x, offset_y)
        self.x1, self.y1, self.x2, self.y2 = bounds
        self.width = self.x2 - self.x1
        self.height = self.y2 - self.y1

        self.monitors = monitors
        self.offset_monitors(offset_x, offset_y)

    def offset_monitors(self, dx, dy):
        for ii in range(self.count):
            self.monitors[ii].apply_offset(dx, dy)

    def get_wallpaper(self):
        wallpaper = Image.new("RGB", (self.width, self.height))

        for monitor in self.monitors:
            image = monitor.generate_fit_image()
            wallpaper.paste(image, (monitor.x1, monitor.y1))
        return wallpaper


class Monitor:
    def __init__(self, x1, y1, x2, y2, fit_mode="stretch", source="local"):
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        self.width = x2 - x1
        self.height = y2 - y1
        self.im = None
        self.fit_mode = fit_mode
        self.source = source
        self.canvas_rect = ()

    def __lt__(self, other):  # First top to bottom, then left to right
        if self.y1 == other.y1:
            return self.x1 < other.x1
        return self.y1 < other.y1

    def __str__(self):
        return "%d %d %d %d" % (self.x1, self.x2, self.y1, self.y2)

    def set_image(self, image):
        self.im = image

    def get_rect(self):
        return self.x1, self.y1, self.x2, self.y2

    def get_size(self):
        return self.width, self.height

    def apply_offset(self, dx, dy):
        self.x1 += dx
        self.x2 += dx
        self.y1 += dy
        self.y2 += dy

    def generate_fit_image(self):
        """Returns an Image with applied fit mode."""
        if self.fit_mode == "stretch":
            return self.im.resize((self.width, self.height))
        else:
            raise NotImplementedError("%s: This fit mode doesn't exist" % self.fit_mode)


def set_wallpaper(image):
    f = NamedTemporaryFile(delete=False)
    image.save(f, format="PNG")
    windll.user32.SystemParametersInfoW(20, 0, f.name, 0)
    f.close()
    # Delete the temporary file after 5 seconds to give time for wallpaper change
    Timer(5, lambda: os.remove(f.name)).run()


def get_num_monitors():
    return windll.user32.GetSystemMetrics(80)


def get_monitors():
    class RectC(Structure):
        _fields_ = [("x1", c_long), ("y1", c_long), ("x2", c_long), ("y2", c_long)]

    c_declaration = CFUNCTYPE(c_byte, POINTER(c_int), POINTER(c_int), POINTER(RectC), c_byte)
    _monitors = []

    def callback_python(hMonitor, hdcMonitor, lprcMonitor, dwData):
        rect = lprcMonitor.contents
        _monitors.append(Monitor(rect.x1, rect.y1, rect.x2, rect.y2))
        return True

    callback_c = c_declaration(callback_python)

    windll.user32.EnumDisplayMonitors(None, None, callback_c, 0)
    return sorted(_monitors)


def main():
    monitors = get_monitors()
    # path = "C:\\Users\\Maciek\\Desktop\\wallpaper.png"

    if len(monitors) != len(argv) - 1:
        print("You supplied %d arguments and you have %d monitors" % (len(argv) - 1, len(monitors)))
        exit(1)

    for ii in range(len(monitors)):
        monitors[ii].set_image(Image.open(argv[ii + 1], "r"))

    desktop = Desktop(monitors)
    wallpaper = desktop.get_wallpaper()
    set_wallpaper(wallpaper)


if __name__ == "__main__":
    main()
