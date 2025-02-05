from fastapi import FastAPI, Request, Form
from twilio.twiml.messaging_response import MessagingResponse
import uvicorn

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Server is running!"}

# ADHD Screening Questions
questions = [
    "Do you frequently lose focus on tasks, even ones you enjoy? (Yes/No)",
    "Do you misplace important things like keys, phone, or wallet often? (Yes/No)",
    "Do you struggle to complete tasks before jumping to new ones? (Yes/No)",
    "Have you experienced these symptoms since childhood? (Yes/No)",
    "Do you feel restless or struggle to relax? (Yes/No)"
]

user_sessions = {}  # Stores user responses temporarily

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request, Body: str = Form(...), From: str = Form(...)):
    user_message = Body.strip().lower()
    user_number = From  # This is the user's phone number from WhatsApp
    
    if user_number not in user_sessions:
        user_sessions[user_number] = {"current_q": 0, "responses": []}

    session = user_sessions[user_number]
    response = MessagingResponse()

    if session["current_q"] < len(questions):
        if user_message in ["yes", "no"] or session["current_q"] == 0:
            if session["current_q"] > 0:
                session["responses"].append(user_message)
            response.message(questions[session["current_q"]])
            session["current_q"] += 1
        else:
            response.message("Please respond with Yes or No.")
    else:
        adhd_risk = session["responses"].count("yes")
        if adhd_risk >= 3:
            response.message("Your responses indicate possible ADHD symptoms. Consider speaking with a specialist.")
        else:
            response.message("Your responses do not strongly indicate ADHD, but if you're struggling, speaking with a professional might help.")
        user_sessions.pop(user_number)  # Clear session after completion
    
    return response.to_xml()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
