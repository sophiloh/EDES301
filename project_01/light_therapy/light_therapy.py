"""
--------------------------------------------------------------------------
Smart Light Therapy
--------------------------------------------------------------------------
License:   
Copyright 2025 Sophianne Loh

Redistribution and use in source and binary forms, with or without 
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this 
list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, 
this list of conditions and the following disclaimer in the documentation 
and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors 
may be used to endorse or promote products derived from this software without 
specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE 
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL 
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
--------------------------------------------------------------------------

Use the following hardware components to make a smart light therapy device:  
  - HT16K33 Display
  - Buttons (2)
  - BH1750 Light Sensor
  - DS3231 Real Time Clock Module
  - WS2812B 5050 LED Strip

Requirements:
  - Hardware:
    - HT16K33 Display
        - Displays time in military time format, except when LED strip light 
        intensity is being manually adjusted via buttons
    - Buttons(2)
        - Increase Button (green cap) will increase LED strip light intensity
        by 50 units (on 0-255 scale)
        - Decrease Button (yellow cap) will decrease LED strip light intensity
        by 50 units (on 0-255 scale)
    - BH1750 Light Sensor 
        - Continuously monitors ambient light intensity in units of lux. If
        ambient light intensity falls outside of threshold brightness level,
        will lead to adjustment of LED strip light intensity
    - DS3231 Real Time Clock Module
        - Keeps track of time even without connection to Internet. Thus, allows
        the LED strip to change color and intensity to mimic the sunlight levels
        expected during a particular time of day.
    - WS2812B 5050 LED Strip
        - Outputs light intensity and color based on time of day, ambient light,
        and user adjustment

Uses:
  - HT16K33 display library developed in EDES 301 class
    - Library updated to add "set_digit_raw()", "set_colon()"
  - DS3231 Adafruit library
  - BH1750 Adafruit library
  - Button library developed in EDES 301 class

"""

# Imports
import time
import board
import busio
import adafruit_bh1750
import adafruit_ds3231
import opc
import ht16k33
import button

# ------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------
MIN_BRIGHTNESS = 0
MAX_BRIGHTNESS = 255
BRIGHTNESS_STEP = 50
DISPLAY_TIMEOUT = 1  # seconds
# ------------------------------------------------------------------------
# Global variables
# ------------------------------------------------------------------------

brightness = 100
last_button_press_time = 0
showing_brightness = False

# ------------------------------------------------------------------------
# Functions / Classes
# ------------------------------------------------------------------------

# Initialize Components
i2c = board.I2C()
led_strip = LEDStrip()
sensor = adafruit_bh1750.BH1750(i2c)
rtc = adafruit_ds3231.DS3231(i2c)
hex_display = ht16k33.HT16K33(1, 0x70)

# Buttons
increase_btn = button.Button("P2_4", press_low=True)
decrease_btn = button.Button("P2_2", press_low=True)

# define LED class:

class LEDStrip:
    """ LED strip class """
    def __init__(self, address='localhost:7890', num_leds=240, color=(255, 255, 255)):
        self.client = opc.Client(address)
        self.num_leds = num_leds
        self.color = color
        self.brightness = 128

        if not self.client.can_connect():
            print(f"WARNING: Could not connect to {address}")

    def set_brightness(self, brightness):
        self.brightness = max(0, min(255, brightness))
        scaled_color = tuple(int(c * self.brightness / 255) for c in self.color)
        pixels = [scaled_color] * self.num_leds
        self.client.put_pixels(pixels, channel=0)

    def off(self):
        self.client.put_pixels([(0, 0, 0)] * self.num_leds, channel=0)
        
def set_rtc_time():
    """ allows for manually setting system time stored in device """
    # Define the date and time (Year, Month, Day, Hour, Minute, Second, Weekday, Julian day, DST)
    current_time = time.struct_time((2025, 4, 24, 12, 00, 0, 3, 114, -1))  # 2 = Wednesday
    rtc.datetime = current_time
    print("RTC time set to:", current_time)

# Uncomment the following line if you want to set RTC time when the program starts:
set_rtc_time()

def update_leds():
    """ sets color and intensity of LEDs """
    print(f"Setting LED brightness to: {brightness}")
    led_strip.set_brightness(brightness)

def get_target_brightness_and_color(hour):
    """ defines brightness and color (R, G, B) for different times of day """
    if 6 <= hour < 7:      # Sunrise
        return 100, (255, 100, 0)   # warm orange
    elif 7 <= hour < 10:   # Morning
        return 150, (255, 255, 200) # soft white
    elif 10 <= hour < 16:  # Midday
        return 200, (255, 255, 255) # bright white
    elif 16 <= hour < 19:  # Golden hour
        return 140, (255, 180, 50)  # golden orange
    elif 19 <= hour < 20:  # Dusk
        return 80, (150, 100, 100)  # soft pinkish dim
    else:                  # Night
        return 50, (50, 50, 100)    # dim cool blue

