# CalmMind Final Year Project

CalmMind is a full-stack mental health management system built with Django. It features an AI-powered chatbot, PHQ-9 depression assessment, doctor-patient appointment scheduling, and dashboard management.

---

## 🌐 Features

- AI Chatbot (Fine-tuned TinyLlama with WebSocket-based interaction)
- PHQ-9 Depression Assessment with ML model
- Secure authentication & role-based access
- Doctor dashboard with analytics, appointments, and patient details
- Patient dashboard with appointments and results
- Appointment chatbot to help book slots
- PDF generation for reports

---

## 📁 Project Structure

Refer to the detailed directory structure above for module-level organization including:
- `auth_app`: Custom authentication with doctor/patient/admin roles
- `chatbot`: LLM-powered real-time chatbot interface
- `appointment_chatbot`: Intent-based appointment booking assistant
- `assessment`: PHQ-9 depression assessment with ML integration
- `ml_models/`: Contains trained `multi_output_phq9_model.pkl`
- `tinyllama-finetuned/`: Contains adapter weights for TinyLlama
- `dashboard/`: Contains dashboard for doctor and patient
- `appointment/`: Contains Appointment for booking through UI
- `patient_profile/`: Contains profile for patient and setting views for doctor

---

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.9+
- PostgreSQL
- NPM (for Tailwind)
- HuggingFace CLI

### Environment Setup

```bash
cp example-env.env .env
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Install Tailwind dependencies:
```bash
npm install
npx tailwindcss -i ./static/css/tailwind-input.css -o ./static/css/output.css --watch
```

### Database Configuration

1. **Set PostgreSQL credentials** in your `.env` file.
2. **Create the database:**

```bash
psql -U postgres
CREATE DATABASE calmmind;
```

3. **Run Django migrations:**
```bash
python manage.py makemigrations
python manage.py migrate auth_app
```

> ⚠️ After migrating `auth_app`, fix the `django_admin_log` foreign key constraint:

### SQL Constraint Fix (PostgreSQL)

Use the following SQL script after migration to ensure `django_admin_log` references your custom user model (`auth_app_user`):

```sql
-- Step 1: Dynamically drop existing FK using a CTE
DO $$
DECLARE
    fk_name TEXT;
BEGIN
    SELECT conname INTO fk_name
    FROM pg_constraint
    WHERE conrelid = 'django_admin_log'::regclass
      AND confrelid = 'auth_user'::regclass;

    EXECUTE format('ALTER TABLE django_admin_log DROP CONSTRAINT %I;', fk_name);
END $$;

-- Step 2: Add new FK referencing custom user model
ALTER TABLE django_admin_log
ADD CONSTRAINT fk_user_id FOREIGN KEY (user_id)
REFERENCES auth_app_user (id) ON DELETE CASCADE;
```

> 🗂️ Save the script as `fix_admin_log_fk.sql` and execute it in `psql`:
```bash
psql -U postgres -d calmmind -f fix_admin_log_fk.sql
```

4. Create superuser:
```bash
python manage.py createsuperuser
```

---

## 🧠 LLM Fine-tuning with TinyLlama

> ⚠️ To run the chatbot with fine-tuned TinyLlama, you **must have the base model locally or online.**

The fine-tuning process only trains adapter layers. To run the model in production, **both the base model and the adapters are required.**

### Download Base TinyLlama
```bash
huggingface-cli download TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T --local-dir ./tinyllama-base
```

### Code Paths (in `llm_model.py` or similar):
```python
LLAMA_MODEL_PATH = os.path.join(BASE_DIR, 'tinyllama-base')
# For remote: LLAMA_MODEL_PATH = "TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T"
FINETUNED_PATH = os.path.join(BASE_DIR, 'tinyllama-finetuned')
```

Ensure both paths exist locally before starting the chatbot server.

---

## 🔄 Run the Server

```bash
python manage.py runserver
```

Optional: use `ngrok` or `localhost.run` for public tunneling.

---

### 🐳 Docker Image

You can pull and run the CalmMind Mental Health Assistant using the prebuilt Docker image:

```bash
docker pull rasik09/calmmind-mental-health-assistant:latest
```

To run the container:

```bash
docker run -it --rm -p 8000:8000 rasik09/calmmind-mental-health-assistant:latest
```

> ⚠️ Make sure your PostgreSQL instance is running and accessible by the container. Configure environment variables accordingly.

If your app requires any `.env` file or volume mounts, you can run it like:

```bash
docker run -it --rm -p 8000:8000 \
  --env-file .env \
  rasik09/calmmind-mental-health-assistant:latest
```



## 📌 License
This project is developed for academic purposes and follows the MIT License.

---

## 🙌 Acknowledgements
- HuggingFace & TinyLlama Team
- Django & TailwindCSS Docs
- Mental health datasets (PHQ-9)
