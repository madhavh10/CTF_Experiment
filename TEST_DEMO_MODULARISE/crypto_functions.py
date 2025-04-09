import re
import streamlit as st

def extract_flag(file_content, default_flag):
    """Extracts flag in KPMG_CTF{...} format from the original file."""
    match = re.search(r"KPMG_CTF\{.*?\}", file_content)
    return match.group(0) if match else default_flag

def get_crypto_prompt(file_content, difficulty):
    """Generates a Gemini prompt for cryptographic challenge creation."""
    base_prompt = (
        f"Create three different encrypted versions of this CTF flag using different encryption methods (easy, medium, hard). "
        f"All must decode to the original flag.\n\n"
        "Easy: Use a simple cipher (e.g., Base64, ROT13, Caesar shift).\n"
        "Medium: Use a slightly more complex method (e.g., XOR with a short key, AES-128 with a known key, Vigenère cipher).\n"
        "Hard: Use a strong method (e.g., AES-256 with unknown key, RSA with small primes, or a multi-step cipher chain).\n\n"
        "Provide the encrypted outputs and necessary hints (without giving away the solution).\n\n"
        f"Original Flag:\n{file_content}\n\n"
        f"Generate the '{difficulty}' version only."
    )
    return base_prompt

def process_crypto_challenges(file_content, filename, challenge_name, category, description, flag, value, model, upload_fn):
    difficulties = ["Easy", "Medium", "Hard"]
    extracted_flag = extract_flag(file_content, flag)

    for diff in difficulties:
        prompt = get_crypto_prompt(extracted_flag, diff)

        try:
            response = model.generate_content(prompt)
            modified_content = response.text.strip()
        except Exception as e:
            st.error(f"AI generation failed for {diff}: {e}")
            continue

        upload_fn(
            challenge_name=f"{challenge_name} - {diff}",
            category=category,
            description=f"{description}\n\n{modified_content}",
            value=value + difficulties.index(diff) * 50,
            flag=extracted_flag,
            challenge_url=None,
            difficulty=diff,
        )

        st.success(f"{diff} Crypto Challenge generated and uploaded.")

