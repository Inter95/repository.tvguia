# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

import urllib
import xbmc
import xbmcvfs
import os
from Utils import *
from PIL import Image, ImageFilter

THUMBS_CACHE_PATH = xbmc.translatePath("special://profile/Thumbnails/Video")
ADDON_DATA_PATH_IMAGES = os.path.join(ADDON_DATA_PATH, "images")


def filter_image(input_img, radius):
    if not xbmcvfs.exists(ADDON_DATA_PATH_IMAGES):
        xbmcvfs.mkdir(ADDON_DATA_PATH_IMAGES)
    input_img = xbmc.translatePath(urllib.unquote(input_img.encode("utf-8"))).replace("image://", "")
    if input_img.endswith("/"):
        input_img = input_img[:-1]
    cachedthumb = xbmc.getCacheThumbName(input_img)
    filename = "%s-radius_%i.png" % (cachedthumb, radius)
    targetfile = os.path.join(ADDON_DATA_PATH_IMAGES, filename)
    xbmc_vid_cache_file = os.path.join("special://profile/Thumbnails/Video", cachedthumb[0], cachedthumb)
    xbmc_cache_file = os.path.join("special://profile/Thumbnails", cachedthumb[0], cachedthumb[:-4] + ".jpg")
    if input_img == "":
        return "", ""
    if not xbmcvfs.exists(targetfile):
        img = None
        for i in range(1, 4):
            try:
                if xbmcvfs.exists(xbmc_cache_file):
                    log("image already in xbmc cache: " + xbmc_cache_file)
                    img = Image.open(xbmc.translatePath(xbmc_cache_file))
                    break
                elif xbmcvfs.exists(xbmc_vid_cache_file):
                    log("image already in xbmc video cache: " + xbmc_vid_cache_file)
                    img = Image.open(xbmc.translatePath(xbmc_vid_cache_file))
                    break
                else:
                    xbmcvfs.copy(unicode(input_img, 'utf-8', errors='ignore'), targetfile)
                    img = Image.open(targetfile)
                    break
            except:
                log("Could not get image for %s (try %i)" % (input_img, i))
                xbmc.sleep(500)
        if not img:
            return "", ""
        img.thumbnail((200, 200), Image.ANTIALIAS)
        img = img.convert('RGB')
        imgfilter = MyGaussianBlur(radius=radius)
        img = img.filter(imgfilter)
        img.save(targetfile)
    else:
        log("blurred img already created: " + targetfile)
        img = Image.open(targetfile)
    imagecolor = get_colors(img)
    return targetfile, imagecolor


def get_cached_thumb(filename):
    if filename.startswith("stack://"):
        filename = strPath[8:].split(" , ")[0]
    if filename.endswith("folder.jpg"):
        cachedthumb = xbmc.getCacheThumbName(filename)
        thumbpath = os.path.join(THUMBS_CACHE_PATH, cachedthumb[0], cachedthumb).replace("/Video", "")
    else:
        cachedthumb = xbmc.getCacheThumbName(filename)
        if ".jpg" in filename:
            cachedthumb = cachedthumb.replace("tbn", "jpg")
        elif ".png" in filename:
            cachedthumb = cachedthumb.replace("tbn", "png")
        thumbpath = os.path.join(THUMBS_CACHE_PATH, cachedthumb[0], cachedthumb).replace("/Video", "")
    return thumbpath


def get_colors(img):
    width, height = img.size
    try:
        pixels = img.load()
    except:
        return "FFF0F0F0"
    data = []
    for x in range(width/2):
        for y in range(height/2):
            cpixel = pixels[x*2, y*2]
            data.append(cpixel)
    r = 0
    g = 0
    b = 0
    counter = 0
    for x in range(len(data)):
        brightness = data[x][0] + data[x][1] + data[x][2]
        if brightness > 150 and brightness < 720:
            r += data[x][0]
            g += data[x][1]
            b += data[x][2]
            counter += 1
    if counter > 0:
        rAvg = int(r/counter)
        gAvg = int(g/counter)
        bAvg = int(b/counter)
        Avg = (rAvg + gAvg + bAvg) / 3
        minBrightness = 130
        if Avg < minBrightness:
            Diff = minBrightness - Avg
            for color in [rAvg, gAvg, bAvg]:
                if color <= (255 - Diff):
                    color += Diff
                else:
                    color = 255
        imagecolor = "FF%s%s%s" % (format(rAvg, '02x'), format(gAvg, '02x'), format(bAvg, '02x'))
    else:
        imagecolor = "FFF0F0F0"
    log("Average Color: " + imagecolor)
    return imagecolor


class FilterImageThread(threading.Thread):

    def __init__(self, image="", radius=25):
        threading.Thread.__init__(self)
        self.filterimage = image
        self.radius = radius

    def run(self):
        try:
            self.image, self.imagecolor = filter_image(self.filterimage, self.radius)
        except:
            self.image = ""
            self.imagecolor = ""
            log("exception. probably android PIL issue.")


class MyGaussianBlur(ImageFilter.Filter):
    name = "GaussianBlur"

    def __init__(self, radius=2):
        self.radius = radius

    def filter(self, image):
        return image.gaussian_blur(self.radius)
