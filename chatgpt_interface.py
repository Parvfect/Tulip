# Note: you need to be using OpenAI Python v0.27.0 for the code below to work
import openai
import json
import colorama
from colorama import Fore

openai.api_key = ""

def message_loop():

    
    conversation_history = [{"role": "system", "content": "You are a helpful assistant."}]
    while(True):
        user_input = input(Fore.WHITE + "Enter input -  ")
        conversation_history.append({"role": "user", "content": f"{user_input}"})
        reply = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation_history
        ).choices[0].message.content
        print(Fore.RED + f"{reply}")
        conversation_history.append({"role": "assistant", "content": reply})

message_loop()
