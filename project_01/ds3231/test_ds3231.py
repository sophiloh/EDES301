import adafruit_ds3231
import time

import board
i2c = board.I2C()  # uses board.SCL and board.SDA
rtc = adafruit_ds3231.DS3231(i2c)
rtc.datetime = time.struct_time((2025,4,22,22,22,0,1,112,1))
t = rtc.datetime
print(t)
print(t.tm_hour, t.tm_min)