from fastapi import FastAPI, WebSocket
import uvicorn
import re

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Server is running!"}

questions = [
    "Do you frequently lose focus on tasks, even ones you enjoy?",
    "Do you misplace important things like keys, phone, or wallet often?",
    "Do you struggle to complete tasks before jumping to new ones?",
    "Have you experienced these symptoms since childhood?",
    "Do you feel restless or struggle to relax?"
]

user_sessions = {}

@app.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    user_id = websocket.client

    if user_id not in user_sessions:
        user_sessions[user_id] = {"current_q": 0, "responses": []}

    session = user_sessions[user_id]

    await websocket.send_text("Hello! Answer Yes or No to the following questions.")

    while session["current_q"] < len(questions):
        question = questions[session["current_q"]]
        await websocket.send_text(question)

        user_response = await websocket.receive_text()
        user_response = user_response.strip().lower()

        yes_patterns = re.compile(r"^(yes|yep|yeah|y|sure|ok)\b", re.IGNORECASE)
        no_patterns = re.compile(r"^(no|nope|nah|n|never)\b", re.IGNORECASE)

        if yes_patterns.match(user_response):
            session["responses"].append("yes")
        elif no_patterns.match(user_response):
            session["responses"].append("no")
        else:
            await websocket.send_text("Please respond with Yes or No.")
            continue

        session["current_q"] += 1

    adhd_risk = session["responses"].count("yes")
    if adhd_risk >= 3:
        await websocket.send_text("Your responses indicate possible ADHD symptoms. Consider speaking with a specialist.")
    else:
        await websocket.send_text("Your responses do not strongly indicate ADHD, but if you're struggling, speaking with a professional might help.")

    await websocket.close()
    del user_sessions[user_id]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
