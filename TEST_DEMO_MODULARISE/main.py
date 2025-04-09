# Required imports
import os
import re
import json
import requests
import subprocess
import streamlit as st
import google.generativeai as genai
import re
from pathlib import Path

# Configuration
CTFD_URL = "http://localhost:8000"
API_TOKEN = "ctfd_b292ab6c693fc59b76c62c6145b44c4be91bac8b549681c61c2287e46b1d68b8"
HEADERS = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json",
}
genai.configure(api_key="AIzaSyBvcIqqahMhT76SWyUKfOkQcIz7U9uoE4A")
model = genai.GenerativeModel("gemini-2.0-flash")

def clean_dockerfile(content):
    return re.sub(r"```(?:dockerfile)?\s*([\s\S]*?)\s*```", r"\1", content).strip()

def clean_php(content):
    return re.sub(r"```(?:php)?\s*([\s\S]*?)\s*```", r"\1", content).strip()

# Prompt Generators

def generate_crypto_challenge(file_content, difficulty):
    prompt = f"""
Create three different encrypted versions of this CTF flag using different encryption methods (easy, medium, hard). All must decode to the original flag

Easy: Use a simple cipher (e.g., Base64, ROT13, Caesar shift).
Medium: Use a complex cipher (e.g., XOR, Vigenere, AES-128 with known key).
Hard: Use strong/multi-step cipher (AES-256 with unknown key, RSA, chained encryption).

Provide encrypted outputs and required hints without solution.
Original Flag:
{file_content}

Generate the '{difficulty}' version.
"""
    response = model.generate_content(prompt)
    return response.text

def generate_web_challenge(index_php, dockerfile, flag_txt, difficulty):
    prompt = f"""
You are given a Capture The Flag (CTF) web challenge consisting of a PHP file (index.php), a Dockerfile, and a flag.txt file.

Your task:
- Analyze the PHP code and identify the main vulnerability.
- Based on the difficulty level ({difficulty}), enhance the challenge by modifying the existing code *without referencing or introducing new files that are not already provided*.
- DO NOT reference any files like about.html or other assets that are not explicitly included in the input.
- The goal is to retain the core vulnerability but make it more complex based on difficulty:
  - Easy: Introduce a basic vulnerability (e.g., file inclusion with a known path).
  - Medium: Obfuscate or layer the vulnerability slightly (e.g., whitelist bypass, variable overwrite).
  - Hard: Make it harder to exploit (e.g., chained bugs, filters, deeper logic).
- Ensure all files required by the Dockerfile exist and match the output exactly.

Here are the challenge components:

PHP Code:
{index_php}

Dockerfile:
{dockerfile}

Flag:
{flag_txt}

Now generate a new version of the challenge for the specified difficulty. Only output content for the 3 files below, and make sure they are logically consistent and self-contained.

Output format:
---DOCKERFILE---
<dockerfile content>
---INDEX.PHP---
<php content>
---FLAG.TXT---
<flag content>
"""
    response = model.generate_content(prompt)
    return response.text

def safe_extract(section_name, next_section, content):
    pattern = rf"---{section_name}---\s*(.*?)\s*---{next_section}---"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise ValueError(f"Missing section: {section_name}")
    return match.group(1).strip()

def parse_generated_files(content):
    dockerfile = safe_extract("DOCKERFILE", "INDEX.PHP", content)
    index_php = safe_extract("INDEX.PHP", "FLAG.TXT", content)
    match = re.search(r"---FLAG.TXT---\s*(.*)", content, re.DOTALL)
    if not match:
        raise ValueError("Missing section: FLAG.TXT")
    flag_txt = match.group(1).strip()
    return dockerfile, index_php, flag_txt

def save_generated_files(difficulty, dockerfile_content, index_php, flag_txt, folder_name):
    path = Path(folder_name) / difficulty.lower()
    path.mkdir(parents=True, exist_ok=True)
    (path / "Dockerfile").write_text(clean_dockerfile(dockerfile_content))
    (path / "index.php").write_text(clean_php(index_php), encoding="utf-8")
    (path / "flag.txt").write_text(flag_txt)
    return path

def run_docker_container(folder, diff):
    container_name = diff.lower()
    base_port = 9000
    port = base_port + ["Easy", "Medium", "Hard"].index(diff)
    if not os.path.exists(os.path.join(folder, "Dockerfile")):
        raise FileNotFoundError("Dockerfile not found in " + folder)
    for f in ["index.php", "flag.txt"]:
        if not os.path.exists(os.path.join(folder, f)):
            raise FileNotFoundError(f"{f} missing in {folder}")
    subprocess.run(["docker", "build", "-t", container_name, folder], check=True)
    subprocess.run([
        "docker", "run", "-d", "--rm", "-p", f"{port}:80",
        "--name", container_name, container_name
    ], check=True)
    return f"http://localhost:{port}"

# Upload Functions

