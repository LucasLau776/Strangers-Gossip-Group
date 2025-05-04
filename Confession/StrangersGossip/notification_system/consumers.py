import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_key = self.scope['session'].session_key
        await self.channel_layer.group_add(
            f"notifications_{self.session_key}",
            self.channel_name
        )
        await self.accept()

    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event['data']))