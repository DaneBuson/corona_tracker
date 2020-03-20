# corona_tracker
Simple script to periodically poll Covid-19 stats and display to a 128/64 OLED display on the RaspberryPi

This is based off of the great library from AdaFruit for the Adafruit SSD1306-based OLED display

The display portion is mostly cribbed from their stats.py program in the example directory

## Usage: 

It pulls from two urls, one for the world count, one for the US.

Additionally I've added the ability to display weather, and moved the URLs and city values into a config file.

In order to use weather you have to go to openweathermap.org and get an api_key and put in the config file.

It will switch between the two kinds of display for whatever duration is in the config (10 seconds by default)

```
https://www.worldometers.info/coronavirus/
https://www.worldometers.info/coronavirus/country/us/
```

Just run it with python3 - it will pull every 15 minutes (900 seconds) by default

##Installation:

Install pip3 and the other python3 libararies needed

```
sudo apt install python3-pip libopenjp2-7-dev libopenjp2-7    
sudo python3 -m pip install beautifulsoup4 requests Adafruit-SSD1306 pillow RPi.GPIO pyown
```
