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
from appointment.models import Appointment, DoctorAvailability
from auth_app.models import Patient, Doctor
from dashboard.models import Notification
import dateparser
import re

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
    if context is None:
        context = {}
    
    # Create a copy to avoid modifying the original
    context_copy = context.copy()
    
    # Check if we need to save an appointment
    if "ready_to_save" in context_copy and context_copy["ready_to_save"]:
        print("Ready to save flag detected, saving appointment...")
        del context_copy["ready_to_save"]  # Remove the flag
        response = await save_appointment(context_copy, user_id)
        context_copy["completed"] = True
        return response, context_copy
    
    # Tokenize the sentence
    tokenized_sentence = tokenize(sentence)

    # If the context specifies a step, use it to determine the intent
    if "step" in context_copy:
        tag = context_copy["step"]
        
        # Handle the intent based on the step
        if tag == "get_name" or tag == "get_date" or tag == "get_time":
            response = handle_follow_up(tag, tokenized_sentence, context_copy, user_id)
            
            # Check if the appointment is ready to be saved after handling the follow-up
            if "ready_to_save" in context_copy and context_copy["ready_to_save"]:
                print("Ready to save flag detected after follow-up, saving appointment...")
                del context_copy["ready_to_save"]
                response = await save_appointment(context_copy, user_id)
                context_copy["completed"] = True
            
            return response, context_copy
    else:
        # Otherwise, classify the intent normally
        X = bag_of_words(tokenized_sentence, all_words)
        X = X.reshape(1, X.shape[0])
        X = torch.from_numpy(X).to(device)

        output = model(X)
        _, predicted = torch.max(output, dim=1)
        tag = tags[predicted.item()]
        probs = torch.softmax(output, dim=1)
        prob = probs[0][predicted.item()]

        print(f"Predicted Intent: {tag}, Confidence: {prob.item()}")  # Debug log

        if prob.item() < 0.75:
            return "I'm sorry, I didn't understand that.", context_copy

    # Handle the intent based on the tag
    for intent in intents['intents']:
        if intent['tag'] == tag:
            if tag == "appointment_booking":
                context_copy["step"] = "get_name"
                response = "I'd be happy to help you book an appointment. Could you please tell me your name?"
                return response, context_copy
            elif tag in ["greeting", "goodbye", "thanks"]:
                return random.choice(intent['responses']), context_copy
            else:
                # For other non-booking intents
                return random.choice(intent['responses']), context_copy
                
    # If no matching intent is found
    return "I'm not sure how to help with that. Would you like to book an appointment?", context_copy
                                                                
def handle_appointment_booking(sentence, context, user_id):
    if not context:
        context = {"step": "get_name"}
    return handle_follow_up(context.get("step", "get_name"), sentence, context, user_id)


def handle_appointment_booking(sentence, context, user_id):
    if not context:
        context = {"step": "get_name"}
    return handle_follow_up(context.get("step", "get_name"), sentence, context, user_id)

def handle_follow_up(step, sentence, context, user_id):
    sentence_text = " ".join(sentence)
    doc = nlp(sentence_text)
    extracted_entities = {
        "name": None,
        "date": None,
        "time": None
    }

    print(f"Processing sentence: {sentence_text}")  # Debug log

    # Regular expressions for date formats
    date_patterns = [
        r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
        r'\d{2}-\d{2}-\d{4}',  # DD-MM-YYYY
        r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
        r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
    ]

    # Regular expression for time
    time_pattern = r'\d{1,2}\s*(?:am|pm|AM|PM|a\.m\.|p\.m\.)|(?:\d{1,2}:\d{2})'

    # Extract entities from spaCy NER
    for ent in doc.ents:
        print(f"Entity: {ent.text}, Label: {ent.label_}")  # Debug log
        if ent.label_ == "PERSON":
            extracted_entities["name"] = ent.text
        elif ent.label_ == "DATE":
            extracted_entities["date"] = ent.text
        elif ent.label_ == "TIME":
            extracted_entities["time"] = ent.text

    # Use regex to check for date if not found by spaCy
    if not extracted_entities["date"]:
        for pattern in date_patterns:
            date_match = re.search(pattern, sentence_text.replace(" ", ""))
            if date_match:
                extracted_entities["date"] = date_match.group(0)
                print(f"Date found with regex: {extracted_entities['date']}")
                break

    # Use regex to check for time if not found by spaCy
    if not extracted_entities["time"]:
        time_match = re.search(time_pattern, sentence_text)
        if time_match:
            extracted_entities["time"] = time_match.group(0)
            print(f"Time found with regex: {extracted_entities['time']}")

    if step == "get_name":
        if extracted_entities["name"]:
            context["name"] = extracted_entities["name"]
            context["step"] = "get_date"
            print(f"Updated context after get_name: {context}")  # Debug log
            return f"Thank you, {extracted_entities['name']}. When would you like the appointment?"
        else:
            return "Could you please provide your name?"

    elif step == "get_date":
        if extracted_entities["date"]:
            # Validate the date is in the future
            parsed_date = dateparser.parse(extracted_entities["date"])
            if parsed_date and parsed_date.date() >= datetime.now().date():
                context["date"] = extracted_entities["date"]
                context["step"] = "get_time"
                print(f"Updated context after get_date: {context}")  # Debug log
                return f"Got it. What time would you like the appointment on {extracted_entities['date']}?"
            else:
                return "Please provide a valid future date for your appointment."
        else:
            return "I couldn't understand the date. Please provide a date in YYYY-MM-DD format (e.g., 2025-04-20)."

    elif step == "get_time":
        if extracted_entities["time"]:
            context["time"] = extracted_entities["time"]
            print(f"Updated context after get_time: {context}")  # Debug log
            # Don't call save_appointment directly here since it's async
            context["ready_to_save"] = True
            return "Thank you for providing all the information. I'll book your appointment now."
        else:
            return "Could you please provide the time for the appointment? (e.g., 3 PM or 15:00)"
        
                                                                            
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
    
