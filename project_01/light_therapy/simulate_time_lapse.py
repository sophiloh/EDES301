# -----------------------------------------------------------
# Imports
# -----------------------------------------------------------
import time
import board
import busio
import adafruit_bh1750
import adafruit_ds3231
import ht16k33
import opc

# -----------------------------------------------------------
# Define LEDStrip Class (copy from your main program)
# -----------------------------------------------------------
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

# -----------------------------------------------------------
# Initialize Hardware
# -----------------------------------------------------------
# I2C bus
i2c = board.I2C()

# LED Strip
led_strip = LEDStrip()

# RTC Clock
rtc = adafruit_ds3231.DS3231(i2c)

# Hex Display
hex_display = ht16k33.HT16K33(1, 0x70)

# -----------------------------------------------------------
# Supporting Functions
# -----------------------------------------------------------
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

def show_display():
    """ Show time on hex display """
    dt = rtc.datetime
    hour, minute = dt.tm_hour, dt.tm_min
    time_val = hour * 100 + minute
    hex_display.display_number(time_val)
    hex_display.set_colon(True)


# Assume all imports, LEDStrip class, rtc, hex_display, and get_target_brightness_and_color() are already set up.

simulated_hours = [5, 6, 7, 9, 12, 16, 18, 19, 21, 23]  # Key times of day
transition_duration = 4  # seconds per transition
transition_steps = 40    # steps during transition
pause_between_hours = 2  # seconds pause between hours

def lerp(start, end, t):
    return start + (end - start) * t

def lerp_color(start_color, end_color, t):
    return (
        int(lerp(start_color[0], end_color[0], t)),
        int(lerp(start_color[1], end_color[1], t)),
        int(lerp(start_color[2], end_color[2], t)),
    )

def smooth_set_led(brightness_value, color_value):
    led_strip.color = color_value
    led_strip.set_brightness(brightness_value)

def update_fake_rtc(hour, minute):
    """Set fake RTC time to a specific hour and minute."""
    fake_time = time.struct_time((2025, 4, 24, hour, minute, 0, 3, 114, -1))
    rtc.datetime = fake_time

def simulate_smooth_time_travel_with_clock():
    print("\nStarting Smooth Time-Lapse Test...\n")
    try:
        for i in range(len(simulated_hours) - 1):
            start_hour = simulated_hours[i]
            end_hour = simulated_hours[i + 1]

            # Set initial and target LED settings
            start_brightness, start_color = get_target_brightness_and_color(start_hour)
            end_brightness, end_color = get_target_brightness_and_color(end_hour)

            print(f"Transitioning from {start_hour:02d}:00 to {end_hour:02d}:00")

            # Smoothly transition
            for step in range(transition_steps + 1):
                t = step / transition_steps

                # Interpolate brightness and color
                current_brightness = int(lerp(start_brightness, end_brightness, t))
                current_color = lerp_color(start_color, end_color, t)

                # Calculate "fake" clock time
                total_minutes = (start_hour * 60) + (end_hour - start_hour) * 60 * t
                fake_hour = int(total_minutes // 60) % 24
                fake_minute = int(total_minutes % 60)

                # Update RTC and hex display
                update_fake_rtc(fake_hour, fake_minute)
                show_display()

                # Update LEDs
                smooth_set_led(current_brightness, current_color)

                time.sleep(transition_duration / transition_steps)

            # Pause briefly at the end of transition
            time.sleep(pause_between_hours)

        print("\nSmooth Time-Lapse Simulation Complete.")

    except KeyboardInterrupt:
        print("Simulation interrupted. Cleaning up...")
        led_strip.off()
        hex_display.clear()

if __name__ == "__main__":
    try:
        simulate_smooth_time_travel_with_clock()
    except KeyboardInterrupt:
        print("Simulation interrupted. Cleaning up...")
        led_strip.off()
        hex_display.clear()
