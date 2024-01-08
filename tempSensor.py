import time
from machine import Pin
import onewire, ds18x20

# taken from example code, located here:
# https://docs.micropython.org/en/latest/esp8266/tutorial/onewire.html

# the device is on GPIO5
dat = machine.Pin(5)

# create the onewire object
ds = ds18x20.DS18X20(onewire.OneWire(dat))

# scan for devices on the bus
roms = ds.scan()
print("found devices:", roms)

# need to do this to initiate temperature reading
ds.convert_temp()
# must wait some amount of time for probe to return value (750 ms given in example code in docs)
time.sleep_ms(750)

# retrieves value and prints it
print(ds.read_temp(roms[0]))
