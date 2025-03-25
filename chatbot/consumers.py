import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from .llm_model import LlamaModelWrapper
import logging
import concurrent.futures

logger = logging.getLogger(__name__)

# Create a thread pool executor for running CPU-bound tasks
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

class ChatbotConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handle WebSocket connection."""
        await self.accept()
        logger.info(f"WebSocket connected: {self.channel_name}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        logger.info(f"WebSocket disconnected: {self.channel_name}, code: {close_code}")
    
    async def receive(self, text_data):
        """Handle incoming messages from WebSocket."""
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message', '')
            
            # Send a typing indicator
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'is_typing': True
            }))
            
            # Process the model response in a separate thread
            response = await self.get_model_response(message)
            
            # Send the model's response
            await self.send(text_data=json.dumps({
                'type': 'chatbot_response',
                'message': response
            }))
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid request format'
            }))
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'An error occurred while processing your request'
            }))
    
    async def get_model_response(self, message):
        """Get response from the LLM model in a non-blocking way."""
        try:
            # Run the model inference in a thread pool to avoid blocking the event loop
            llm = LlamaModelWrapper()
            
            # Check if model is loaded
            if not hasattr(llm, 'model') or llm.model is None:
                return "Sorry, the mental health assistant is currently unavailable. Please try again later."
                
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                thread_pool, 
                llm.generate_response, 
                message
            )
            return response
        except Exception as e:
            logger.error(f"Error in get_model_response: {str(e)}")
            return "I'm experiencing technical difficulties. Please try again later."