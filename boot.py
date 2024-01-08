# import network
import asyncio
import json
import network
from time import sleep
from server import Server
import _thread
import os
from microWebSocket import MicroWebSocket
from machine import Pin, PWM
import onewire, ds18x20


class Boot(object):
    def __init__(self):
        self.RELAY_PIN = Pin(14, Pin.OUT)
        self.LED_PIN = Pin(2, Pin.OUT)
        self.RELAY_PIN.on()

        self.TEMP_SENSOR_PIN = Pin(13, Pin.IN)
        self.DS = ds18x20.DS18X20(onewire.OneWire(self.TEMP_SENSOR_PIN))
        self.ROMS = self.DS.scan()

        self.R_PWM = PWM(Pin(12))
        self.G_PWM = PWM(Pin(5))
        self.B_PWM = PWM(Pin(27))
        self.R_PWM.freq(500)
        self.G_PWM.freq(500)
        self.B_PWM.freq(500)
        self.R_PWM.duty(0)
        self.G_PWM.duty(0)
        self.B_PWM.duty(0)
        self._setColor((816, 408, 1023))

        self.targetTemp = 60
        self.currentTemperature = 0
        _thread.start_new_thread(self._tempCheckLoop, ())

        self.station = network.WLAN(network.STA_IF)
        self.station.active(True)
        config = self._getWifiConfig(".wifiConfig.json")
        if config is None:
            return
        ssid, password = config
        self._connectToWiFi(ssid, password)

        self.server = Server(
            {
                "kettleOn": self._onKettleOn,
                "kettleOff": self._onKettleOff,
                "getCurrentTemperature": self._onGetCurrentTemperature,
            }
        )
        _thread.start_new_thread(self.server.listen, ())

    def _onKettleOn(self, message, websocket: MicroWebSocket):
        self.RELAY_PIN.off()
        self.LED_PIN.on()
        self.server.respond(websocket, "Kettle turned on")

    def _onKettleOff(self, message, websocket: MicroWebSocket):
        self.RELAY_PIN.on()
        self.LED_PIN.off()
        self.server.respond(websocket, "Kettle turned off")

    def _targetTempReached(self):
        self.RELAY_PIN.on()
        self.LED_PIN.off()

    def _tempCheckLoop(self):
        while True:
            self.currentTemperature = self._readTemp()
            print(self.currentTemperature)
            if self.currentTemperature >= self.targetTemp:
                self._targetTempReached()

    def _readTemp(self):
        self.DS.convert_temp()
        # trzeba poczekać 750 ms wg specyfikacji
        sleep(750)
        try:
            temp: float = self.ROMS[0].read_temp()
            return temp
        except Exception:
            return None

    def _onGetCurrentTemperature(self, message, websocket: MicroWebSocket):
        self.server.respond(
            websocket,
            "ok",
            200,
            {
                "temperature": self.currentTemperature(),
            },
        )

    def _setColor(self, color: tuple[int]):
        self.R_PWM.duty(color[0])
        self.G_PWM.duty(color[1])
        self.B_PWM.duty(color[2])

    def _getWifiConfig(self, path) -> tuple[str, str]:
        print("Extracting wifi config from specified file...")
        # testing if file exists
        try:
            with open(path, "r") as f:
                pass
        except OSError:
            print("Specified wifi config file doesn't exist!")
            return None

        # opening file
        with open(path, "r") as f:
            try:
                # loading data to json format
                data = json.loads(f.read())

                # extracting required values from file
                ssid = str(data["ssid"])
                password = str(data["password"])

                return ssid, password
            except json.JSONDecodeError:
                print(
                    "Data in specified wifi config file couldn't be decoded to json!"
                )
            except KeyError as e:
                print(
                    f"Couldn't find key '{e.args[0]}' in specified wifi config file!"
                )
        return None

    def _connectToWiFi(self, ssid, password):
        if not self.station.isconnected():
            print("Attempting to connect to specified network...")
            self.station.connect(ssid, password)
            while not self.station.isconnected():
                sleep(0.5)
        print(f"Network connected! Network config: {self.station.ifconfig()}")


if __name__ == "__main__":
    _thread.start_new_thread(Boot, ())
