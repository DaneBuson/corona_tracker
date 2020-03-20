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
import pyowm
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

weather_refresh = int(config['Weather']['refresh'])
if (weather_refresh < 300):
    weather_refresh = 300

#how long each 'frame' stays up
duration = int(config['General']['duration'])

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
    try:
        response = requests.get(url)
    except ConnectionError:
        corona = {'Error': "Connection"}
        return 
        
    soup = BeautifulSoup(response.text, "html.parser")

    #with open("index.html") as fp:
    #    soup = BeautifulSoup(fp, "html.parser")

    corona = {'Deaths': 0, 'Infect': 0, 'Recove': 0, 'Error': "None"}

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

def get_weather_data(config):
    cities = {"city_num":0}

    c_weather = config['Weather']

    api_key = config['Weather']['ow_apikey']

    #connect to openweather with our key
    owm = pyowm.OWM(api_key)

    city_list = []
    for jj in ('city1','city2','city3'):
        if (jj in c_weather.keys()):
            tcity = c_weather[jj].strip()
            city_list.append(c_weather[jj])

    #TODO - units SI/Imperial
    city_num = 0
    for city in city_list:
        print ("Getting own for '",city,"'\n")
        observation = owm.weather_at_place(city)
        w = observation.get_weather()

        CC = "CC"+str(city_num)
        cities[CC] = {'name': city}
        cities[CC]['wind_speed'] = w.get_wind()['speed']
        #cities[CC]['wind_deg'] = w.get_wind()['deg'] #direction

        #tempF = w.get_temperature('fahrenheit')
        temp =  w.get_temperature('celsius')

        cities[CC]['temp'] = {'temp_cur': int(temp['temp']), 'temp_max': int(temp['temp_max']), 'temp_min': int(temp['temp_min'])}
        cities[CC]['humidity'] = w.get_humidity()
        status = w.get_status()
        cities[CC]['status'] = status

        #print ("\tWeather in ",city," is ",status)
        city_num += 1

    cmd = "date |cut -c 11-23"
    stdoutdata = subprocess.getoutput(cmd)
    cities['timestamp'] = "Time: " + stdoutdata.split()[0] + " PDT"
    
    cities['city_num'] = city_num
    return cities


def get_max_string (*args):
    max = 0

    for dString in args:
        if (len(dString) > max):
            max = len(dString)

    return max


last_refresh = {'corona':0,'weather':0}
wo_infected = ""
wo_deaths = ""
reg_infected = ""
reg_deaths = ""

display_frame = 0
display_city = 0
cities = {}

# start main loop
while True:

    if ((time.time() - last_refresh['corona'])  > corona_refresh):
        #get world corona
        errors = 0
        wo_corona = get_corona(wo_url)
        if (wo_corona['Error'] != 'None'):
            print ("Error while trying to get world stats\n\t",wo_corona['Error'])
            errors += 1

        #get regional corona (us)
        reg_corona = get_corona(reg_url)
        if (reg_corona['Error'] != 'None'):
            print ("Error while trying to get regional stats\n\t",reg_corona['Error'])
            errors += 1

        if (errors == 0):
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
            cmd = " date |cut -c 5-11,25-30"
            stdoutdata = subprocess.getoutput(cmd)
            #curDate = " -- " +  stdoutdata.split()[0-2] + " -- "
            curDate = "  -- " +  stdoutdata + " -- "
    
            print (curTime," - ",curDate,"\n")
            last_refresh['corona'] = time.time()
        else:
            print ("Skipping refresh - errors trying to get data")

    if ((time.time() - last_refresh['weather'])  > weather_refresh):
        cities = get_weather_data (config)
        last_refresh['weather'] = time.time()

    # Drawscreen
    # Draw a black filled box to clear the image.
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    
    if (display_frame == 0): #draw corona
        #print ("\nDisplaying CVD-19 stats")
        draw.text((x, top),        str(curTime),  font=font, fill=255)
        draw.text((x, top+8),        str(curDate),  font=font, fill=255)
        draw.text((x, top+16),    str("World #"),  font=font, fill=255)
        draw.text((x, top+24),     str(wo_infected), font=font, fill=255)
        draw.text((x, top+32),    str(wo_deaths),  font=font, fill=255)

        draw.text((x, top+41),    str(reg_name+" #"),  font=font, fill=255)
        draw.text((x, top+49),     str(reg_infected), font=font, fill=255)
        draw.text((x, top+57),    str(reg_deaths),  font=font, fill=255)
    elif (display_frame == 1): #draw one of the cities
        cmd = " date |cut -c 5-11,25-30"
        stdoutdata = subprocess.getoutput(cmd)
        curDate = "  -- " +  stdoutdata + " -- "

        city = cities["CC"+str(display_city)]
        #print ("\nDisplaying Weather for ",city['name'], "- DC = ",display_city)
        draw.text((x, top),      str(cities['timestamp']), font=font, fill=255)
        draw.text((x, top+8),      str(curDate), font=font, fill=255)
        draw.text((x, top+16),    str("City: "+city['name']),  font=font, fill=255)

        temp_str1 = "Temp: " + str(city['temp']['temp_cur'])
        temp_str2 = "Max/Min: " + str(city['temp']['temp_max']) + "/" + str(city['temp']['temp_min'])
        draw.text((x, top+24),    str(temp_str1),  font=font, fill=255)
        draw.text((x, top+32),    str(temp_str2),  font=font, fill=255)
        draw.text((x, top+48),    str("Cond: "+str(city['status'])),  font=font, fill=255)
        draw.text((x, top+40),    str("Wind: "+str(city['wind_speed'])),  font=font, fill=255)

        display_city = (display_city + 1) % cities['city_num']

    display_frame = (display_frame + 1) %2

    # Display image.
    disp.image(image)
    disp.display()
    time.sleep(duration) 

