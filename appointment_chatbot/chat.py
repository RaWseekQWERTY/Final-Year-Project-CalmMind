import json
import torch
import random
import spacy
from datetime import datetime
from .model import NeuralNetWithAttention 
from .nltk_utils import bag_of_words, tokenize
from .models import ChatLog  
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from appointment.models import Appointment 
from auth_app.models import Patient, Doctor
import dateparser

User = get_user_model()

# Load spaCy for NER
nlp = spacy.load("en_core_web_sm")

# Load intents from JSON file
with open('appointment_chatbot/intents.json', 'r') as f:
    intents = json.load(f)

# Load the trained model
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
FILE = "appointment_chatbot/data.pth"
data = torch.load(FILE)

input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data["all_words"]
tags = data["tags"]
model_state = data["model_state"]

# Initialize the model with attention
model = NeuralNetWithAttention(input_size, hidden_size, output_size).to(device)
model.load_state_dict(model_state)
model.eval()

async def log_interaction(user_id, message, response, intent):
    """
    Save the interaction to the ChatLog table.
    :param user_id: int, ID of the user making the request
    :param message: list, tokenized user input
    :param response: str, chatbot's response
    :param intent: str, identified intent
    """
    try:
        patient = await sync_to_async(Patient.objects.get)(user_id=user_id)
    except Patient.DoesNotExist:
        raise ValueError("No patient found for the given user_id")
    
    # Create the chat log asynchronously
    await sync_to_async(ChatLog.objects.create)(
        patient=patient,  
        message=" ".join(message),  # Convert tokenized input back to string
        response=response,
        intent=intent
    )  
    
async def get_response(sentence, user_id, context=None):
    if not context:
        context = {}

    # If the context specifies a step, use it to determine the intent
    if "step" in context:
        tag = context["step"]
    else:
        # Otherwise, classify the intent normally
        sentence = tokenize(sentence)
        X = bag_of_words(sentence, all_words)
        X = X.reshape(1, X.shape[0])
        X = torch.from_numpy(X).to(device)

        output = model(X)
        _, predicted = torch.max(output, dim=1)
        tag = tags[predicted.item()]
        probs = torch.softmax(output, dim=1)
        prob = probs[0][predicted.item()]

        print(f"Predicted Intent: {tag}, Confidence: {prob.item()}")  # Debug log

        if prob.item() < 0.75:
            return "I'm sorry, I didn't understand that."

    # Handle the intent based on the tag
    for intent in intents['intents']:
        if intent['tag'] == tag:
            if tag == "appointment_booking":
                return handle_appointment_booking(sentence, context, user_id)  
            elif tag in ["get_name", "get_date", "get_time"]:
                return handle_follow_up(tag, sentence, context, user_id)
            else:
                return random.choice(intent['responses'])
                                                    
def handle_appointment_booking(sentence, context, user_id):
    if not context:
        context = {"step": "get_name"}
    return handle_follow_up(context.get("step", "get_name"), sentence, context, user_id)


def handle_follow_up(step, sentence, context, user_id):
    doc = nlp(" ".join(sentence))
    
    extracted_entities = {
        "name": context.get("name"),
        "date": context.get("date"),
        "time": context.get("time")
    }

    print(f"Processing sentence: {' '.join(sentence)}")  # Debug log

    for ent in doc.ents:
        print(f"Entity: {ent.text}, Label: {ent.label_}")  # Debug log
        if ent.label_ == "PERSON":
            extracted_entities["name"] = ent.text
        elif ent.label_ == "DATE":
            extracted_entities["date"] = ent.text
        elif ent.label_ == "TIME":
            extracted_entities["time"] = ent.text

    # Update context
    context.update(extracted_entities)

    if step == "get_name":
        if extracted_entities["name"]:
            context["step"] = "get_date"
            print(f"Updated context after get_name: {context}")  # Debug log
            return f"Thank you, {extracted_entities['name']}. When would you like the appointment?"
        else:
            return "Could you please provide your name?"

    elif step == "get_date":
        if extracted_entities["date"]:
            context["step"] = "get_time"
            print(f"Updated context after get_date: {context}")  # Debug log
            return f"Got it. What time would you like the appointment on {extracted_entities['date']}?"
        else:
            return "Could you please provide the date for the appointment?"

    elif step == "get_time":
        if extracted_entities["time"]:
            print(f"Updated context after get_time: {context}")  # Debug log
            return save_appointment(context, user_id)  # Pass user_id here
        else:
            return "Could you please provide the time for the appointment?"
                                                
def list_available_doctors():
    from auth_app.models import Doctor
    doctors = Doctor.objects.all()
    if doctors.exists():
        response = "Here are the available doctors:\n"
        for doctor in doctors:
            response += f"- Dr. {doctor.user.get_full_name()} ({doctor.specialization})\n"
        return response
    else:
        return "No doctors are currently available."
    
def save_appointment(context, user_id):
    print(f"Saving appointment with context: {context} and user_id: {user_id}")  # Debug log

    try:
        # Extract and parse date/time
        appointment_date = dateparser.parse(context["date"]).date()
        appointment_time = dateparser.parse(context["time"]).time()

        # Fetch the logged-in user's Patient profile
        user = User.objects.get(id=user_id)
        patient = user.patient_profile 

        # Assign a default doctor (you can modify this logic)
        doctor = Doctor.objects.first()

        # Create the appointment
        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=datetime.strptime(appointment_date, "%Y-%m-%d").date(),
            appointment_time=datetime.strptime(appointment_time, "%H:%M").time(),
            status="Pending"
        )

        return f"Your appointment has been booked for {appointment_date} at {appointment_time}. Thank you!"
    except KeyError as e:
        print(f"Missing key in context: {e}")
        raise ValueError(f"Missing required information in context: {e}")
    except Patient.DoesNotExist:
        print(f"No Patient profile found for user_id: {user_id}")
        raise ValueError("No Patient profile found for the logged-in user.")