def upload_to_ctfd_web(challenge_name, category, description, value, flag, url, difficulty):
    payload = {
        "name": f"{difficulty} - {challenge_name}",
        "category": category,
        "description": f"{description} (Difficulty: {difficulty})\n\nURL: {url}",
        "value": value,
        "state": "visible",
        "type": "standard",
    }
    res = requests.post(f"{CTFD_URL}/api/v1/challenges", json=payload, headers=HEADERS)
    if res.status_code != 200:
        st.error(f"Failed to create challenge: {res.text}")
        return False
    cid = res.json()['data']['id']
    flag_payload = {
        "challenge_id": cid,
        "content": flag,
        "type": "static",
        "data": "",
    }
    flag_res = requests.post(f"{CTFD_URL}/api/v1/flags", json=flag_payload, headers=HEADERS)
    return flag_res.status_code == 200

def upload_to_ctfd_crypto(challenge_name, category, description, value, flag, url, difficulty, file_dir):
    # Step 1: Create challenge
    payload = {
        "name": f"{difficulty} - {challenge_name}",
        "category": category,
        "description": f"{description} (Difficulty: {difficulty})\n\nURL: {url}",
        "value": value,
        "state": "visible",
        "type": "standard",
    }
    res = requests.post(f"{CTFD_URL}/api/v1/challenges", json=payload, headers=HEADERS)
    if res.status_code != 200:
        st.error(f"Failed to create Crypto challenge: {res.text}")
        return False

    cid = res.json()['data']['id']

    # Step 2: Add flag
    flag_payload = {
        "challenge_id": cid,
        "content": flag,
        "type": "static",
        "data": "",
    }
    flag_res = requests.post(f"{CTFD_URL}/api/v1/flags", json=flag_payload, headers=HEADERS)

    # Step 3: Upload & link files (Dockerfile, challenge.txt, flag.txt)
    file_paths = [
        os.path.join(file_dir, "Dockerfile"),
        os.path.join(file_dir, "challenge.txt"),
        os.path.join(file_dir, "flag.txt"),
    ]
    uploaded_file_ids = []

    for file_path in file_paths:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}
                file_res = requests.post(f"{CTFD_URL}/api/v1/files", files=files, headers={"Authorization": f"Token {API_TOKEN}"})
                if file_res.status_code == 200:
                    file_id = file_res.json()['data']['id']
                    uploaded_file_ids.append(file_id)
                else:
                    st.error(f"File upload failed for {file_path}: {file_res.text}")
                    return False
        else:
            st.warning(f"File not found: {file_path}")

    # Step 4: Attach files to challenge
    for file_id in uploaded_file_ids:
        attach_res = requests.post(
            f"{CTFD_URL}/api/v1/challenges/{cid}/files",
            headers=HEADERS,
            json={"file_id": file_id}
        )
        if attach_res.status_code != 200:
            st.error(f"Failed to link file ID {file_id} to challenge: {attach_res.text}")
            return False

    return flag_res.status_code == 200


# Streamlit UI
st.title("CTF Challenge Generator & Uploader")

with st.expander("Challenge Details", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        challenge_name = st.text_input("Challenge Name", "Dynamic Challenge")
        category = st.selectbox("Category", ["Cryptography", "Web Exploitation"])
    with col2:
        description = st.text_area("Description", "Solve this challenge!")
        flag = st.text_input("Flag", "KPMG_CTF{dynamic_flag}")
        value = st.number_input("Points", min_value=10, value=100, step=10)

uploaded_files = st.file_uploader("Upload required files", accept_multiple_files=True)

if uploaded_files:
    file_dict = {f.name: f.getvalue().decode() for f in uploaded_files}
    difficulties = ["Easy", "Medium", "Hard"]

    if st.button("Generate & Upload Challenges"):
        with st.spinner("Processing..."):
            for diff in difficulties:
                if category == "Cryptography":
                    file_content = next(iter(file_dict.values()))
                    modified = generate_crypto_challenge(file_content, diff)
                    fname = f"{diff.lower()}_crypto.txt"
                    Path(fname).write_text(modified)
                    match = re.search(r"KPMG_CTF\{.*?\}", file_content)
                    final_flag = match.group(0) if match else flag
                    upload_to_ctfd_crypto(challenge_name, category, description, value + 50 * difficulties.index(diff), final_flag, diff, modified)

                elif category == "Web Exploitation":
                    dockerfile = file_dict.get("Dockerfile", "")
                    index_php = file_dict.get("index.php", "")
                    flag_txt = file_dict.get("flag.txt", flag)
                    generated = generate_web_challenge(index_php, dockerfile, flag_txt, diff)
                    d_content, i_content, f_content = parse_generated_files(generated)
                    save_path = save_generated_files(diff, d_content, i_content, f_content, "generated_web")
                    url = run_docker_container(str(save_path), diff)
                    upload_to_ctfd_web(challenge_name, category, description, value + 50 * difficulties.index(diff), f_content, url, diff)

        st.success("All challenges processed and uploaded!")
