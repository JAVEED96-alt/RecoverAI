# RecoverAI

> AI-powered revenue recovery system for failed payments.

## 🚀 Overview

RecoverAI is an AI-powered revenue recovery system designed to transform failed payments into measurable recovery opportunities.

Instead of simply detecting failed payments, RecoverAI:

1. Detects failed payments
2. Diagnoses the failure
3. Selects a recovery policy
4. Executes the recovery action
5. Records the recovery outcome
6. Measures recovered revenue
7. Uses Google Gemini to explain the decision

## 🎯 Problem

Failed payments represent potential lost revenue.

Traditional systems may identify that a payment failed, but they often don't provide an intelligent workflow for deciding what should happen next.

RecoverAI addresses this by connecting payment failure detection, ML diagnosis, policy decisions, execution, recovery outcomes, and AI explanations.

## 🧠 RecoverAI Pipeline

Payment
↓
Detection
↓
Diagnosis
↓
AI Policy
↓
Recovery Action
↓
Recovery Outcome
↓
Metrics
↓
Gemini Explanation

## 🤖 AI Components

### Detection

Identifies failed payment cases that require recovery.

### Diagnosis

Classifies the likely reason for the payment failure and provides confidence.

### AI Policy

Converts the diagnosis into an operational recovery action.

Examples include:

- Retry immediately
- Send recovery link
- Escalate to human review

### Gemini Explanation

Google Gemini converts the structured RecoverAI decision into a human-readable explanation.

Gemini explains the existing pipeline decision rather than replacing the detection, diagnosis, policy, or recovery systems.

## 📊 Evaluation Results

Synthetic evaluation results:

- Records evaluated: 75
- Recovery attempts: 23
- Successful recoveries: 12
- Failed recoveries: 11
- Recovery rate: 52.17%
- Revenue at risk: ₹290,647.66
- Revenue recovered: ₹153,605.40
- Revenue unrecovered: ₹137,042.26
- Exceptions: 52

> These are synthetic evaluation results and do not represent real recovered Razorpay funds.

## 🏗️ Architecture

Razorpay/Test Payments
        ↓
FastAPI Backend
        ↓
Payment Data
        ↓
Detection Layer
        ↓
Diagnosis Layer
        ↓
AI Policy Layer
        ↓
Execution Layer
        ↓
Recovery Outcome
        ↓
Metrics & Dashboard

Google Gemini provides the explanation layer over the structured recovery decisions.

## 🛠️ Tech Stack

### Backend

- Python
- FastAPI
- Pandas
- NumPy
- Scikit-learn
- Razorpay API
- Google Gemini

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

### Data & ML

- Synthetic Razorpay payment data
- Machine learning
- Recovery policy engine
- Evaluation metrics

## 📁 Project Structure

RecoverAI/
│
├── backend/
│
├── fronted/
│
├── outputs/
│
├── Decision/
│
├── dashboard.py
│
├── .gitignore
│
└── README.md

## ⚙️ Running the Backend

cd backend

Create a virtual environment:

python -m venv .venv

Activate it on Windows:

.venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Create a local `.env` file and add your API credentials.

Start FastAPI:

uvicorn api:app --reload

## 💻 Running the Frontend

cd fronted

npm install

npm run dev

Open the local Next.js application in your browser.

## 🔐 Environment Variables

Never commit API keys to GitHub.

Create a local `.env` file:

GEMINI_API_KEY=your_key_here

Add any other required credentials locally.

## 🎥 Demo

Demo video:

[Add your hackathon demo link here]

## 💡 Key Idea

RecoverAI follows the principle:

**Prediction → Decision → Action → Outcome → Explanation**

The goal is not just to detect failed payments, but to intelligently turn them into measurable recovery opportunities.

## 🏆 Hackathon

Built as an AI-powered revenue recovery solution for failed payment workflows.
