import google.generativeai as genai
import os

api_key = "AIzaSyDKZAhVP3Gdgm2nnwiOhEjH1jI15KyzV70"
genai.configure(api_key=api_key)

try:
    with open("models.txt", "w") as f:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                f.write(f"Model: {m.name}\n")
    print("Models written to models.txt")
except Exception as e:
    print(f"Error listing models: {e}")
