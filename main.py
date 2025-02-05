from fastapi import FastAPI, Request, Form, Depends
from twilio.twiml.messaging_response import MessagingResponse
import uvicorn
import time
import re

app = FastAPI()

# ADHD Screening Questions
questions = [
    "Do you frequently lose focus on tasks, even ones you enjoy? (Yes/No)",
    "Do you misplace important things like keys, phone, or wallet often? (Yes/No)",
    "Do you struggle to complete tasks before jumping to new ones? (Yes/No)",
    "Have you experienced these symptoms since childhood? (Yes/No)",
    "Do you feel restless or struggle to relax? (Yes/No)"
]

user_sessions = {}  # Store user conversations

SESSION_TIMEOUT = 600  # 10 minutes (in seconds)


@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    form_data = await request.form()
    user_message = form_data.get("Body", "").strip().lower()
    user_number = form_data.get("From")

    # If user is new or session expired, reset session
    if user_number not in user_sessions or time.time() - user_sessions[user_number]["timestamp"] > SESSION_TIMEOUT:
        user_sessions[user_number] = {"current_q": 0, "responses": [], "timestamp": time.time()}

    session = user_sessions[user_number]
    response = MessagingResponse()

    # Normalize Yes/No responses
    yes_patterns = re.compile(r"^(yes|yep|yup|yeah|sure|ok|okay|yea|affirmative)\b", re.IGNORECASE)
    no_patterns = re.compile(r"^(no|nope|nah|never|negative)\b", re.IGNORECASE)

    if session["current_q"] < len(questions):
        if yes_patterns.match(user_message):
            session["responses"].append("yes")
        elif no_patterns.match(user_message):
            session["responses"].append("no")
        elif session["current_q"] > 0:  # If mid-convo and invalid response
            response.message("Please respond with Yes or No.")
            return response.to_xml()

        response.message(questions[session["current_q"]])
        session["current_q"] += 1
        session["timestamp"] = time.time()  # Update last activity timestamp

    else:
        adhd_risk = session["responses"].count("yes")
        if adhd_risk >= 3:
            response.message("Your responses indicate possible ADHD symptoms. Consider speaking with a specialist.")
        else:
            response.message("Your responses do not strongly indicate ADHD, but if you're struggling, speaking with a professional might help.")

        # Remove session after completion
        del user_sessions[user_number]

    return response.to_xml()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
