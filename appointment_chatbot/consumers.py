import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from appointment_chatbot.chat import get_response 

class AppointmentChatbotConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.context = {}  # Initialize context
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        user_message = data['message']
        user_id = self.scope["user"].id  # Get the logged-in user's ID
      
  
        # Get chatbot response with context and user_id
        bot_response = await get_response(user_message, user_id, self.context)

        # Send response back to client
        await self.send(text_data=json.dumps({
            'message': bot_response
        }))