RecoverAI

AI-powered revenue recovery for failed payments.

RecoverAI is an AI-powered revenue recovery system that turns failed
payments into measurable recovery opportunities. Instead of only
detecting a failed payment, RecoverAI moves each case through detection,
diagnosis, policy selection, execution, recovery measurement, and
AI-powered explanation.

🚀 What RecoverAI Does

RecoverAI follows this end-to-end workflow:

Payment Data → Detection → Diagnosis → Policy → Execution → Recovery
Outcome → Final Metrics

The system answers: 1. Why did the payment fail? 2. What recovery action
should be taken? 3. Was the action executed? 4. Did the payment actually
recover?

🧠 Core Pipeline

Detection

Identifies failed payment cases that require recovery.

Diagnosis

Classifies the likely failure category and provides a confidence score.

AI Policy

Converts diagnosis and confidence into an operational recovery decision.
Actions include retry_now, retry_later, send_reminder, and
escalate_human.

Execution

Records whether the selected recovery action was sent, skipped, or
otherwise handled.

Recovery Outcome

Measures the actual outcome of the recovery attempt.

An executed recovery action is not the same as a recovered
payment.

Final Metrics

Aggregates attempts, successful recoveries, failed recoveries, revenue
at risk, recovered revenue, unrecovered revenue, and exceptions.

Gemini Explanation

Google Gemini provides a human-readable explanation of an individual
RecoverAI case using structured information already produced by the
pipeline. Gemini is an explanation layer; it does not replace the
detection, diagnosis, policy, execution, or recovery-outcome logic.

🤖 AI-Powered Payment Investigation

Payment Lookup lets an operator enter a payment ID and request an
AI-grounded investigation. The explanation can summarize what happened,
why it happened, the diagnosed bucket and confidence, the RecoverAI
decision, execution status, and recovery outcome.

📊 Evaluation Results

Metric                         Result

Records evaluated                  75
Recovery attempts                  23
Successful recoveries              12
Failed recoveries                  11
Recovery rate                  52.17%
Revenue at risk           ₹290,647.66
Revenue recovered         ₹153,605.40
Revenue unrecovered       ₹137,042.26
Exceptions                         52

Important: These are synthetic evaluation results and do not
represent real recovered Razorpay funds.

🏗️ Architecture

Payment Data
     ↓
Detection
     ↓
Diagnosis
     ↓
Policy
     ↓
Execution
     ↓
Recovery Outcome
     ↓
Final Metrics

Serving layer:

FastAPI → Next.js Dashboard

Gemini provides the explanation layer over structured recovery records.

🖥️ Dashboard

The dashboard provides: - Overview --- revenue risk, recovered
revenue, recovery rate, and exceptions - Revenue --- recovery
performance and revenue breakdown - AI Policy --- policy action
distribution and individual policy decisions - Recovery Audit ---
recovery outcomes and payment-level records - Exceptions --- failed
or review-required recovery cases - Payment Lookup --- payment
investigation with Gemini - Architecture --- visual RecoverAI
pipeline

📸 Screenshots

Add the screenshots to a screenshots/ folder and use:

Overview



Revenue



AI Policy



Recovery Audit



Exceptions



Gemini Payment Investigation



Architecture



🛠️ Tech Stack

Backend

Python

FastAPI

Uvicorn

Pandas

NumPy

Scikit-learn

Joblib

Razorpay SDK

Google Gemini

Python Dotenv

Frontend

Next.js

React

TypeScript

Tailwind CSS

AI/ML

Machine-learning based payment diagnosis

Confidence-based recovery policy

Recovery outcome evaluation

Google Gemini for grounded explanations

📁 Project Structure

RecoverAI/
├── backend/
│   ├── api.py
│   ├── pipeline.py
│   ├── explanation_layer.py
│   ├── audit_metrics_layer.py
│   ├── recovery_outcome_layer.py
│   ├── razorpay_service.py
│   ├── webhook.py
│   ├── requirements.txt
│   └── ...
│
├── fronted/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── package.json
│
├── Decision/
├── outputs/
├── dashboard.py
├── .gitignore
└── README.md

⚙️ Setup

Backend

cd backend
pip install -r requirements.txt

Create a local .env file with required credentials, for example:

GEMINI_API_KEY=your_gemini_api_key

Do not commit .env or API keys to GitHub.

Start FastAPI:

python -m uvicorn api:app --reload

The backend runs locally on http://127.0.0.1:8000.

Frontend

Open another terminal:

cd fronted
npm install
npm run dev

Then open the local Next.js URL, normally http://localhost:3000.

🔐 Environment Variables

Keep secrets local. The repository should contain placeholders such as
.env.example, never real API keys.

The .gitignore should exclude .env, .env.*, .venv/,
__pycache__/, *.pyc, fronted/node_modules/, and fronted/.next/.

🎥 Demo

The demo flow is:

Overview → Architecture → AI Policy → Recovery Audit → Payment Lookup
→ Gemini Explanation → Results

Add the final hackathon demo-video link here:

[Demo Video](YOUR_DEMO_VIDEO_LINK)

💡 Key Idea

Prediction → Decision → Action → Outcome → Explanation

The goal is not simply to detect failed payments. The goal is to turn
payment failures into intelligent, auditable, and measurable recovery
opportunities.

🏆 Hackathon Focus

RecoverAI demonstrates how machine learning, policy-based decisioning,
payment operations, recovery measurement, and generative AI can work
together in a single revenue recovery workflow.
