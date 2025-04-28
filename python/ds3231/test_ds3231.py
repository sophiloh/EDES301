import time
import board
import busio
import adafruit_ds3231

# Setup I2C
i2c = busio.I2C(board.SCL, board.SDA)
rtc = adafruit_ds3231.DS3231(i2c)

# Get time
t = rtc.datetime
print("Current RTC time: {}-{:02}-{:02} {:02}:{:02}:{:02}".format(
    t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec))

# OPTIONAL: set RTC to current system time (uncomment if needed)
# import datetime
# rtc.datetime = datetime.datetime.now().timetuple()
