import json
import asyncio
import _thread
from microWebSrv import MicroWebSrv
from microWebSocket import MicroWebSocket
from machine import Pin


class Server(object):
    def __init__(self, customCommands=None):
        self.clients = []
        self.PORT = 2137
        if customCommands is None:
            customCommands = {}
        self.customCommands = customCommands
        self.commandHandles = {
            "ping": self._handlePingCommand,
            "setName": self._handleSetName,
            "verify": self._handleVerifyCommand,
            "ledOn": self._handleLedOn,
            "ledOff": self._handleLedOff,
        }
        self.commandHandles.update(self.customCommands)

    def listen(self):
        print(f"Starting server at 'localhost' port {self.PORT}")
        asyncio.run(self._mainLoop())

    async def _mainLoop(self):
        mws = MicroWebSrv(port=self.PORT)
        mws.MaxWebSocketRecvLen = 256
        mws.WebSocketThreaded = False
        mws.AcceptWebSocketCallback = (
            self._handleOpenConnection
        )  # Function to receive WebSockets
        mws.Start(threaded=True)
        while True:
            await asyncio.sleep(1)

    def _handleOpenConnection(self, websocket: MicroWebSocket, httpClient):
        self.clients.append(websocket)

        websocket.RecvTextCallback = self._handleMessage
        websocket.RecvBinaryCallback = self._handleMessageBinary
        websocket.ClosedCallback = self._handleCloseConnection

        websocket.host = httpClient.GetIPAddr()
        websocket.name = "Unnamed"

        print(f"New connection from '{websocket.host}' aka '{websocket.name}'")

    def _handleCloseConnection(self, websocket):
        print(
            f"Connection from '{websocket.host}' aka '{websocket.name}' closed!"
        )
        self.clients.remove(websocket)

    def _handleMessageBinary(self, websocket, message):
        pass

    def _parseMessageFromJSON(
        self,
        rawMessage: str,
        websocket: MicroWebSocket,
    ) -> dict:
        try:
            message = json.loads(rawMessage)
            return message
        except Exception:
            print(
                f"Message from '{websocket.host}' couldn't have been parsed to json"
            )
            self.respond(
                websocket, "Your message couldn't be parsed to json!", 400
            )
        return None

    def _handleMessage(
        self,
        websocket: MicroWebSocket,
        rawMessage: str,
    ) -> None:
        print(
            f"Received new message from '{websocket.host}' aka '{websocket.name}'"
        )

        message = self._parseMessageFromJSON(rawMessage, websocket)
        if message is None:
            return

        try:
            command = message["command"]
            if command not in self.commandHandles:
                raise ValueError

            # executing correct handle for specified command
            self.commandHandles[command](message, websocket)
        except KeyError:
            self.respond(websocket, "There is no command specified!", 400)
        except ValueError:
            self.respond(
                websocket, f"There is no command named '{command}'!", 400
            )

    def _handlePingCommand(self, _, websocket: MicroWebSocket) -> None:
        self.respond(websocket, "Ping received! We have a connection!")

    def _handleVerifyCommand(
        self, message: dict, websocket: MicroWebSocket
    ) -> None:
        try:
            question = message["question"]
            if question == "Which team is the best":
                print(
                    f"Connection from '{websocket.host}' aka '{websocket.name}' verified!"
                )
                self.respond(websocket, "Sprytne Dzbany")
                return
            self.respond(websocket, "Wrong question!", 400)
        except KeyError:
            self.respond(websocket, "There is no question specified!", 400)

    def _handleSetName(self, message: dict, websocket: MicroWebSocket) -> None:
        try:
            name = message["name"]
            websocket.name = str(name)
            print(
                f"Connection from '{websocket.host}' named themselves '{name}'"
            )
            self.respond(websocket, "Your name was set")
        except KeyError:
            self.respond(websocket, "There is no name specified!", 400)

    def _handleLedOn(self, _, websocket: MicroWebSocket) -> None:
        led = Pin(2, Pin.OUT)
        led.on()
        self.respond(websocket, "LED has been turned on")

    def _handleLedOff(self, _, websocket: MicroWebSocket) -> None:
        led = Pin(2, Pin.OUT)
        led.off()
        self.respond(websocket, "LED has been turned off")

    def respond(
        self,
        websocket: MicroWebSocket,
        message: str,
        code: int = 200,
        extraData: dict = None,
    ) -> None:
        """
        code 200 - ok
        code 400 - bad data
        """
        data = {}
        if extraData is not None:
            data = extraData
        data["message"] = message
        data["code"] = code
        response = json.dumps(data)
        _thread.start_new_thread(websocket.SendText, (response,))


if __name__ == "__main__":
    server = Server()
    server.listen()
