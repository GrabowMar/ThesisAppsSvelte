import os
from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "Backend running on port 5007"

@app.route("/health")
def health():
    return "healthy"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5007))
    app.run(host="0.0.0.0", port=port)