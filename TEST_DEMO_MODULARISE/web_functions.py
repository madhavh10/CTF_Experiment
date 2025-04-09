import os
import subprocess
import re

PORT_MAP = {"Easy": 8081, "Medium": 8082, "Hard": 8083}


def parse_gemini_output(response_text):
    php_code = re.search(r"===BEGIN PHP===\s*(.*?)\s*===END PHP===", response_text, re.DOTALL).group(1)
    dockerfile = re.search(r"===BEGIN DOCKERFILE===\s*(.*?)\s*===END DOCKERFILE===", response_text, re.DOTALL).group(1)
    flag_text = re.search(r"===BEGIN FLAG===\s*(.*?)\s*===END FLAG===", response_text, re.DOTALL).group(1)
    return php_code, dockerfile, flag_text


def create_and_run_docker_script(folder, difficulty):
    port = PORT_MAP[difficulty]
    image_tag = f"{difficulty.lower()}_ctf"

    script_path = os.path.join(folder, "run_docker.bat")
    with open(script_path, "w") as f:
        f.write(f"@echo off\n")
        f.write(f"cd /d {os.path.abspath(folder)}\n")
        f.write(f"docker build -t {image_tag} .\n")
        f.write(f"docker run -d -p {port}:80 --rm --name {image_tag}_container {image_tag}\n")
    
    # Run the .bat script
    subprocess.run(script_path, shell=True)


def process_web_challenges(file_content, filename, challenge_name, category, description, flag, value, model, upload_to_ctfd):
    for difficulty in ["Easy", "Medium", "Hard"]:
        prompt = f"""
You are a CTF challenge creator. Modify the following vulnerable PHP code into a {difficulty.lower()} level web challenge.

⚠️ Requirements:
- Keep the vulnerability exploitable.
- Do not rename functions or variables unnecessarily.
- Add obfuscation or complexity as needed for {difficulty} level.
- The flag is: {flag}
- Store the flag in a file named 'flag.txt' and access it via PHP.
- Return:
  1. Modified PHP
  2. Dockerfile
  3. flag.txt

Format:
===BEGIN PHP===
<?php ... ?>
===END PHP===

===BEGIN DOCKERFILE===
FROM php:8.2-apache
COPY index.php /var/www/html/index.php
COPY flag.txt /flag.txt
EXPOSE 80
===END DOCKERFILE===

===BEGIN FLAG===
{flag}
===END FLAG===

Original PHP:
{file_content}
"""

        response = model.generate_content(prompt)
        php_code, dockerfile, flag_text = parse_gemini_output(response.text)

        # Save to docker/<difficulty>/
        folder = os.path.join("docker", difficulty.lower())
        os.makedirs(folder, exist_ok=True)

        with open(os.path.join(folder, "index.php"), "w", encoding="utf-8") as f:
            f.write(php_code)
        with open(os.path.join(folder, "Dockerfile"), "w", encoding="utf-8") as f:
            f.write(dockerfile)
        with open(os.path.join(folder, "flag.txt"), "w", encoding="utf-8") as f:
            f.write(flag_text)

        # Build and run via .bat script
        create_and_run_docker_script(folder, difficulty)

        # Generate URL
        url = f"http://localhost:{PORT_MAP[difficulty]}"

        # Upload to CTFd
        upload_to_ctfd(challenge_name, category, description, value, flag, url, difficulty)
