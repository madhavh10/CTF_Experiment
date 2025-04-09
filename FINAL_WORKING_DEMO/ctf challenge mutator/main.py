import os
import requests
import json
import streamlit as st
import re
import google.generativeai as genai

# CTFd Server Configuration
CTFD_URL = "http://localhost:8000"  # Change this if needed
API_TOKEN = "ctfd_b292ab6c693fc59b76c62c6145b44c4be91bac8b549681c61c2287e46b1d68b8"  # Replace with your API token

# Headers for authentication
HEADERS = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json",
}

# Set up Gemini API Key
genai.configure(api_key="AIzaSyBvcIqqahMhT76SWyUKfOkQcIz7U9uoE4A")

model = genai.GenerativeModel("gemini-2.0-flash")

# Function to generate challenge based on difficulty level
def generate_challenge(file_content, difficulty, filename): # NEED TO CREATE A GROUP OF PROMPT TEXT FILES FOR EACH CATEGORY
    prompt = (
        f"Create three different encrypted versions of this CTF flag using different encryption methods (easy, medium, hard). All must decode to the original flag\n\n"
        "Easy: Use a simple cipher (e.g., Base64, ROT13, Caesar shift).\n\n"
        "Medium: Apply a slightly more complex method (e.g., XOR with a short key, AES-128 with a known key, Vigenère cipher).\n\n"
        "Hard: Use a strong encryption method (e.g., AES-256 with an unknown key that must be brute-forced, RSA with small primes, or a multi-step cipher chain).\n\n"
        "Provide the encrypted outputs and necessary hints (without giving away the solution) for each level.\n\n"
        f"Original Flag:\n{file_content}\n\n"
        f"Generate the '{difficulty}' version of the encrypted flag."
    )
    # if category == "Cryptography":
    #     prompt =crypto.py f"Generate a {difficulty} level cryptography challenge based on the following code:\n{file_content}"
    
    response = model.generate_content(prompt)
    return response.text

# Function to create challenge file
def create_challenge_file(code, filename, difficulty):
    new_filename = f"{difficulty.lower()}_{filename}"
    with open(new_filename, "w") as f:
        f.write(code)
    return new_filename

# Function to upload challenge to CTFd
def upload_to_ctfd(challenge_name, category, description, value, flag, filename, difficulty):
    # Step 1: Create Challenge
    challenge_payload = {
        "name": f"{difficulty} - {challenge_name}",
        "category": category,
        "description": f"{description} (Difficulty: {difficulty})",
        "value": value,
        "state": "visible",
        "type": "standard",
    }

    response = requests.post(f"{CTFD_URL}/api/v1/challenges", json=challenge_payload, headers=HEADERS)
    if response.status_code == 200:
        challenge_id = response.json()["data"]["id"]
        st.success(f"Challenge '{challenge_name} ({difficulty})' Created! ID: {challenge_id}")
    else:
        st.error(f"Failed to create challenge: {response.text}")
        return False

    # Step 2: Add Flag
    flag_payload = {
        "challenge_id": challenge_id,
        "content": flag,
        "type": "static",
        "data": "",
    }

    response = requests.post(f"{CTFD_URL}/api/v1/flags", json=flag_payload, headers=HEADERS)
    if response.status_code == 200:
        st.success(f"Flag added for '{challenge_name} ({difficulty})'")
    else:
        st.error(f"Failed to add flag: {response.text}")
        return False

    # Step 3: Upload File
    try:
        files = {"file": open(filename, "rb")}
        data = {"challenge_id": challenge_id, "type": "challenge"}

        response = requests.post(f"{CTFD_URL}/api/v1/files", files=files, data=data, headers={"Authorization": f"Token {API_TOKEN}"})
        if response.status_code == 200:
            st.success(f"File '{filename}' uploaded successfully for '{challenge_name} ({difficulty})'!")
        else:
            st.error(f"Failed to upload '{filename}': {response.text}")
            return False
    except Exception as e:
        st.error(f"Error uploading file '{filename}': {e}")
        return False
    
    return True

# Streamlit UI
st.title("CTF Challenge Modulator with CTFd Integration")
st.write("Upload a challenge file, generate different difficulty levels, and upload directly to CTFd.")

# Challenge details input
with st.expander("Challenge Details", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        challenge_name = st.text_input("Challenge Name", "Dynamic Challenge")
        category = st.selectbox("Category", ["Web Exploitation", "Binary Exploitation", "Cryptography", "Forensics", "Reverse Engineering"])
    with col2:
        description = st.text_area("Description", "Solve this challenge to get the flag!")
        flag = st.text_input("Flag", "KPMG_CTF{dynamic_challenge_flag}")
        value = st.number_input("Point Value", min_value=10, value=100, step=10)

# File uploader
uploaded_file = st.file_uploader("Upload your challenge file", type=["py", "txt", "c", "cpp", "js", "html", "php"])

if uploaded_file is not None:
    file_content = uploaded_file.getvalue().decode("utf-8")
    filename = uploaded_file.name
    
    st.subheader("Original Challenge File:")
    st.code(file_content, language='python')
    
    if st.button("Generate & Upload All Difficulty Levels"):
        with st.spinner("Generating and uploading challenges..."):
            # Generate difficulties
            difficulties = ["Easy", "Medium", "Hard"]
            all_successful = True
            
            for difficulty in difficulties:
                st.subheader(f"Generating {difficulty} Challenge...")
                
                # Generate the challenge   # (NEED TO CHANGE THIS BASED ON THE CATEGORY OF THE CHALLENGE)
                modified_code = generate_challenge(file_content, difficulty, filename)
                st.code(modified_code, language='python')
                
                # Save to file
                modified_filename = create_challenge_file(modified_code, filename, difficulty)
                
                # Upload to CTFd
                st.subheader(f"Uploading {difficulty} Challenge to CTFd...")
                # Determine correct flag
                # import re

                if category == "Cryptography":
                    # Try to extract flag from original file content (format: KPMG_CTF{...})
                    match = re.search(r"KPMG_CTF\{.*?\}", file_content)
                    final_flag = match.group(0) if match else flag  # Use extracted flag or fallback to provided one
                else:
                    # Modify flag for non-crypto categories with difficulty suffix
                    final_flag = flag.replace("}", f"_{difficulty.upper()}" + "}")

                success = upload_to_ctfd(
                    challenge_name,
                    category,
                    description,
                    value + (difficulties.index(difficulty) * 50),
                    final_flag,
                    modified_filename,
                    difficulty
                )


                
                if not success:
                    all_successful = False
            
            if all_successful:
                st.success("All challenges successfully generated and uploaded to CTFd!")
            else:
                st.warning("Some challenges may not have been uploaded successfully. Check the logs above.")