from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.sessions.backends.db import SessionStore
from asgiref.sync import sync_to_async
import json
from .chat import get_response

class AppointmentChatbotConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get the session key from the scope
        self.session_key = self.scope["session"].session_key
        if not self.session_key:
            # Create a new session if one doesn't exist
            await sync_to_async(self.scope["session"].create)()
            self.session_key = self.scope["session"].session_key

        # Load the context from the session
        self.context = self.scope["session"].get("chat_context", {})

        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        user_message = data['message']
        user_id = self.scope["user"].id  # Get the logged-in user's ID

        # Debug log to verify context before processing
        print(f"Current context before processing: {self.context}")

        # Get chatbot response with context and user_id
        bot_response, updated_context = await get_response(user_message, user_id, self.context)
        
        # Update the instance variable with the returned context
        self.context = updated_context
        
        # Save the updated context back to the session
        self.scope["session"]["chat_context"] = self.context
        await sync_to_async(self.scope["session"].save)()

        # Debug log to verify context after processing
        print(f"Updated context after processing: {self.context}")

        # Send response back to client
        await self.send(text_data=json.dumps({
            'message': bot_response
        }))
        
        # Only clear the context when the appointment is completed
        if "completed" in self.context and self.context["completed"]:
            print("Appointment completed, clearing context")
            del self.scope["session"]["chat_context"]
            self.context = {}
            await sync_to_async(self.scope["session"].save)()