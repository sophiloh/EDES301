# Smart Light Therapy Device

This software is for an ENGI 301 project, where I built a device that tracks the time, ambient lighting, and user preference to adjust LED strip lights to particular colors and intensities, mimicking the natural sunlight throughout the day.

Link to hackster.io project, which details information on the hardware side of this project: https://www.hackster.io/ssl12/edes-301-smart-light-therapy-4f5a94

## Relevant libraries to install:
- Adafruit DS3231 library:
pip3 install adafruit-circuitpython-ds3231
- Adafruit BH1750 library:
pip3 install adafruit-circuitpython-bh1750

## Instructions on running software:
In the cloud9 terminal, open two terminals and navigate to EDES301/project_01 in both terminals.

Set the RTC time if needed by uncommenting line 142 and entering in the date and time in line 137. See comments in line 136 for notation.

In one terminal, type in sudo ./run-opc-server to run the OPC needed for the LED strip. In the other terminal, navigate to EDES301/project_01/light_therapy to send the sudo ./run command to run the main program.

Run the following commands to make the code run automatically on boot:

sudo crontab -e
@reboot sleep 30 && sh /var/lib/cloud9/ENGI301/project_01/run > /var/lib/cloud9/logs/cronlog 2>&1
Exit and Save

sudo reboot

