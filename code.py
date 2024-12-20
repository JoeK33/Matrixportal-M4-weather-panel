# SPDX-FileCopyrightText: 2020 John Park for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# Matrix Weather display
# For Metro M4 Airlift with RGB Matrix shield, 64 x 32 RGB LED Matrix display

"""
This example queries the Open Weather Maps site API to find out the current
weather for your location... and display it on a screen!
if you can find something that spits out JSON data, we can display it
"""
import time
import board
import microcontroller
from digitalio import DigitalInOut, Direction, Pull
from adafruit_matrixportal.network import Network
from adafruit_matrixportal.matrix import Matrix
import openweather_graphics  # pylint: disable=wrong-import-position

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

if hasattr(board, "D12"):
    jumper = DigitalInOut(board.D12)
    jumper.direction = Direction.INPUT
    jumper.pull = Pull.UP
    is_imperial = jumper.value
elif hasattr(board, "BUTTON_DOWN") and hasattr(board, "BUTTON_UP"):
    button_down = DigitalInOut(board.BUTTON_DOWN)
    button_down.switch_to_input(pull=Pull.UP)

    button_up = DigitalInOut(board.BUTTON_UP)
    button_up.switch_to_input(pull=Pull.UP)
    if not button_down.value:
        print("Down Button Pressed")
        microcontroller.nvm[0] = 1
    elif not button_up.value:
        print("Up Button Pressed")
        microcontroller.nvm[0] = 0
    print(microcontroller.nvm[0])
    is_imperial = microcontroller.nvm[0]
else:
    is_imperial = False

if is_imperial:
    UNITS = "imperial"  # can pick 'imperial' or 'metric' as part of URL query
    print("Jumper set to imperial")
else:
    UNITS = "metric"
    print("Jumper set to metric")

# Use cityname, country code where countrycode is ISO3166 format.
# E.g. "New York, US" or "London, GB"
LOCATION = secrets["city"]
print("Getting weather for {}".format(LOCATION))
# Set up from where we'll be fetching data
DATA_SOURCE = (
    "http://api.openweathermap.org/data/2.5/weather?q=" + LOCATION + "&units=" + UNITS
)
DATA_SOURCE += "&appid=" + secrets["openweather_token"]
# You'll need to get a token from openweather.org, looks like 'b6907d289e10d714a6e88b30761fae22'
# it goes in your secrets.py file on a line such as:
# 'openweather_token' : 'your_big_humongous_gigantor_token',
DATA_LOCATION = []
SCROLL_HOLD_TIME = 0  # set this to hold each line before finishing scroll

# --- Display setup ---
matrix = Matrix()
network = Network(status_neopixel=board.NEOPIXEL, debug=True)
if UNITS in ("imperial", "metric"):
    gfx = openweather_graphics.OpenWeather_Graphics(
        matrix.display, am_pm=True, units=UNITS
    )

print("gfx loaded")
localtime_refresh = None
display_refresh = None
weather_refresh = None
weather_value = None
while True:
    # only query the online time once per hour (and on first run)
    if (not localtime_refresh) or (time.monotonic() - localtime_refresh) > 3600:
        try:
            print("Trying to get time from internet!")
            network.get_local_time()
            localtime_refresh = time.monotonic()
        except RuntimeError as e:
            print("Some error occured, retrying! -", e)
            continue

    # only query the weather every 10 minutes (and on first run)
    if (not weather_refresh) or (time.monotonic() - weather_refresh) > 600:
        try:
            value = network.fetch_data(DATA_SOURCE, json_path=(DATA_LOCATION,))
            print("Response is", value)
            weather_value = value
            weather_refresh = time.monotonic()
        except RuntimeError as e:
            print("Some error occured, retrying! -", e)
            continue

    # Update display every minute (mostly to update clock)
    if (not display_refresh) or (time.monotonic() - display_refresh) > 60:
        try:
            print("Updating display")
            localtime = time.localtime()
            # between the hours of midnight and 8am, display a black image to turn screen "off"
            if localtime[3] < 8:
                print("It's late, showing black screen")
                gfx.display_black()
            else:
                gfx.display_weather(weather_value, localtime)

            display_refresh = time.monotonic()
        except RuntimeError as e:
            print("Some error occured, retrying! -", e)
            continue

    gfx.scroll_next_label()
    # Pause between labels
    time.sleep(SCROLL_HOLD_TIME)
