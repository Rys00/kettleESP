# import network
import asyncio
import json
import network
from time import sleep
from server import Server
import _thread
import os


class Boot(object):
    def __init__(self):
        self.station = network.WLAN(network.STA_IF)
        self.station.active(True)
        config = self._getWifiConfig(".wifiConfig.json")
        if config is None:
            return
        ssid, password = config
        self._connectToWiFi(ssid, password)

        self.server = Server()
        # _thread.start_new_thread(self.server.listen, ())

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
    Boot()
