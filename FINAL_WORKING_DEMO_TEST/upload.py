import requests
import json
import streamlit as st
import google.generativeai as genai
import os

# CTFd Server URL
CTFD_URL = "http://localhost:8000"  # Change this if needed
API_TOKEN = "ctfd_b292ab6c693fc59b76c62c6145b44c4be91bac8b549681c61c2287e46b1d68b8"  # Replace with your API token

# Set up Gemini API Key
API_KEY = "AIzaSyBvcIqqahMhT76SWyUKfOkQcIz7U9uoE4A"
genai.configure(api_key=API_KEY)

# Headers for authentication
HEADERS = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json",
}

# Load challenges from JSON file
def generate_challenges():
    try:
        with open("challenges.json", "r") as f:
            data = json.load(f)
            challenges = data.get("results", [])  # ✅ Extract only the list of challenges
        return challenges
    except FileNotFoundError:
        st.error("❌ 'challenges.json' file not found.")
        return []
    except json.JSONDecodeError:
        st.error("❌ Error parsing 'challenges.json'. Make sure it's valid JSON.")
        return []
        
# Function to upload challenges to CTFd
def upload_challenges():
    challenges = generate_challenges()

    for challenge in challenges:
        challenge_payload = {
            "name": challenge["name"],
            "category": challenge["category"],
            "description": challenge["description"],
            "value": challenge["value"],
            "state": "visible",
            "type": "standard",
        }

        # Step 1: Create Challenge
        response = requests.post(f"{CTFD_URL}/api/v1/challenges", json=challenge_payload, headers=HEADERS)
        print("######### Step #1", response.text)
        if response.status_code == 200:
            challenge_id = response.json()["data"]["id"]
            print(f"✅ Challenge '{challenge['name']}' Created! ID: {challenge_id}")
        else:
            print(f"❌ Failed to create challenge: {response.text}")
            continue

        # Step 2: Add Flag
        flag_payload = {
            "challenge_id": challenge_id,
            "content": challenge["flag"],
            "type": "static",
            "data": "",
        }

        response = requests.post(f"{CTFD_URL}/api/v1/flags", json=flag_payload, headers=HEADERS)
        print("######### Step #2", response.text)
        if response.status_code == 200:
            print(f"✅ Flag added for '{challenge['name']}'")
        else:
            print(f"❌ Failed to add flag: {response.text}")
            continue

        # Step 3: Upload Files
        for filename in challenge.get("files", []):
            try:
                file_path = os.path.join(".", filename)
                files = {"file": open(file_path, "rb")}
                data = {"challenge_id": challenge_id, "type": "challenge"}

                response = requests.post(f"{CTFD_URL}/api/v1/files", files=files, data=data,
                                         headers={"Authorization": f"Token {API_TOKEN}"})
                print("###### Files #3", response.text)
                if response.status_code == 200:
                    print(f"✅ File '{filename}' uploaded successfully for '{challenge['name']}'!")
                else:
                    print(f"❌ Failed to upload '{filename}': {response.text}")
            except Exception as e:
                print(f"❌ Error uploading file '{filename}': {e}")

    print("🎯 All challenges successfully injected into CTFd!")

# Streamlit UI
st.title("CTF Challenge Modulator")
st.write("Generate challenges dynamically and upload them to CTFd.")

if st.button("Upload Challenges to CTFd"):
    upload_challenges()
    st.success("Challenges successfully uploaded!")
