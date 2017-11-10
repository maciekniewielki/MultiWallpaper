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

        size = (1280, 720)
        width = 4

        self.monitors = get_monitors()
        self.desktop = Desktop(self.monitors)
        # for x in [0, 2]:
        #     for y in [0, 2]:
        #         self.monitors.append(Monitor(1920*x, y*1080, 1920*(x+1), (y+1)*1080))

        # self.monitors.append(Monitor(1920 +300, 1080, 1920 * 2-200, 2 * 1080+500))

        # self.monitors.append(Monitor(1920 + 300, -1500, 1920 * 2 - 200,  -500))
        self.rect_images = [0] * len(self.monitors)
        bounds = get_bounds(self.monitors)
        scale = size[0]/(bounds[2] - bounds[0]), size[1]/(bounds[3] - bounds[1])
        scale = [min(scale)]*2

        self.canv = tk.Canvas(self, width=size[0], height=size[1])
        self.confirm_button = tk.Button(self, text="Confirm", command=self.apply_wallpaper)

        # canv.pack(fill="both", expand=True, anchor=tk.CENTER)
        self.canv.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.confirm_button.pack()
        self.monitors_id = []
        self.rects = []
        for index, monitor in enumerate(self.monitors):
            rect = monitor.get_rect()
            print("Rect: %s" % str(rect))
            canv_rect = (rect[0]-bounds[0])*scale[0]+width, (rect[1]-bounds[1])*scale[1]+width, \
                        (rect[2]-bounds[0])*scale[0]-width, (rect[3]-bounds[1])*scale[1]-width
            print("Canv rect: %s" % str(canv_rect))
            rectangle = self.canv.create_rectangle(*canv_rect, width=4, tags=index)
            self.monitors_id.append(rectangle)
            self.rects.append(canv_rect)

        def on_canvas_click(event):
            print('Got object click', event.x, event.y)
            item = self.canv.find_closest(event.x, event.y)[0]
            which = filedialog.askopenfilename()
            index = int(self.canv.gettags(item)[0])
            im = Image.open(which, "r")
            self.monitors[index].set_image(im.copy())
            im = im.resize((int(self.rects[index][2]-self.rects[index][0]), int(self.rects[index][3]-self.rects[index][1])),
                      Image.ANTIALIAS)
            self.rect_images[index] = ImageTk.PhotoImage(im)
            self.canv.create_image((self.rects[index][0], self.rects[index][1]), image=self.rect_images[index], tags=index, anchor=tk.NW)
            print("Image rect: %s" % str(self.rects[index]))
            self.canv.tag_raise(self.monitors_id[index])
            print("Number %d bind to wallpaper %s" % (index, which))

        self.canv.bind('<ButtonPress-1>', on_canvas_click)

    def apply_wallpaper(self):
        desktop = Desktop(self.monitors)
        wallpaper = desktop.get_wallpaper()
        set_wallpaper(wallpaper)


if __name__ == "__main__":
    app = WallGui()
    app.mainloop()