def get_light_thresholds(hour):
    """ returns (too_dark_threshold, too_bright_threshold) for different times
    of the day """
    if 6 <= hour < 7:       # Sunrise
        return 30, 150
    elif 7 <= hour < 10:    # Morning
        return 80, 250
    elif 10 <= hour < 16:   # Midday
        return 100, 350
    elif 16 <= hour < 19:   # Golden hour
        return 60, 200
    elif 19 <= hour < 20:   # Dusk
        return 30, 120
    else:                   # Night
        return 10, 80

def check_auto_brightness():
    """ checks ambient lighting from BH1750 and compares to target brightness 
    and thresholds for each time of day """
    global brightness
    hour = rtc.datetime.tm_hour
    light_level = sensor.lux

    # Get time-based targets
    target_brightness, target_color = get_target_brightness_and_color(hour)

    # Time-aware thresholds
    too_dark_threshold, too_bright_threshold = get_light_thresholds(hour)

    # Nudge logic
    brightness_adjustment = 0
    if light_level < too_dark_threshold:
        brightness_adjustment = BRIGHTNESS_STEP
    elif light_level > too_bright_threshold:
        brightness_adjustment = -BRIGHTNESS_STEP

    adjusted_brightness = target_brightness + brightness_adjustment
    adjusted_brightness = max(MIN_BRIGHTNESS, min(MAX_BRIGHTNESS, adjusted_brightness))

    if brightness != adjusted_brightness or led_strip.color != target_color:
        print(f"[Hybrid Brightness] Hour: {hour}, Lux: {light_level:.2f}, Adjusted: {adjusted_brightness}, Color: {target_color}")
        brightness = adjusted_brightness
        led_strip.color = target_color
        update_leds()


def show_display():
    """ HT16K33 displays time normally and brightness level during button presses """
    if showing_brightness:
        hex_display.display_number(brightness)
        hex_display.set_colon(False)
    else:
        dt = rtc.datetime
        hour, minute = dt.tm_hour, dt.tm_min  # Assume it returns (hour, minute)
        time_val = hour * 100 + minute
        hex_display.display_number(time_val)
        hex_display.set_colon(True)

def on_increase_press():
    """ increase button press will:
            - increase LED intensity by 50 units
            - switch HT16K33 to display LED intensity"""
    global brightness, last_button_press_time, showing_brightness
    print("Increase button pressed")  # Debug line
    brightness = min(brightness + BRIGHTNESS_STEP, MAX_BRIGHTNESS)
    update_leds()
    last_button_press_time = time.time()
    showing_brightness = True

def on_decrease_press():
    """ decrease button press will:
            - decrease LED intensity by 50 units
            - switch HT16K33 to display LED intensity"""
    global brightness, last_button_press_time, showing_brightness
    print("Decrease button pressed")  # Debug line
    brightness = max(brightness - BRIGHTNESS_STEP, MIN_BRIGHTNESS)
    update_leds()
    last_button_press_time = time.time()
    showing_brightness = True
    
increase_btn.set_on_press_callback(on_increase_press)
decrease_btn.set_on_press_callback(on_decrease_press)


# ------------------------------------------------------------------------
# Main script
# ------------------------------------------------------------------------
try:
    while True:
        # Check auto brightness based on light levels
        check_auto_brightness()

        # Monitor button presses for manual adjustment or reset
        if increase_btn.is_pressed():
            # Increase button pressed
            on_increase_press()

        elif decrease_btn.is_pressed():
            # Decrease button pressed
            on_decrease_press()

        # Monitor for long button press to reset to automatic mode
        if increase_btn.is_pressed() or decrease_btn.is_pressed():
            # Track the time when the button was pressed
            press_time = time.time()
            
            while time.time() - press_time < 3:
                # Wait for 3 seconds of button hold
                if not (increase_btn.is_pressed() or decrease_btn.is_pressed()):
                    break  # Button released early, exit loop

            # Reset to auto if held for 3 seconds
            if time.time() - press_time >= 3:
                print("Button held for 3 seconds - Resetting to automatic mode")
                brightness = 100  # Reset to default brightness
                led_strip.set_brightness(brightness)
                showing_brightness = False  # Show time on display
                last_button_press_time = time.time()

        # Manage brightness display timeout (to show time after a timeout)
        if time.time() - last_button_press_time > DISPLAY_TIMEOUT:
            showing_brightness = False
        
        # Show the current display
        show_display()

        time.sleep(1)  # Sleep for a second before checking again

except KeyboardInterrupt:
    print("Cleaning up...")
    increase_btn.cleanup()
    decrease_btn.cleanup()
    led_strip.off()
    hex_display.clear()
