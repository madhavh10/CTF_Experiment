import streamlit as st
import google.generativeai as genai  # Corrected import
import os

# Set up Gemini API Key
API_KEY = "AIzaSyBvcIqqahMhT76SWyUKfOkQcIz7U9uoE4A"
genai.configure(api_key=API_KEY)

def generate_challenge(file_content, difficulty):
    prompt = (
        f"Create three different encrypted versions of this CTF flag using different encryption methods (easy, medium, hard). All must decode to the original flag\n\n"
        "Easy: Use a simple cipher (e.g., Base64, ROT13, Caesar shift).\n\n"
        "Medium: Apply a slightly more complex method (e.g., XOR with a short key, AES-128 with a known key, Vigenère cipher).\n\n"
        "Hard: Use a strong encryption method (e.g., AES-256 with an unknown key that must be brute-forced, RSA with small primes, or a multi-step cipher chain).\n\n"
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

st.title("CTF Challenge Modulator")
st.write("Upload a challenge file, and get three modulated versions with different difficulty levels.")

uploaded_file = st.file_uploader("Upload your challenge file", type=["py", "txt"])

if uploaded_file is not None:
    file_content = uploaded_file.getvalue().decode("utf-8")

    st.subheader("Original Challenge File:")
    st.code(file_content, language='python')

    st.subheader("Generating Modulated Challenges...")

    easy_challenge = generate_challenge(file_content, "Easy")
    medium_challenge = generate_challenge(file_content, "Medium")
    hard_challenge = generate_challenge(file_content, "Hard")

    st.subheader("Easy Challenge:")
    st.code(easy_challenge, language='python')

    st.subheader("Medium Challenge:")
    st.code(medium_challenge, language='python')

    st.subheader("Hard Challenge:")
    st.code(hard_challenge, language='python')
    
    st.success("Challenges generated successfully!")
