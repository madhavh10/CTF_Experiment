import os
import shutil
import time
import json
import csv
import ast
import re
import subprocess
import requests
import streamlit as st
import google.generativeai as genai
import ollama

# Setup
CHALLENGE_DIR = "crypto/challenge1/"
OUTPUT_DIR = "CTF01"
CSV_TEMPLATE_DIR = os.path.join(OUTPUT_DIR, "csv_templates")
MODIFIED_DIR = os.path.join(OUTPUT_DIR, "modified_challenges")
CSV_FILE = os.path.join(CSV_TEMPLATE_DIR, "caesar_cipher.csv")
JSON_FILE = os.path.join(CSV_TEMPLATE_DIR, "caesar_cipher.json")
PROMPT_PATH = os.path.join(CHALLENGE_DIR, "prompts/new_prompt_test.txt")

os.makedirs(CSV_TEMPLATE_DIR, exist_ok=True)
os.makedirs(MODIFIED_DIR, exist_ok=True)

# Gemini API
GEMINI_API_KEY = "AIzaSyBvcIqqahMhT76SWyUKfOkQcIz7U9uoE4A"
genai.configure(api_key=GEMINI_API_KEY)

# CTFd Setup
CTFD_URL = "http://localhost:8000"
API_TOKEN = "ctfd_b292ab6c693fc59b76c62c6145b44c4be91bac8b549681c61c2287e46b1d68b8"
HEADERS = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json",
}


def get_ai_response(prompt):
    try:
        response = ollama.chat(model="llama3", messages=[{"role": "user", "content": prompt}])
        raw_text = response["message"]["content"].strip()
        match = re.search(r"```(?:csv)?\s*(name,.*?\n(?:.+\n)*?)```", raw_text, re.DOTALL)
        if match:
            return match.group(1).strip()
        match = re.search(r"(name,description,category,value,type,state,max_attempts,flag,files[\s\S]*?)(?:\n\s*\n|$)", raw_text)
        return match.group(1).strip() if match else "Error: No valid CSV format found."
    except Exception as e:
        return f"Error: {str(e)}"


def csv_to_json(csv_file, json_output_name="caesar_cipher.json"):
    output_path = os.path.join(CSV_TEMPLATE_DIR, json_output_name)

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data = []
        for row in reader:
            challenge = {}
            for key, value in row.items():
                if key == "files":
                    # Auto-generate the correct modified filename
                    challenge_name = row["name"].strip().lower().replace(" ", "_").replace("-", "_")
                    challenge_file = f"modified_challenges/{challenge_name}.txt"
                    challenge["files"] = [challenge_file]
                else:
                    challenge[key] = value
            data.append(challenge)

    with open(output_path, "w", encoding="utf-8") as jf:
        json.dump(data, jf, indent=4)


def generate_json_template():
    if not os.path.exists(PROMPT_PATH):
        st.error("Prompt file not found.")
        return
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        prompt = f.read()
    csv_content = get_ai_response(prompt)
    if "Error" in csv_content:
        st.error(csv_content)
        return
    with open(CSV_FILE, "w", encoding="utf-8") as f:
        f.write(csv_content.strip())
    csv_to_json(CSV_FILE, "caesar_cipher.json")
    st.success("CSV & JSON generated!")
    st.info(f"✅ JSON saved to: `{JSON_FILE}`")


def generate_challenge(file_content, difficulty):
    prompt = f"""Create three different encrypted versions of this CTF flag using different encryption methods (easy, medium, hard). 
Easy: Use a simple cipher (Base64, ROT13).
Medium: Use XOR or Vigenère.
Hard: Use AES (ECB, 128-bit, fixed IV). 
Original Flag:\n{file_content}
Generate the '{difficulty}' version only.
"""
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"


def process_challenges():
    files = [f for f in os.listdir(CHALLENGE_DIR) if f.endswith((".py", ".txt"))]
    for filename in files:
        base_name = os.path.splitext(filename)[0]  # e.g., challenge1
        with open(os.path.join(CHALLENGE_DIR, filename), "r") as f:
            content = f.read()

        for level in ["Easy", "Medium", "Hard"]:
            modified = generate_challenge(content, level)
            mod_filename = f"{base_name}_{level.lower()}.txt"
            mod_path = os.path.join(MODIFIED_DIR, mod_filename)
            with open(mod_path, "w") as out:
                out.write(modified)
    st.success("All AI-modified challenges saved to modified_challenges/")


def upload_challenges():
    try:
        with open(JSON_FILE, "r") as f:
            challenges = json.load(f)
    except:
        st.error("Couldn't read caesar_cipher.json")
        return

    for ch in challenges:
        payload = {
            "name": ch["name"],
            "category": ch["category"],
            "description": ch["description"],
            "value": ch["value"],
            "state": "visible",
            "type": "standard",
        }
        r = requests.post(f"{CTFD_URL}/api/v1/challenges", json=payload, headers=HEADERS)
        if r.status_code == 200:
            ch_id = r.json()["data"]["id"]
            flag_payload = {"challenge_id": ch_id, "content": ch["flag"], "type": "static"}
            requests.post(f"{CTFD_URL}/api/v1/flags", json=flag_payload, headers=HEADERS)

            for fname in ch.get("files", []):
                fpath = os.path.join(".", fname)
                if os.path.exists(fpath):
                    with open(fpath, "rb") as f:
                        files = {"file": f}
                        data = {"challenge_id": ch_id, "type": "challenge"}
                        requests.post(f"{CTFD_URL}/api/v1/files", files=files, data=data,
                                      headers={"Authorization": f"Token {API_TOKEN}"})
    st.success("Challenges uploaded to CTFd!")


# ======================
# ✅ Streamlit UI
# ======================
st.title("🚀 Auto CTF Generator")
st.write("Click button below to generate + upload CTF challenges.")

if st.button("Run End-to-End CTF Workflow"):
    generate_json_template()
    process_challenges()
    upload_challenges()
