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

import re
import requests
import time
from bs4 import BeautifulSoup

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
                        statnum = child.string
                data += 1
                if (data == 1):
                    corona['Infect'] = statnum
                elif (data == 2):
                    corona['Deaths'] = statnum
                elif (data == 3):
                    corona['Recove'] = statnum
                #print("    Statnum = ", statnum)
    return corona 

# start main loop
while True:

    # Draw a black filled box to clear the image.
    draw.rectangle((0,0,width,height), outline=0, fill=0)

    # Shell scripts for system monitoring from here : https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load
    #cmd = "hostname -I | cut -d\' \' -f1"
    #IP = subprocess.check_output(cmd, shell = True )
    #cmd = "top -bn1 | grep load | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'"
    #CPU = subprocess.check_output(cmd, shell = True )
    #cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
    #MemUsage = subprocess.check_output(cmd, shell = True )
    #cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%dGB %s\", $3,$2,$5}'"
    #Disk = subprocess.check_output(cmd, shell = True )

    #get world corona
    url = 'https://www.worldometers.info/coronavirus/'
    web_corona = get_corona(url)
    # Write two lines of text.
    infected = "Infected: " + web_corona['Infect']
    deaths   = "Deaths  : " + web_corona['Deaths']

    url = 'https://www.worldometers.info/coronavirus/country/us/'
    web_corona = get_corona(url)
    # Write two lines of text.
    us_infected = "Infected: " + web_corona['Infect']
    us_deaths   = "Deaths  : " + web_corona['Deaths']

    cmd = "date |cut -c 11-23"
    #curTime = subprocess.check_output(cmd, shell = True )
    stdoutdata = subprocess.getoutput(cmd)
    curTime = "CVD-19 @ " + stdoutdata.split()[0] + " PDT"
    print (curTime,"\n")

    draw.text((x, top),        str(curTime),  font=font, fill=255)
    draw.text((x, top+8),        str("  ----------------"),  font=font, fill=255)
    draw.text((x, top+16),    str("World #"),  font=font, fill=255)
    draw.text((x, top+24),     str(infected), font=font, fill=255)
    draw.text((x, top+32),    str(deaths),  font=font, fill=255)

    draw.text((x, top+41),    str("US #"),  font=font, fill=255)
    draw.text((x, top+49),     str(us_infected), font=font, fill=255)
    draw.text((x, top+57),    str(us_deaths),  font=font, fill=255)

    #draw.text((x, top+25),    str(Disk),  font=font, fill=255)

    # Display image.
    disp.image(image)
    disp.display()
    time.sleep(900) #every 15 minutes

