from app import app
from app.models import User, db
import subprocess
import time

if __name__ == "__main__":
    # Command to run the PHP server in the background
    command = ['sudo', 'php', '-S', 'localhost:8000']

    # Run the PHP server in the background
    subprocess.Popen(command)

    # Give the PHP server some time to start
    time.sleep(5)

    # Run the Flask app
    app.run(debug=True)