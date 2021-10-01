
from __future__ import division
import os
import openai
import re
import sys
from google.cloud import speech, texttospeech
from six.moves import queue
import time
import torch
import random
import pyaudio
from playsound import playsound
import string
from pynput.keyboard import Key, Controller
import os

openai.api_key = ""
gcloud_key_path = "/home/parv/Documents/Tulip/gcloudkey.json"
prompt = "The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly.\n\nHuman: Hello, who are you?\nAI: I am an AI created by OpenAI. How can I help you today?\n"

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

""" Google Speech to Text """

class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)


""" Main runner code """

def listen_print_loop(responses):
    """Iterates through server responses, feeds them into GPT3 and synthesises the output - returns the whole transcript """ 

    #synthesize_text("I have started listening")
    prompt = "The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly.\n\nHuman: Hello, who are you?\nAI: I am an AI created by OpenAI. How can I help you today?\n "
    num_chars_printed = 0
    
    for response in responses:

        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript

        overwrite_chars = " " * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + "\r")
            sys.stdout.flush()

            num_chars_printed = len(transcript)

        else:
            if re.search(r"\b(exit|quit)\b", transcript, re.I):
                print("Exiting..")
                break

            num_chars_printed = 0

            text = str(transcript + overwrite_chars)

            print("You: {}".format(text))

            prompt = build_prompt(prompt, text)
            output = query_model(prompt)
            prompt += output + "\n"

            output = output.replace('AI:', '').replace('Human:', '')
            
            print(f"Tulip: {output}")

            
            try:
                toggle_mic()
                synthesize_text(output)
                toggle_mic()
                
                

            except:
                print("Error")
                toggle_mic()
                prompt = clear_prompt()
                continue

    return prompt
            
            
def main():

    language_code = "en-US"  

    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code,
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )

        responses = client.streaming_recognize(streaming_config, requests)
        
        transcript = listen_print_loop(responses)
        save_to_file(transcript)

""" GPT-3 code """

def build_prompt(prompt, input_text):

    return str(prompt + "Human : " + input_text + "\nAI:")

def clear_prompt():

    return "The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly.\n\nHuman: Hello, who are you?\nAI: I am an AI created by OpenAI. How can I help you today?\n "

def query_model(prompt):
    """ Queries the model and returns the finished prompt """
    
    response = openai.Completion.create(
    engine="davinci",
    prompt=prompt, 
    temperature=0.9,
    max_tokens=150,
    top_p=1,
    frequency_penalty=0.0,
    presence_penalty=0.6,
    stop=["\n", " Human:", " AI:"]
    )
    
    return response.choices[0].text

def generate_random_string():
    """ Random String for storing data"""
    return "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))


""" Google Text to Speech """

def synthesize_text(text):
    """Synthesizes speech from the input string of text."""
    
    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="fr-GB-Wavenet-C",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        request={"input": input_text, "voice": voice, "audio_config": audio_config}
    )

    with open("output.mp3", "wb") as out:
        out.write(response.audio_content)
        out.close()
    
    playsound("output.mp3")
    
""" Helper Methods """

def toggle_mic():
    """ Toggles the microphone on and off """

    # Presses Ctrl + -
    keyboard.press_and_release('ctrl+-')

def set_environment_variables(key_path):
    """ Sets the environment variables for gcloud authentication"""
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
    openai.api_key = read_key('key.txt')

def read_key(filename):

    f = open(filename, "r")
    return f.read()
    
def save_to_file(prompt):
    """ Saves data to file in path + conversation_data/chat_{random_key} """

    random_string = generate_random_string()
    file_name = "conversation_data/chat_" + random_string + ".txt"
    file = open(file_name, "w")
    file.write(prompt)
    file.close()
    print("File saved as " + file_name)

if __name__ == "__main__":
    openai.api_key = read_key("key.txt")
    set_environment_variables(gcloud_key_path)
    main()



