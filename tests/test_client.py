from client import Client
from server import Server
import message
import asyncio
import unittest


class ClientTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.server = Server(host="localhost")
        self.client = Client(host="localhost")
        self.server_task = asyncio.create_task(self.server.run())
        await self.client.connect()

    async def test_identify(self):
        await self.client.send(
            message.Message({"type": "IDENTIFY", "username": "JaneDoe"})
        )
        msg = await self.client.recv()
        self.assertEqual(msg["message"], "success")

    async def asyncTearDown(self):
        self.server_task.cancel()
