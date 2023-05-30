from flask import Flask, jsonify, request
import speech_recognition as sr
from gtts import gTTS
import transformers
import os
import datetime
import numpy as np
from playsound import playsound
import requests
import json
import re

app = Flask(__name__)


class ChatBot():
    def __init__(self, name):
        self.name = name

    def speech_to_text(self, audio):
        recognizer = sr.Recognizer()
        try:
            self.text = recognizer.recognize_google(audio)
            print("Me  --> ", self.text)
        except:
            print("Me  -->  ERROR")

    @staticmethod
    def text_to_speech(text):
        print("Dev --> ", text)
        speaker = gTTS(text=text, lang="en")

        filename = 'res.mp3'
        speaker.save(filename)
        playsound(filename)
        os.remove(filename)

    def wake_up(self, text):
        return True if self.name in text.lower() else False

    @staticmethod
    def action_time():
        return datetime.datetime.now().time().strftime('%H:%M')

    @staticmethod
    def extract_ticket_number(text):
        # Use regex or other string manipulation techniques to extract the ticket number
        # Modify this function based on the format of your ticket numbers
        # This is just a basic example
        pattern = r"(?:ticket|INC|REQ|PRB)[\s_-]?(\w+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        else:
            return None

    @staticmethod
    def get_ticket_info(ticket_number):
        baseurl = "https://dev89134.service-now.com/api/now/table/incident/{ticket_number}"
        username = '<admin>'
        password = '<1/1YRrg^pwKO>'

        # Make the API call
        response = requests.get(baseurl, auth=("admin", "1/1YRrg^pwKO"))

        # Check the response status code
        if response.status_code == 200:
            # Extract the ticket information from the JSON response
            ticket_info = response.json().get('result')

            # Extract relevant information from ticket_info and format it as a response message
            # Customize this based on the information you want to retrieve from ServiceNow

            # Example: Extracting the status of the ticket
            status = ticket_info[0].get('state')

            # Format the response message
            response_message = "The status of ticket {ticket_number} is {status}."

            return response_message

        else:
            return "Failed to retrieve ticket information."


ai = ChatBot(name="dev")
nlp = transformers.pipeline("conversational", model="microsoft/DialoGPT-medium")
os.environ["TOKENIZERS_PARALLELISM"] = "true"


@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message')

    ai.text = message

    if ai.wake_up(ai.text) is True:
        res = "Hello, I am Dave the AI. What can I do for you?"
    elif "time" in ai.text:
        res = ai.action_time()
    elif any(i in ai.text for i in ["thank", "thanks"]):
        res = np.random.choice(
            ["you're welcome!", "anytime!", "no problem!", "cool!", "I'm here if you need me!", "mention not"])
    elif any(i in ai.text for i in ["exit", "close"]):
        res = np.random.choice(["Tata", "Have a good day", "Bye", "Goodbye", "Hope to meet soon", "peace out!"])
    elif "ticket" in ai.text.lower():
        ticket_number = ai.extract_ticket_number(ai.text)

        if ticket_number:
            res = ai.get_ticket_info(ticket_number)
        else:
            res = "Please provide a valid ticket number."
    else:
        if ai.text == "ERROR":
            res = "Sorry, come again?"
        else:
            chat = nlp(transformers.Conversation(ai.text), pad_token_id=50256)
            res = str(chat)
            res = res[res.find("bot >> ") + 6:].strip()

    ai.text_to_speech(res)
    return jsonify({'response': res})


if __name__ == '__main__':
    app.run(debug=True)
