from django.conf import settings
from django.shortcuts import render, redirect
from .models import PHQ9Assessment
from django.core.exceptions import PermissionDenied
from auth_app.models import Patient
import pickle
import pandas as pd

def assessment(request):
    if request.method == 'POST':
        # Check if the user is a patient
        if not hasattr(request.user, 'patient_profile'):
            raise PermissionDenied("Only patients can take the PHQ-9 assessment.")

        # Check if all fields are filled
        errors = {}
        form_data = {}
        for i in range(1, 11):
            question_key = f'q{i}'
            question_value = request.POST.get(question_key)
            if not question_value:
                errors[question_key] = f'Question {i} is required.'
            else:
                try:
                    form_data[question_key] = int(question_value)
                except ValueError:
                    errors[question_key] = f'Invalid value for Question {i}.'

        if errors:
            return render(request, 'assessment/depression_test.html', {'errors': errors})

        # Convert form data to DataFrame for prediction
        new_user_data = pd.DataFrame([form_data])

        # Load the model and predict
        with open(settings.PHQ9_MODEL_PATH, 'rb') as file:
            loaded_model = pickle.load(file)
        new_pred = loaded_model.predict(new_user_data)
        predicted_score, predicted_class = new_pred[0]

        # Save the assessment to the database
        assessment = PHQ9Assessment(
            patient=request.user.patient_profile,  # Use patient_profile instead of patient
            **form_data,
            predicted_score=predicted_score,
            predicted_depression_level=str(int(predicted_class)),
        )
        assessment.save()

        # Redirect to the result page with the assessment ID
        return redirect('result', assessment_id=assessment.assessment_id)

    return render(request, 'assessment/depression_test.html')

def result(request, assessment_id=None):
    # Check if the user is a patient
    if not hasattr(request.user, 'patient_profile'):
        raise PermissionDenied("Only patients can view assessment results.")

    # Fetch the patient profile
    patient = request.user.patient_profile

    # Fetch the latest assessment if no assessment_id is provided
    if not assessment_id:
        latest_assessment = PHQ9Assessment.objects.filter(patient=patient).last()
        if not latest_assessment:
            return redirect('assessment')
        assessment_id = latest_assessment.assessment_id

    # Fetch the assessment from the database
    try:
        assessment = PHQ9Assessment.objects.get(assessment_id=assessment_id)
    except PHQ9Assessment.DoesNotExist:
        return redirect('assessment')

    # Map depression levels to their labels
    depression_levels = {
        '0': 'None',
        '1': 'Mild',
        '2': 'Moderate',
        '3': 'Moderately Severe',
        '4': 'Severe',
    }

    # Prepare context for the template
    context = {
        'score': assessment.score,
        'predicted_score': assessment.predicted_score,
        'depression_level': depression_levels.get(assessment.depression_level, 'Unknown'),
        'predicted_depression_level': depression_levels.get(assessment.predicted_depression_level, 'Unknown'),
    }

    return render(request, 'assessment/test_result.html', context)