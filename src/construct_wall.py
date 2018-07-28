from ctypes import *
from PIL import Image
import os
from sys import argv
from tempfile import NamedTemporaryFile
from threading import Timer


VERBOSE = True


def log(text):
    if VERBOSE:
        print(text)


def offset(bounds, dx, dy):
    bounds = list(bounds)
    bounds[0] += dx
    bounds[2] += dx
    bounds[1] += dy
    bounds[3] += dy
    return tuple(bounds)


def get_size(bounds):
    return bounds[2] - bounds[0], bounds[3] - bounds[1]


class Desktop:

    def __init__(self, monitors):
        self.monitors = monitors
        self.count = len(monitors)
        bounds = Desktop.get_outer_bound(monitors)
        offset_x = - bounds[0]
        offset_y = - bounds[1]
        # Offset the desktop to begin in 0,0
        self.offset_monitors(offset_x, offset_y)
        bounds = offset(bounds, offset_x, offset_y)
        self.x1, self.y1, self.x2, self.y2 = bounds
        self.width = self.x2 - self.x1
        self.height = self.y2 - self.y1


    @staticmethod
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

    @staticmethod
    def get_num_monitors():
        return windll.user32.GetSystemMetrics(80)

    @staticmethod
    def get_outer_bound(monitors):
        return min(monitors, key=lambda x: x.x1).x1, min(monitors, key=lambda x: x.y1).y1, \
               max(monitors, key=lambda x: x.x2).x2, max(monitors, key=lambda x: x.y2).y2

    def get_bounds(self):
        return self.x1, self.y1, self.x2, self.y2

    def offset_monitors(self, dx, dy):
        for ii in range(self.count):
            self.monitors[ii].apply_offset(dx, dy)

    def get_wallpaper(self):
        wallpaper = Image.new("RGB", (self.width, self.height))

        for monitor in self.monitors:
            image = monitor.generate_image()
            wallpaper.paste(image, (monitor.x1, monitor.y1))
        return wallpaper


class Monitor:

    def __init__(self, x1, y1, x2, y2, fit_mode="stretch", im_path=None, image=None):
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        self.width = x2 - x1
        self.height = y2 - y1
        self.fit_mode = fit_mode

        self.im_path = None
        self.im = None
        if image is not None:
            self.load_image(image)
        elif im_path is not None:
            self.load_image_file(im_path)

    def __lt__(self, other):  # First top to bottom, then left to right
        if self.y1 == other.y1:
            return self.x1 < other.x1
        return self.y1 < other.y1

    def __str__(self):
        return "%d %d %d %d" % (self.x1, self.x2, self.y1, self.y2)

    def get_rect(self):
        return self.x1, self.y1, self.x2, self.y2

    def get_size(self):
        return self.width, self.height

    def apply_offset(self, dx, dy):
        self.x1 += dx
        self.x2 += dx
        self.y1 += dy
        self.y2 += dy

    def load_image(self, image):
        """Loads the image from existing Image object."""
        self.im = image.copy()
        self.im_path = "Memory"

    def load_image_file(self, image_path):
        """Loads the image from path."""
        self.im_path = image_path
        self.im = Image.open(image_path)
        self.im.load()

    def generate_image(self, fit_mode=None):
        """Returns an Image with applied fit mode."""
        if not self.im:
            log("The image for monitor %s isn't loaded. Returning black background...")
            return Image.new("RGB", (self.width, self.height))

        if fit_mode is None:
            fit_mode = self.fit_mode

        if fit_mode == "stretch":
            return self.im.resize((self.width, self.height))
        elif fit_mode == "cut":
            return self.im.crop((0, 0, self.width, self.height))
        else:
            message = "%s: This fit mode doesn't exist" % fit_mode
            raise NotImplementedError(message)


def set_wallpaper(image):
    f = NamedTemporaryFile(delete=False)
    image.save(f, format="PNG")
    windll.user32.SystemParametersInfoW(20, 0, f.name, 1)
    f.close()

    # Delete the temporary file after a few seconds to give time for wallpaper change
    Timer(10, lambda: os.remove(f.name)).start()

    image.save("wallpaper_temp.png", format="PNG")


def print_usage():
    print("Usage: %s <image_path_1> <image_path_2> ... <output_file>" % argv[0])


def main():
    monitors = Desktop.get_monitors()

    if len(monitors) != len(argv) - 2:
        print("Wrong number of arguments.")
        print("You supplied %d arguments (with output file) and have %d monitors" % (len(argv) - 1, len(monitors)))
        print_usage()
        exit(1)

    for monitor, filename in zip(monitors, argv[1:-1]):
        monitor.load_image_file(filename)

    desktop = Desktop(monitors)
    wallpaper = desktop.get_wallpaper()
    wallpaper.save(argv[-1])
    # set_wallpaper(wallpaper)


if __name__ == "__main__":
    main()
