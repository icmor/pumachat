#!/usr/bin/env python
from utils import BaseChat, MessageException
from message import Message
import asyncio
import socket
import logging


class Client(BaseChat):

    def __init__(self, host=socket.gethostname(), port=8080):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    async def connect(self):
        self.reader, self.writer = await \
            asyncio.open_connection(self.host, self.port)

    async def run(self):
        try:
            while True:
                await self.connect()
                if (not await self.login()
                        and input("Reintentar login? [y/n] ").lower()
                        in ["yes", "y"]):
                    continue
                break
        except (OSError, ConnectionRefusedError) as e:
            logging.critical("Error de conexión.")
            logging.exception(e)
        except MessageException as e:
            logging.critical("Respuesta del servidor no reconocida.")
            logging.exception(e)
        except asyncio.CancelledError as e:
            logging.critical("Error inesperado durante la ejecución.")
            logging.exception(e)
        finally:
            await self.cleanup()

    async def login(self):
        username = input("Enter your username: ")
        await self.send(Message({"type": "IDENTIFY",
                                 "username": username}))
        response = await self.recv()
        logging.debug(response.__repr__())
        raise MessageException("Unrecognized response from server")
        match response:
            case {"type": "INFO", "message": "success"}:
                print(f"Login exitoso! Bienvenido {username}")
                return True
            case {"type": "WARNING"}:
                print(response["message"])
                return False
            case _:
                raise MessageException("Expected message type 'WARNING'. Got",
                                       response.__repr__())

    async def cleanup(self):
        pass


async def main():
    client = Client()
    await client.run()

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING,
                        format='%(levelname)s [%(name)s] %(message)s')
    asyncio.run(main())
