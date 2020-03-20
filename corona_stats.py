# Copyright (c) 2017 Adafruit Industries
# Author: Tony DiCola & James DeVito
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import time

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import subprocess
import configparser

import re
import requests
import time
from bs4 import BeautifulSoup


#Load config file

config = configparser.ConfigParser()
config.read('tiny_tracker.ini')

corona_refresh = int(config['Corona']['refresh'])
if (corona_refresh < 1140):
    corona_refresh = 1140

wo_url = config['Corona']['world']
reg_url = config['Corona']['region']
reg_name = config['Corona']['region_name']

# Raspberry Pi pin configuration:
RST = None     # on the PiOLED this pin isnt used
# Note the following are only used with SPI:
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0

# 128x64 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)

# Initialize library.
disp.begin()

# Clear display.
disp.clear()
disp.display()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0,0,width,height), outline=0, fill=0)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0


# Load default font.
font = ImageFont.load_default()

# Alternatively load a TTF font.  Make sure the .ttf font file is in the same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
# font = ImageFont.truetype('Minecraftia.ttf', 8)

def get_corona(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    #with open("index.html") as fp:
    #    soup = BeautifulSoup(fp, "html.parser")

    corona = {'Deaths': 0, 'Infect': 0, 'Recove': 0}

    nomatch = 0
    line_count = 1 
    data = 0
    for a_divtag in soup.findAll('div'):
        divattrs = a_divtag.attrs
        line_count += 1
        if (a_divtag.has_attr('class')):
            dClass = divattrs['class'][0]
            if (dClass == 'maincounter-number'):
                #print ("DivTag = ",line_count," attrs = ", divattrs)
                #print ("    content: ",a_divtag)
                #print ("Number? : ",a_divtag.contents[0].string)
                ccount = 0
                for child in a_divtag.children:
                    ccount += 1
                    #print("#", ccount," - ", child)
                    if (ccount == 2):
                        statnum = child.string.strip()
                data += 1
                if (data == 1):
                    corona['Infect'] = statnum
                elif (data == 2):
                    corona['Deaths'] = statnum
                elif (data == 3):
                    corona['Recove'] = statnum
                #print("    Statnum = ", statnum)
    return corona 

def get_max_string (*args):
    max = 0

    for dString in args:
        if (len(dString) > max):
            max = len(dString)

    return max

# start main loop
while True:

    # Draw a black filled box to clear the image.
    draw.rectangle((0,0,width,height), outline=0, fill=0)

    #get world corona
    wo_corona = get_corona(wo_url)

    #get regional corona (us)
    reg_corona = get_corona(reg_url)

    padding = get_max_string( wo_corona['Infect'], wo_corona['Deaths'], reg_corona['Infect'], reg_corona['Deaths'])

    # format world #'s
    wo_infected = "Infected: " + wo_corona['Infect'].rjust(padding)
    wo_deaths   = "Deaths  : " + wo_corona['Deaths'].rjust(padding)

    # format regional #'s
    reg_infected = "Infected: " + reg_corona['Infect'].rjust(padding)
    reg_deaths   = "Deaths  : " + reg_corona['Deaths'].rjust(padding)

    cmd = "date |cut -c 11-23"
    stdoutdata = subprocess.getoutput(cmd)
    curTime = "CVD-19 @ " + stdoutdata.split()[0] + " PDT"
    print (curTime,"\n")

    cmd = " date |cut -c 5-11,25-30"
    stdoutdata = subprocess.getoutput(cmd)
    #curDate = " -- " +  stdoutdata.split()[0-2] + " -- "
    curDate = "  -- " +  stdoutdata + " -- "
    print (curDate,"\n")

    draw.text((x, top),        str(curTime),  font=font, fill=255)
    draw.text((x, top+8),        str(curDate),  font=font, fill=255)
    draw.text((x, top+16),    str("World #"),  font=font, fill=255)
    draw.text((x, top+24),     str(wo_infected), font=font, fill=255)
    draw.text((x, top+32),    str(wo_deaths),  font=font, fill=255)

    draw.text((x, top+41),    str(reg_name+" #"),  font=font, fill=255)
    draw.text((x, top+49),     str(reg_infected), font=font, fill=255)
    draw.text((x, top+57),    str(reg_deaths),  font=font, fill=255)

    #draw.text((x, top+25),    str(Disk),  font=font, fill=255)

    # Display image.
    disp.image(image)
    disp.display()
    time.sleep(corona_refresh) 

