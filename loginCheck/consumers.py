from channels.generic.websocket import AsyncWebsocketConsumer
import json
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model

CustomUser = get_user_model()


class UserStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_authenticated:
            await self.update_user_login_status(user, True)
            await self.accept()

    async def disconnect(self, close_code):
        user = self.scope["user"]
        if user.is_authenticated:
            await self.update_user_login_status(user, False)

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            data = json.loads(text_data)
            user_ids = data.get('userid', [])
            login_statuses = await self.get_users_login_status(user_ids)
            await self.send(text_data=json.dumps(login_statuses))

    @sync_to_async
    def update_user_login_status(self, user, status):
        CustomUser.objects.filter(id=user.id).update(login=status)

    @sync_to_async
    def get_users_login_status(self, user_ids):
        statuses = {}
        for user_id in user_ids:
            user = CustomUser.objects.get(id=user_id)
            if user:
                statuses[user_id] = user.login
            else:
                statuses[user_id] = False
        return statuses
