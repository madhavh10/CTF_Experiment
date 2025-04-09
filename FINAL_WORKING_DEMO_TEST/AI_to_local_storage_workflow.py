import os
import json
import time
import subprocess
import requests
import csv
import ollama
import re
import google.generativeai as genai
import ast
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

API_KEY = "AIzaSyBvcIqqahMhT76SWyUKfOkQcIz7U9uoE4A"  # Replace with your actual Gemini API key
genai.configure(api_key=API_KEY)

CHALLENGE_DIR = "crypto/challenge1/"
PROMPT_PATH = os.path.join(CHALLENGE_DIR, "prompts/new_prompt_test.txt")
OUTPUT_DIR = "CTF01"
CSV_TEMPLATE_DIR = os.path.join(OUTPUT_DIR, "csv_templates")
CSV_FILE = os.path.join(CSV_TEMPLATE_DIR, "caesar_cipher.csv")
JSON_FILE = os.path.join(CSV_TEMPLATE_DIR, "caesar_cipher.json")
MODIFIED_DIR = os.path.join(OUTPUT_DIR, "modified_challenges")

os.makedirs(CSV_TEMPLATE_DIR, exist_ok=True)
os.makedirs(MODIFIED_DIR, exist_ok=True)


def clean_json_data(data):
    """Cleans JSON data to keep only required keys, including flag and files."""
    allowed_keys = {
        "name",
        "description",
        "category",
        "value",
        "type",
        "state",
        "max_attempts",
        "flag",
        "files"
    }
    return [{k: v for k, v in entry.items() if k in allowed_keys and v is not None} for entry in data]


def csv_to_json(csv_file_path, json_file_path):
    allowed_keys = {
        "name",
        "description",
        "category",
        "value",
        "type",
        "state",
        "max_attempts",
        "flag",
        "files"
    }

    with open(csv_file_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        challenges = []
        for row in reader:
            challenge = {}
            for key in row:
                if key in allowed_keys:
                    if key == "files":
                        try:
                            challenge[key] = ast.literal_eval(row[key])
                        except Exception:
                            challenge[key] = []
                    else:
                        challenge[key] = row[key]
            challenges.append(challenge)

    # Save JSON output
    with open(json_file_path, "w", encoding="utf-8") as json_file:
        json.dump(challenges, json_file, indent=4)




def get_ai_response(prompt):
    """Uses AI to generate a challenge template in CSV format."""
    try:
        response = ollama.chat(model="llama3", messages=[{"role": "user", "content": prompt}])
        raw_text = response["message"]["content"].strip()

        # Extract CSV from triple backticks if present
        csv_match = re.search(r"```(?:csv)?\s*(name,.*?\n(?:.+\n)*?)```", raw_text, re.DOTALL)

        if csv_match:
            return csv_match.group(1).strip()

        # Fallback: try extracting directly if no backticks
        # Fallback: extract up to the first blank line or extra commentary
        csv_match = re.search(r"(name,description,category,value,type,state,max_attempts,flag,files[\s\S]*?)(?:\n\s*\n|$)", raw_text)

        if csv_match:
            return csv_match.group(1).strip()

        return "Error: No valid CSV format found in AI response."

    except Exception as e:
        return f"Error fetching AI response: {str(e)}"


def generate_json_template():
    """Generates a JSON challenge template from a prompt.txt file."""
    if not os.path.exists(PROMPT_PATH):
        print(f"Error: Prompt file {PROMPT_PATH} does not exist.")
        return

    with open(PROMPT_PATH, "r", encoding="utf-8") as file:
        prompt = file.read()

    csv_content = get_ai_response(prompt)

    if "Error" in csv_content:
        print(csv_content)
        return

    with open(CSV_FILE, "w", encoding="utf-8") as file:
        file.write(csv_content)

    print(f"CSV saved successfully at {CSV_FILE}")

    csv_to_json(CSV_FILE, JSON_FILE)
    print(f"JSON saved successfully at {JSON_FILE}")


def start_streamlit():
    """Starts the Streamlit app in the background."""
    subprocess.Popen(["streamlit", "run", "sample_ai_mutation.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Starting CTF challenge mutator app...")

    for _ in range(30):
        try:
            response = requests.get("http://localhost:8501")
            if response.status_code == 200:
                print("The app is running!")
                return
        except requests.ConnectionError:
            pass
        time.sleep(1)

    print("Error: The app did not start in time.")
    exit(1)


def generate_challenge(file_content, difficulty):
    prompt = (
        f"Create three different encrypted versions of this CTF flag using different encryption methods (easy, medium, hard). All must decode to the original flag\n\n"
        "Easy: Use a simple cipher (e.g., Base64, ROT13, Caesar shift).\n\n"
        "Medium: Apply a slightly more complex method (e.g., XOR with a short key, or use Vignere Cipher).\n\n"
        "Hard: Use a strong encryption method (e.g., AES encryption with ECB mode of encryption and No Padding and use a known IV and key size as 128 bits).\n\n"
        "Provide the encrypted outputs and necessary hints (without giving away the solution) for each level.\n\n"
        f"Original Flag:\n{file_content}\n\n"
        f"Generate the '{difficulty}' version of the encrypted flag."
    )

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text if hasattr(response, "text") else "Error: No response received."
    except Exception as e:
        return f"Error generating challenge: {str(e)}"


def process_challenges():
    """Reads challenge files, modifies them, and saves the output."""
    challenge_files = [f for f in os.listdir(CHALLENGE_DIR) if f.endswith((".py", ".txt"))]

    if not challenge_files:
        print("No challenge files found in the directory.")
        return

    for filename in challenge_files:
        file_path = os.path.join(CHALLENGE_DIR, filename)

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                file_content = file.read()
        except Exception as e:
            print(f"Error reading file {filename}: {e}")
            continue

        for difficulty in ["Easy", "Medium", "Hard"]:
            modified_challenge = generate_challenge(file_content, difficulty)

            if "Error" in modified_challenge:
                print("Skipping file due to AI error")
                continue
    
            mod_filename = f"{difficulty.lower()}_{filename}"
            mod_file_path = os.path.join(MODIFIED_DIR, mod_filename)

            with open(mod_file_path, "w", encoding="utf-8") as mod_file:
                mod_file.write(modified_challenge)

    print("All modified challenges saved successfully!")


def main():
    """Main execution workflow."""
    print("Starting Streamlit server...")
    start_streamlit()

    print("Generating JSON template...")
    generate_json_template()

    print("Processing challenges...")
    process_challenges()

    print("All tasks completed successfully!")


if __name__ == "__main__":
    main()
