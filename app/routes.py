from flask import render_template, request, jsonify, send_from_directory, flash, redirect, url_for
from flask_socketio import SocketIO, emit
from app import app
from app.db import db
from sqlalchemy import text
import os
import magic
import requests
import time
import subprocess
import threading

socketio = SocketIO(app, async_mode='threading')

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None  # Initialize result to None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Vulnerable SQL query (SQLi)
        query = f"SELECT * FROM user WHERE username = '{username}'"

        # Use session.execute() with text() to run the query
        try:
            user_result = db.session.execute(text(query)).fetchall()  # Get all results

            if len(user_result) == 0:
                result = f"No such username {user_result} found!"
            elif len(user_result) > 1:
                result = f"Multiple users {user_result} grabbed. Bailing out."
            elif user_result:
                # Sequential password checking
                _, _, stored_password = user_result[0]  # Assume only one user for simplicity
                print(f"DB password is: {stored_password}")
                print(f"recieved password is: {password}")
                for i in range(len(stored_password)):
                    if stored_password[i] == password[i]:
                        print("so good so far")
                        time.sleep(0.0005)
                    else:
                        print(f"characters do not match!: {stored_password[i]}  {password[i]}")
                        result = 'Invalid password.'
                        break
                result = f"Logged in! Welcome {username}"
            else:
                result = f'Invalid credentials or no username found.'
        except Exception as e:
            result = f'Error: {str(e)}'

    return render_template('index.html', result=result)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/upload/', defaults={'filename': None}, methods=['GET', 'POST'])
@app.route('/upload/<filename>', methods=['GET', 'POST'])
def upload_file(filename):
    global upload_counter, upload_queue
    if request.method == 'POST':
        # Check if the request contains a file
        print(request.files)
        if 'uploaded_file' not in request.files:
            return jsonify({'error': 'No file part.'}), 400

        file = request.files['uploaded_file']

        # If no file was selected
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Temporarily upload file
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Check MIME type
        mime = magic.Magic()
        mime_type = mime.from_file(file_path)  # Read the first 1024 bytes for MIME type detection
        print(f"MIME TYPE: {mime_type}")

        # Allow only specific MIME types
        if mime_type.startswith('JPEG') or mime_type.startswith('PNG'):
            handle_upload()
            return jsonify({'success': f'File {file.filename} successfully uploaded! {upload_queue} files in queue.'}), 200
        else:
            os.remove(file_path)
            return jsonify({'error': 'Invalid MIME FILE type. Only .png and .jpg are allowed.'}), 400

    # Handle GET requests to retrieve a specific file
    if filename:
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
            if filename.endswith('.php'):
                # Send the PHP file to the PHP server and get the result
                try:
                    with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'rb') as f:
                        php_code = f.read()
                    response = requests.post(f'http://localhost:8000/uploads/{filename}', data=php_code)

                    return jsonify({"text":response.text, "status":response.status_code}), 200
                except Exception as e:
                    return jsonify({'error': str(e)}), 500

            # If it's not a PHP file, just send it normally
            return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
        else:
            return jsonify({'error': 'File not found.'}), 404

    # For GET requests without a filename, reject access attempt.
    return jsonify({'access': 'Access Denied!'}), 403

#NFS Stuff here

BACKUP_SERVER = '127.0.0.1'
BACKUP_OPEN = 10
EXTEND_TIME_PER_FILE = 10
upload_counter = 0
backup_active = False
upload_queue = 0
time_remaining = 0
countdown_thread = None

def start_backup():
    """Start the NFS server and initiate the countdown."""
    global backup_active, time_remaining, countdown_thread

    backup_active = True
    print("Starting NFS server and exposing /uploads/")
    file_path = os.path.join(app.config['UPLOAD_FOLDER'])
    subprocess.run(["sudo", "exportfs", "-o", "rw,sync,no_subtree_check,no_root_squash", f"*:{file_path}"])

    if time_remaining <= 0:
        time_remaining = BACKUP_OPEN + (upload_queue * EXTEND_TIME_PER_FILE)

    socketio.emit('backup_status', {'message': f"Backup started. Time until close: {time_remaining} seconds."})

    if not countdown_thread or not countdown_thread.is_alive():
        countdown_thread = threading.Thread(target=emit_countdown)
        countdown_thread.start()

def emit_countdown():
    """Emit countdown updates to the client every second."""
    global time_remaining, backup_active

    while time_remaining > 0 and backup_active:
        time.sleep(1)
        time_remaining -= 1
        socketio.emit('countdown', {'time_remaining': time_remaining})

    if time_remaining <= 0 and backup_active:
        stop_backup()

def stop_backup():
    """Stop the backup/NFS server."""
    global backup_active, upload_queue, time_remaining

    backup_active = False
    upload_queue = 0  # Reset the upload queue
    time_remaining = 0  # Reset the time remaining
    print("Stopping NFS server")
    file_path = os.path.join(app.config['UPLOAD_FOLDER'])
    subprocess.run(["sudo", "exportfs", "-u", f"*:{file_path}"])

    socketio.emit('backup_status', {'message': "Backup has finished. All safe!"})
    time.sleep(2)
    socketio.emit('backup_status', {'message': "Searching for Printers."})
    time.sleep(1)
    socketio.emit('backup_status', {'message': "Searching for Printers.."})
    time.sleep(1)
    socketio.emit('backup_status', {'message': "Searching for Printers..."})
    time.sleep(1)
    socketio.emit('backup_status', {'message': "Searching for Printers."})
    time.sleep(1)
    socketio.emit('backup_status', {'message': "Searching for Printers.."})
    time.sleep(1)
    socketio.emit('backup_status', {'message': "Searching for Printers..."})
    time.sleep(1)
    socketio.emit('backup_status', {'message': "1 Printer found. idkwid//Mr-Krabs_Printer."})
    time.sleep(1)
    socketio.emit('backup_status', {'message': "Sending Print."})
    time.sleep(1)
    socketio.emit('backup_status', {'message': "ERROR - DRIVER NOT FOUND"})


def handle_upload():
    """Handle the upload, increase the upload counter, and manage the backup server."""
    global upload_counter, upload_queue, time_remaining

    upload_counter += 1
    upload_queue += 1  # Increase the queue for each upload

    if upload_queue > BACKUP_OPEN:
        if not backup_active:
            start_backup()
        else:
            time_remaining += EXTEND_TIME_PER_FILE
            socketio.emit('backup_status', {'message': f"Backup already in-progress. Time until close extended: {time_remaining} seconds."})
    else:
        socketio.emit('backup_status', {'message': f"Upload queue: {upload_queue} files. I'll only start backing these up when I queue up {BACKUP_OPEN} files."})

if __name__ == '__main__':
    socketio.run(app, debug=True)