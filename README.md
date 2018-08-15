# MultiWallpaper
Python program that generates a wallpaper for a multi-monitor desktop. Currently it consists of two scripts. Windows only atm.
# construct_wall.py
It is a console program which takes as many images as you have monitors (top-down and left-right order) and outputs a merged wallpaper image, which should correspond to the current monitor configuration. Just set the wallpaper fit mode to "span" and you can set the image as wallpaper.
# wallpaper_gui.py
This script uses some wallpaper-building functionality from the console version and adds a simple gui. You can manually select an image for each of your monitors, as well as an additional fit mode.
