from channels.generic.websocket import AsyncWebsocketConsumer
import json

class DeviceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.identifier = self.scope['url_route']['kwargs']['identifier']
        self.group_name = f"device_{self.identifier}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps({"message": f"Conectado a {self.identifier}"}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # no hacemos nada al recibir desde cliente en este ejemplo
        pass

    async def location_message(self, event):
        # event esperado con 'text' (JSON)
        await self.send(text_data=event.get("text"))
