import torch
from peft import PeftModel
from transformers import AutoTokenizer, AutoModelForCausalLM
from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)

class LlamaModelWrapper:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LlamaModelWrapper, cls).__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        try:
            logger.info("Loading TinyLlama model with LoRA adapters...")
            self.model_path = settings.LLAMA_MODEL_PATH
            self.lora_path = "tinyllama-finetuned"

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.lora_path, 
                local_files_only=True
            )

            # Load base model with full CPU loading
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                local_files_only=True,
                torch_dtype=torch.float32,
                device_map="cpu",       # Force CPU
                offload_folder=None,    # Disable offloading
                offload_state_dict=False
            )

            # Apply LoRA adapters
            self.model = PeftModel.from_pretrained(
                self.model,
                self.lora_path,
                local_files_only=True
            )

            # Merge adapters (critical for inference)
            self.model = self.model.merge_and_unload()
            # print(self.model)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
        
    def is_mental_health_related(self, query):
        """Check if the query is related to mental health."""
        mental_health_keywords = [
            'anxiety', 'depression', 'stress', 'mental health', 'therapy', 
            'counseling', 'panic', 'mood', 'emotion', 'feeling', 'sad', 
            'worried', 'nervous', 'fear', 'phobia', 'ocd', 'trauma',
            'ptsd', 'bipolar', 'schizophrenia', 'addiction', 'substance',
            'coping', 'self-care', 'meditation', 'mindfulness', 'wellness','die','self-harm','cut'
            'suicide', 'self-harm', 'self-destructive', 'self-inflicted','crying','breakdown','lonely'
            ,'insomnia','mental','mental illness','burnout','overwhelmed','fear','phobia','ocd','trauma','ptsd','bipolar',
            'intrusive thoughts','schizophrenia','addiction','substance','counseling','panic','self-harm','self-steem',
            'meditation','mindfulness','wellness','psychiatrist','coping','hopeless','future','insomnia','mental disorder','help','suggestions'
            ,'lazy','work','job','deprieved','anxious','sucide','confidence','self-esteem','adhd'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in mental_health_keywords)
    
    def is_greeting(self, query):
        """Check if the query is a simple greeting"""
        greetings = {'hello', 'hi', 'hey', 'good morning', 'good afternoon', 
                     'good evening', 'howdy', 'greetings'}
        return any(greeting in query.lower().split() for greeting in greetings)
    
    def is_goodbye(self, query):
        """Check if the query is a simple greeting"""
        greetings = {'bye', 'goodbye', 'sayonara', 'gracias', 'thanks', 
                     'thank you'}
        return any(greeting in query.lower().split() for greeting in greetings)
    
    def generate_response(self, query, max_length=128):
        try:
            if self.model is None or self.tokenizer is None:
                return "Model not loaded."
            
            if self.is_greeting(query):
                return "Hello! I'm here to help with mental health and well-being questions. How can I assist you today?^-^"

            if self.is_goodbye(query):
                return "Always, Ask anything else if you want to ^^"
            
            if not self.is_mental_health_related(query):
                return "I'm a mental health assistant and can only answer questions related to mental health, well-being, and emotional support."
            
            formatted_prompt = (
                f"### Instruction:\n{query}\n\n### Response:\n"
            )

            # Tokenize
            inputs = self.tokenizer(
                formatted_prompt, 
                return_tensors="pt",
                truncation=True,
                max_length=128  # Match training max_length
            ).to(self.model.device)

            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.eos_token_id  # Prevent padding issues
                )

            # Get the generated tokens after the input
            generated_tokens = outputs[0][inputs.input_ids.shape[1]:]
            response = self.tokenizer.decode(
                generated_tokens,
                skip_special_tokens=True
            ).strip()
            
            # Fallback: Avoid echoing
            if response.lower().strip() == query.lower().strip():
                return "I'm really sorry you're feeling this way. You're not alone, and there are people who care. Would you like to talk about it more?"


            return response

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I'm here to help, but something went wrong generating a response. Please try again."
