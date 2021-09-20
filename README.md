# Tulip
Conversational AI Assistant

Installation 

1. 
> git clone 
> pip install -r requirements.txt

2. Setup wheel for PyAudio (not included in requirements.txt) - https://pypi.org/project/PyAudio/
3. Set environment variables for gcloud authentication - https://developers.google.com/maps/documentation/maps-static/get-api-key
4. Enable texttospeech and speech apis in the google cloud project - https://support.google.com/googleapi/answer/6158841?hl=en 
5. Set your GPT - 3 access key in key.txt - a file that must be created. The program automatically reads from that file.

Running

> python tulip.py




Note
1. playsound can error out sometimes when there is a delay between creating the audio file and responses, fixing it is a major headache.
2. Mic toggles on and off automatically 
3. Initial setup for speech to text gcloud takes a while
4. Change the Structure of the prompt for different use cases

Have fun!
