import openai
import winsound
import sys
import time
import keyboard
import json
import speech_recognition as sr
import http.client
import json
import requests
from config import *
from utils.translate import *
from utils.TTS import *
from utils.subtitle import *
from utils.promptMaker import *
from utils.twitch_config import *

conn = http.client.HTTPConnection("127.0.0.1:1337")
thread_id = "127.0.0.1"

# to help the CLI write unicode characters to the terminal
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)

# use your own API Key, you can get it from https://openai.com/. I place my API Key in a separate file called config.py
openai.api_key = "sk-nah"

conversation = []
# Create a dictionary to hold the message data
history = {"history": conversation}

mode = 0
total_characters = 0
chat = ""
chat_now = ""
chat_prev = ""
is_Speaking = False
owner_name = "Valastor"
blacklist = ["Nightbot", "streamelements"]

# function to get the user's input audio
def record_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Recording...")
        audio = r.listen(source)
        print("Stopped recording.")
        with open("recorded_audio.wav", "wb") as file:
            file.write(audio.get_wav_data())

        print("Audio saved to recorded_audio.wav")
        return audio

# function to transcribe the user's audio
def transcribe_audio(audio):
    global chat_now
    r = sr.Recognizer()
    try:
        chat_now = r.recognize_google(audio)
        print ("Question: " + chat_now)
        result = owner_name + " said " + chat_now
        conversation.append({'role': 'user', 'content': result})
        ask_ai(chat_now)
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))


def ask_ai(question):
    # Read the identity from the identity.txt file
    with open('characterConfig/Pina/identity.txt', 'r') as file:
        identity = file.read().strip()

    memories = [
        {
            "content": identity,
            "role": "system"
        },
        {
            "content": question,
            "role": "user"
        }
    ]

    data = {
        "messages": memories,
        "model": "mistral-ins-7b-q4",
        "stream": False,
        "max_tokens": 4096,
        "stop": ["\n", "Human:", "AI:"],
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "temperature": 0.7,
        "top_p": 0.95
    }

    headers = {'Content-Type': 'application/json'}

    response = requests.post('http://localhost:1337/v1/chat/completions', headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_data = response.json()
        answer = response_data['choices'][0]['message']['content']
        print("Answer: " + answer)
        translate_text(answer)
    else:
        print(f"Request failed with status code {response.status_code}")

def getPrompt(conversation):
    # Join all conversation content with newline character
    prompt = "\n".join(d['content'] for d in conversation)
    return prompt

def calculate_total_characters(conversation):
    return sum(len(d['content']) for d in conversation)

def openai_ask(question, conversation):
    total_characters = calculate_total_characters(conversation)

    while total_characters > 4000:
        if conversation:
            try:
                conversation.pop(2)
                total_characters = calculate_total_characters(conversation)
            except IndexError as e:
                print("Error: Conversation list is empty.")
        else:
            break

    with open("conversation.json", "w", encoding="utf-8") as file:
        json.dump(conversation, file, indent=4)

    prompt = getPrompt()

    response = openai.Completion.create(
        engine="davinci-codex",
        prompt=prompt,
        max_tokens=100,
        n=1,
        stop=None,
        temperature=0.7,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    answer = response.choices[0].text.strip()
    print("Answer: " + answer)
    translate_text(answer)



# translating is optional
def translate_text(text):
    global is_Speaking
    #detect = detect_google(text)
    #tts_en = translate_google(text, f"{detect}", "EN")
    try:
        print("EN Answer: " + text)
    except Exception as e:
        print("Error printing text: {0}".format(e))
        return

    # Choose between the available TTS engines
    # Japanese TTS
    # voicevox_tts(tts)

    # Silero TTS, Silero TTS can generate English, Russian, French, Hindi, Spanish, German, etc. Uncomment the line below. Make sure the input is in that language
    silero_tts(text, "en", "v3_en", "en_21")

    # Generate Subtitle
    #generate_subtitle(chat_now, text)

    #time.sleep(1)

    # is_Speaking is used to prevent the assistant speaking more than one audio at a time
    is_Speaking = True
    winsound.PlaySound("test.wav", winsound.SND_FILENAME)
    is_Speaking = False

    # Clear the text files after the assistant has finished speaking
    time.sleep(1)
    with open ("output.txt", "w") as f:
        f.truncate(0)
    with open ("chat.txt", "w") as f:
        f.truncate(0)


if __name__ == "__main__":
    try:
            print("Press and Hold Right Shift to record audio")
            while True:
                if keyboard.is_pressed('RIGHT_SHIFT'):
                    audio = record_audio()
                    transcribe_audio(audio)
    except KeyboardInterrupt:
        t.join()
        print("Stopped")

