import json
import asyncio
import _thread
from microWebSrv import MicroWebSrv
from microWebSocket import MicroWebSocket


class Server(object):
    def __init__(self):
        self.clients = []

    def listen(self):
        asyncio.run(self._mainLoop())

    async def _mainLoop(self):
        mws = MicroWebSrv(port=2137)
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
        except json.JSONDecodeError:
            print(
                f"Message from '{websocket.host}' couldn't have been parsed to json"
            )
            self._respond(
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

        commandHandles = {
            "ping": self._handlePingCommand,
            "setName": self._handleSetName,
        }

        try:
            command = message["command"]
            if command not in commandHandles:
                raise ValueError

            # executing correct handle for specified command
            commandHandles[command](message, websocket)
        except KeyError:
            self._respond(websocket, "There is no command specified!", 400)
        except ValueError:
            self._respond(
                websocket, f"There is no command named '{command}'!", 400
            )

    def _handlePingCommand(self, _, websocket: MicroWebSocket) -> None:
        self._respond(websocket, "Ping received! We have a connection!")

    def _handleSetName(self, message: dict, websocket: MicroWebSocket) -> None:
        try:
            name = message["name"]
            websocket.name = str(name)
            print(
                f"Connection from '{websocket.host}' named themselves '{name}'"
            )
            self._respond(websocket, "Your name was set")
        except KeyError:
            self._respond(websocket, "There is no name specified!", 400)

    def _respond(
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
