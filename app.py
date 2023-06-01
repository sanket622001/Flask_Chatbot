from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
from gtts import gTTS
import transformers
import playsound
import os
import time
import datetime
import numpy as np
import logging
import requests
import base64


app = Flask(__name__)
logger = logging.getLogger(__name__)


def get_incident_tickets():
    url = "https://dev89134.service-now.com/api/now/table/incident"

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Basic " + base64.b64encode(f"admin:1/1YRrg^pwKO".encode()).decode()
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for non-2xx status codes
        tickets = response.json().get('result', [])
        return tickets
    except requests.exceptions.RequestException as e:
        logger.error("An error occurred while retrieving incident tickets: %s", str(e))
        return []


class ChatBot:
    def __init__(self, name):
        self.name = name

    def speech_to_text(self, audio):
        recognizer = sr.Recognizer()
        try:
            self.text = recognizer.recognize_google(audio)
            print("Me  --> ", self.text)
        except Exception as e:
            logger.exception("Error in speech-to-text conversion")
            raise e

    @staticmethod
    def text_to_speech(text):
        print("Dev --> ", text)
        try:
            speaker = gTTS(text=text, lang="en")
            filename = 'res.mp3'
            speaker.save(filename)
            playsound.playsound(filename)
            os.remove(filename)
        except Exception as e:
            logger.exception("Error in text-to-speech conversion")
            raise e

    def wake_up(self, text):
        return True if self.name in text.lower() else False

    @staticmethod
    def action_time():
        return datetime.datetime.now().time().strftime('%H:%M')


# Define the ticket status dictionary
status_dict = {
    1: "New",
    2: "In Progress",
    3: "Closed",
    # Add more status mappings as needed
}


ai = ChatBot(name="dev")
nlp = transformers.pipeline("conversational", model="microsoft/DialoGPT-medium")
os.environ["TOKENIZERS_PARALLELISM"] = "true"


@app.route('/chat', methods=['POST'])
def chat():
    if request.method == 'POST':
        data = request.get_json()
        message = data['message']

        try:
            ai.text = message

            if ai.wake_up(ai.text) is True:
                res = "Hello, I am Dave the AI. What can I do for you?"
            elif "time" in ai.text:
                res = ai.action_time()
            elif any(i in ai.text for i in ["thank", "thanks"]):
                res = np.random.choice(
                    ["you're welcome!", "anytime!", "no problem!", "cool!", "I'm here if you need me!", "mention not"])
            elif any(i in ai.text for i in ["exit", "close"]):
                res = np.random.choice(
                    ["Tata", "Have a good day", "Bye", "Goodbye", "Hope to meet soon", "peace out!"])
            elif any(i in ai.text for i in ["incident", "tickets"]):
                tickets = get_incident_tickets()
                if tickets:
                    res = "Here are the incident tickets:\n"
                    for ticket in tickets:
                        res += f"Ticket ID: {ticket.get('number')}, Description: {ticket.get('short_description')}, Status: {status_dict.get(ticket.get('state'), 'Unknown')}\n"
                else:
                    res = "Failed to retrieve incident tickets."
            else:
                if ai.text == "ERROR":
                    res = "Sorry, come again?"
                else:
                    chat = nlp(transformers.Conversation(ai.text), pad_token_id=50256)
                    res = str(chat)
                    res = res[res.find("bot >> ") + 6:].strip()

            ai.text_to_speech(res)
            return jsonify({'response': res})
        except Exception as e:
            logger.exception("Error in processing user request")
            return jsonify({'error': 'An error occurred. Please try again later.'}), 500


@app.route('/speak', methods=['GET'])
def speak():
    text = request.args.get('text')
    ai.text_to_speech(text)
    return ''


if __name__ == '__main__':
    app.run()
