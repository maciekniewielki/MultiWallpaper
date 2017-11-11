import tkinter as tk
from tkinter import filedialog
from construct_wall import *
from PIL import Image, ImageTk


class WallGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.state("zoomed")
        self.title("WallPy")
        self.geometry("1600x900")

        canv_size = (1280, 720)
        spacing = 4

        self.canv = tk.Canvas(self, width=canv_size[0], height=canv_size[1])
        self.confirm_button = tk.Button(self, text="Confirm", command=self.apply_wallpaper)
        self.create_gui()

        monitors = get_monitors()
        self.desktop = Desktop(monitors)

        bounds = self.desktop.get_bounds()
        height = get_size(bounds)
        scale = canv_size[0] / height[0], canv_size[1] / height[1]
        scale = [min(scale)] * 2

        self.init_canvas(scale, spacing)

    def init_canvas(self, scale, spacing):
        for ii in range(self.desktop.count):
            monitor = self.desktop.monitors[ii]
            rect = monitor.get_rect()
            # print("Rect: %s" % str(rect))
            canv_rect = self.monitor_to_canvas(self.desktop.get_bounds(), rect, scale, spacing)
            # print("Canv rect: %s" % str(canv_rect))
            rectangle = self.canv.create_rectangle(*canv_rect, width=spacing, tags=ii)
            monitor.canvas_id = rectangle
            monitor.canvas_rect = canv_rect
        self.canv.bind('<ButtonPress-1>', self.on_canvas_click)

    def monitor_to_canvas(self, bounds, rect, scale, spacing):
        canv_rect = (rect[0] - bounds[0]) * scale[0] + spacing, (rect[1] - bounds[1]) * scale[1] + spacing, \
                    (rect[2] - bounds[0]) * scale[0] - spacing, (rect[3] - bounds[1]) * scale[1] - spacing
        return canv_rect

    def create_gui(self):
        # canv.pack(fill="both", expand=True, anchor=tk.CENTER)
        self.canv.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.confirm_button.pack()

    def on_canvas_click(self, event):
        # print("Got object click at", event.x, event.y)
        item = self.canv.find_closest(event.x, event.y)[0]
        index = int(self.canv.gettags(item)[0])
        monitor = self.desktop.monitors[index]

        # Return if event is not inside the canvas rectangle
        if not ((monitor.canvas_rect[0] < event.x < monitor.canvas_rect[2]) and
                    (monitor.canvas_rect[1] < event.y < monitor.canvas_rect[3])):
            return

        which = filedialog.askopenfilename()

        # Return if no path is given
        if not which:
            return

        im = Image.open(which, "r")
        monitor.set_image(im.copy())
        width, height = [int(x) for x in get_size(monitor.canvas_rect)]
        im = monitor.generate_fit_image().resize((width, height))

        monitor._canvas_im = ImageTk.PhotoImage(im)
        self.canv.create_image(monitor.canvas_rect[:2], image=monitor._canvas_im, tags=index, anchor=tk.NW)
        self.canv.tag_raise(monitor.canvas_id)
        print("Wallpaper %s bind to rect %s" % (which, monitor.get_rect()))

    def apply_wallpaper(self):
        wallpaper = self.desktop.get_wallpaper()
        set_wallpaper(wallpaper)


if __name__ == "__main__":
    app = WallGui()
    app.mainloop()
