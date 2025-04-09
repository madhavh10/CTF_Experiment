from flask import Flask, request, render_template_string
import sqlite3

app = Flask(__name__)

# Setup database
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)")
    cursor.execute("INSERT INTO users (username, password) VALUES ('admin', 'supersecret')")
    conn.commit()
    conn.close()

init_db()

# Vulnerable login endpoint
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        # ❌ SQL Injection vulnerability here!
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        print("[DEBUG] Executing Query:", query)  # To see attempted injections in logs

        cursor.execute(query)
        user = cursor.fetchone()
        conn.close()

        if user:
            return "<h2>Login Successful! Welcome, " + username + "!</h2>"
        else:
            return "<h2>Login Failed! Try again.</h2>"

    return render_template_string("""
        <h1>Login</h1>
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    """)

if __name__ == "__main__":
    app.run(debug=True)
