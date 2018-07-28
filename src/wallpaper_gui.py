import tkinter as tk
from tkinter import filedialog
from construct_wall import *
from PIL import Image, ImageTk


FIT_MODES = "stretch cut".split()
PLANNED_FIT_MODES = "center fit fill stretch tile cut".split()


class WallGui(tk.Tk):
    # TODO Refactor!
    def __init__(self):
        super().__init__()
        self.state("zoomed")
        self.title("WallPy")
        self.geometry("1600x900")
        self.configure(bg="white")

        canv_size = (1280, 720)
        spacing = 4

        # TODO add a button to change wallpaper fit_mode to span

        self.canv = tk.Canvas(self, width=canv_size[0], height=canv_size[1])
        self.confirm_button = tk.Button(self, text="Confirm", command=self.apply_wallpaper)
        self.popup_menu = tk.Menu(self, tearoff=0)
        self.fit_mode_menu = tk.Menu(self.popup_menu, tearoff=0)
        for mode in FIT_MODES:
            self.fit_mode_menu.add_command(label=mode, command=lambda x=mode: self.set_fit_mode(x))

        self.popup_menu.add_cascade(label="Set fit mode", menu=self.fit_mode_menu)
        self.info_frame = InfoFrame(self, browse_callback=self.on_browse)
        self.info_frame.hide_info()
        self.create_gui()

        monitors = get_monitors()
        self.desktop = Desktop(monitors)
        self._selected_monitor = None

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
            rectangle = self.canv.create_rectangle(*canv_rect, width=spacing, outline="black")
            monitor.canvas_id = rectangle
            monitor.canvas_rect = canv_rect
        self.canv.bind('<ButtonPress-1>', self.on_canvas_click)
        self.canv.bind('<ButtonPress-3>', self.on_monitor_click)

    def monitor_to_canvas(self, bounds, rect, scale, spacing):
        canv_rect = (rect[0] - bounds[0]) * scale[0] + spacing, (rect[1] - bounds[1]) * scale[1] + spacing, \
                    (rect[2] - bounds[0]) * scale[0] - spacing, (rect[3] - bounds[1]) * scale[1] - spacing
        return canv_rect

    def create_gui(self):
        # canv.pack(fill="both", expand=True, anchor=tk.CENTER)
        self.canv.place(relx=0.5, rely=0.45, anchor=tk.CENTER)
        self.confirm_button.pack()
        self.info_frame.pack(side="bottom", pady=10)

    def event_inside_monitor(self, monitor, event):
        return ((monitor.canvas_rect[0] < event.x < monitor.canvas_rect[2]) and
                    (monitor.canvas_rect[1] < event.y < monitor.canvas_rect[3]))

    def on_monitor_click(self, event):
        monitor = self.event_to_monitor(event)
        if not monitor:
            return
        print("Clicked monitor: ", monitor)
        # self._selected_monitor = monitor
        self.popup_menu.post(event.x_root, event.y_root)

    def event_to_monitor(self, event):
        for monitor in self.desktop.monitors:
            if self.event_inside_monitor(monitor, event):
                return monitor
        return None

    def on_canvas_click(self, event):
        # print("Got object click at", event.x, event.y)
        monitor = self.event_to_monitor(event)

        # Return if event is not inside the canvas rectangle
        if not monitor:
            self.info_frame.hide_info()
            self.deselect_active_monitor()
            self._selected_monitor = None
            return
        self.info_frame.show_info()

        self.deselect_active_monitor()
        self.canv.itemconfigure(monitor.canvas_id, outline="blue")
        self._selected_monitor = monitor
        # self.info_frame.show_monitor(self._selected_monitor)
        self.info_frame.update_selected()

    def on_browse(self):

        which = filedialog.askopenfilename()

        # Return if no path is given
        if not which:
            return
        monitor = self._selected_monitor
        im = Image.open(which, "r")
        monitor.set_image(im)
        width, height = [int(x) for x in get_size(monitor.canvas_rect)]
        im = monitor.generate_fit_image().resize((width, height))

        monitor._canvas_im = ImageTk.PhotoImage(im)
        image = self.canv.create_image(monitor.canvas_rect[:2], image=monitor._canvas_im, anchor=tk.NW)
        self.canv.tag_lower(image)  # Lowers the image under the rectangle
        self.info_frame.update_selected()
        print("Wallpaper %s bind to rect %s" % (which, monitor.get_rect()))

    def deselect_active_monitor(self):
        if self._selected_monitor:
            self.canv.itemconfigure(self._selected_monitor.canvas_id, outline="black")
            self._selected_monitor = None

    def apply_wallpaper(self):
        # TODO add a file dialog to save the wallpaper. Better don't use tempfile
        wallpaper = self.desktop.get_wallpaper()
        set_wallpaper(wallpaper)

    def set_fit_mode(self, mode):
        if not self._selected_monitor:
            return
        self._selected_monitor.fit_mode = mode
        # TODO update the image in the canvas to reflect fit_mode change
        self.info_frame.update_selected()


class CanvasMonitor:
    def __init__(self, monitor):
        self.monitor = monitor

        # TODO move stuff from the Monitor class here


class InfoFrame(tk.Frame):
    def __init__(self, parent, browse_callback=None, fit_callback=None):
        super().__init__(parent)
        self.columnconfigure(0)
        self.columnconfigure(1)
        self.columnconfigure(2)
        self.rowconfigure(0)
        self.rowconfigure(1)
        # font = tkFont.Font(font="TkDefaultFont").configure(size=40)
        font = (None, 20)

        self.hide_frame = tk.Frame(self, bg="white")
        self.hide_frame.pack()
        tk.Label(self, text="Path:", font=font, bg="white").grid(in_=self.hide_frame, row=0, column=0, sticky="w")
        tk.Label(self, text="Fit mode:", font=font, bg="white").grid(in_=self.hide_frame, row=1, column=0)
        self.path_label = tk.Label(self, text="None", font=("Courier", 20), bg="white")
        self.path_browse = tk.Button(self, text="Browse", command=browse_callback, font=font, bg="white")
        self.fit_mode_label = tk.Label(self, text="stretch", font=("Courier", 20), bg="white")
        self.path_label.grid(in_=self.hide_frame, row=0, column=1, padx=20)
        self.path_browse.grid(in_=self.hide_frame, row=0, column=2)
        self.fit_mode_label.grid(in_=self.hide_frame, row=1, column=1)

    def show_monitor(self, monitor):
        if monitor.im:
            self.path_label.config(text=monitor.im.filename)
        else:
            self.path_label.config(text="None")
        self.fit_mode_label.config(text=monitor.fit_mode)

    def update_selected(self):
        self.show_monitor(super()._root()._selected_monitor)

    def hide_info(self):
        self.hide_frame.lift()

    def show_info(self):
        self.hide_frame.lower()

if __name__ == "__main__":
    app = WallGui()
    app.mainloop()