async def save_appointment(context, user_id):
    print(f"Saving appointment with context: {context} and user_id: {user_id}")  # Debug log

    try:
        # Check if all required fields are present
        if not all(key in context for key in ["name", "date", "time"]):
            missing_fields = [key for key in ["name", "date", "time"] if key not in context]
            return f"Missing required information: {', '.join(missing_fields)}. Please provide this information."
            
        # Extract and parse date/time
        parsed_date = dateparser.parse(context["date"])
        parsed_time = dateparser.parse(context["time"])
        
        if not parsed_date or not parsed_time:
            return "I couldn't understand the date or time format. Please try again."
        
        appointment_date = parsed_date.date()
        appointment_time = parsed_time.time()
        
        # Get current date and time
        current_datetime = datetime.now()
        
        # Combine appointment date and time for comparison
        appointment_datetime = datetime.combine(appointment_date, appointment_time)
        
        # Check if the appointment is in the past
        if appointment_datetime < current_datetime:
            return "Sorry, you cannot book appointments for past dates and times. Please select a future date and time."

        try:
            # Fetch the logged-in user's Patient profile using sync_to_async
            user = await sync_to_async(User.objects.get)(id=user_id)
            
            # Get the patient profile, with better error handling
            try:
                patient = await sync_to_async(lambda: user.patient_profile)()
            except AttributeError:
                return "Error: No patient profile found for your account."

            # Fetch the first doctor
            doctor = await sync_to_async(Doctor.objects.first)()
            if not doctor:
                return "Error: No doctors available in the system."
                
            # Check if the appointment is on a weekend
            if appointment_date.weekday() in [5, 6]:  # 5 = Saturday, 6 = Sunday
                return "Sorry, appointments are not available on weekends. Please select a weekday."
                
            # Check if the doctor has availability for the selected date and time
            
            # Get the doctor's availability for the selected day
            availability = await sync_to_async(lambda: DoctorAvailability.objects.filter(
                doctor=doctor,
                day_of_week=appointment_date.weekday()
            ).first())()
            
            if not availability:
                return f"Sorry, the doctor is not available on {appointment_date.strftime('%A')}s. Please select another day."
                
            # Check if the appointment time is within visiting hours
            if not (availability.visiting_hours_start <= appointment_time <= availability.visiting_hours_end):
                return f"Sorry, the doctor is only available between {availability.visiting_hours_start.strftime('%H:%M')} and {availability.visiting_hours_end.strftime('%H:%M')} on {appointment_date.strftime('%A')}s. Please select a time within these hours."
                
            # Check if the doctor is already booked for the selected date and time
            existing_appointment = await sync_to_async(lambda: Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time
            ).exists())()
            
            if existing_appointment:
                return "Sorry, the selected time slot is already booked. Please select another time."

            # All validations passed, create the appointment
            appointment = await sync_to_async(Appointment.objects.create)(
                patient=patient,
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status="Pending"
            )

            # Create notification for the doctor
            
            notification_message = f"New appointment request from {user.get_full_name()} for {appointment_date.strftime('%Y-%m-%d')} at {appointment_time.strftime('%H:%M')}."
            
            await sync_to_async(Notification.objects.create)(
                user=doctor.user,
                message=notification_message
            )
            
            print(f"Notification created for doctor: {doctor.user.username}")

            # Return success message
            return f"Your appointment has been successfully booked with Dr. {doctor.user.last_name} for {appointment_date.strftime('%A, %B %d, %Y')} at {appointment_time.strftime('%I:%M %p')}. The doctor has been notified."
        
        except Exception as e:
            print(f"Database error: {str(e)}")
            return f"Database error: {str(e)}"
            
    except Exception as e:
        print(f"Error saving appointment: {e}")
        return f"Sorry, there was an error booking your appointment: {str(e)}"