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

socketio = SocketIO(app)

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

            try:
                if user_result[1]:
                    print("ha got in!")
                    result = 'Wow 2 users? I gotta bail hopefully nothing bad happens!<br>' + \
                             '<br>'.join(str(item) for item in user_result)
                    print(result)
                    return render_template('index.html', result=result)
            except:
                print("nothing bad here. ha")

            if user_result:
                # Sequential password checking
                _, _, stored_password = user_result[0]  # Assume only one user for simplicity
                for i in range(len(stored_password)):
                    time.sleep(0.05)  # Delay to simulate sequential checking
                    if stored_password[i] != password[i]:
                        result = 'Invalid password.'
            else:
                result = 'Invalid credentials or no users found.'
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
            return jsonify({'error': 'Invalid MIME FILE type. Only .png, .jpg, and .img are allowed.'}), 400

    # Handle GET requests to retrieve a specific file
    if filename:
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
            if filename.endswith('.php'):
                # Send the PHP file to the PHP server and get the result
                try:
                    with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'rb') as f:
                        php_code = f.read()
                    response = requests.post(f'http://localhost:8000/uploads/{filename}', data=php_code)

                    return response.text, response.status_code
                except Exception as e:
                    return jsonify({'error': str(e)}), 500

            # If it's not a PHP file, just send it normally
            return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
        else:
            return jsonify({'error': 'File not found.'}), 404

    # For GET requests without a filename, list uploaded files
    uploaded_files = os.listdir(app.config['UPLOAD_FOLDER'])
    if uploaded_files:
        return jsonify({'uploaded_files': uploaded_files}), 200
    else:
        return jsonify({'error': 'No files uploaded yet.'}), 404

#NFS Stuff here

BACKUP_SERVER = '127.0.0.1'
BACKUP_OPEN = 10
UPLOAD_THRESHOLD = 5
EXTEND_TIME_PER_FILE = 20
upload_counter = 0
backup_active = False
upload_queue = 0
timer = None


def start_backup():
    """Start the NFS server and initiate the countdown."""
    global backup_active, timer, upload_queue, time_remaining

    backup_active = True
    print("Starting NFS server and exposing /uploads/")
    file_path = os.path.join(app.config['UPLOAD_FOLDER'])
    subprocess.run(["sudo", "exportfs", "-o", "rw,sync,no_subtree_check,no_root_squash", f"*:{file_path}"])

    # Reset timer and calculate total time to close if it's a new start
    if time_remaining <= 0:
        time_remaining = BACKUP_OPEN + (upload_queue * EXTEND_TIME_PER_FILE)

    # Emit initial backup status
    socketio.emit('backup_status', {'message': f"Backup server started. Time until close: {time_remaining} seconds."})

    # Start a thread to emit countdown updates every second
    if timer:
        timer.cancel()  # Cancel the previous timer if it's still running
    timer = threading.Timer(time_remaining, stop_backup)
    timer.start()

    threading.Thread(target=emit_countdown).start()

def emit_countdown():
    """Emit countdown updates to the client every second."""
    global time_remaining
    while time_remaining > 0:
        time.sleep(1)
        time_remaining -= 1
        socketio.emit('countdown', {'time_remaining': time_remaining})

    if time_remaining <= 0:
        socketio.emit('countdown', {'time_remaining': 0})
        stop_backup()

def stop_backup():
    """Stop the backup/NFS server."""
    global backup_active, upload_queue

    backup_active = False
    upload_queue = 0  # Reset the upload queue
    print("Stopping NFS server")
    file_path = os.path.join(app.config['UPLOAD_FOLDER'])
    subprocess.run(["sudo", "exportfs", "-u", f"*:{file_path}"])

    # Emit a message to the client
    socketio.emit('backup_status', {'message': "Backup server stopped."})

def handle_upload():
    """Handle the upload, increase the upload counter, and manage the backup server."""
    global upload_counter, upload_queue, time_remaining

    upload_counter += 1
    upload_queue += 1

    if not backup_active:
        start_backup()
    else:
        time_remaining += EXTEND_TIME_PER_FILE
        flash(f"Backup is already active. Upload added, {upload_queue} files in the queue. Time extended by {EXTEND_TIME_PER_FILE} seconds.")
        socketio.emit('backup_status', {'message': f"Upload added. Time until close: {time_remaining} seconds."})

    flash(f"Upload threshold reached, lets sync them so we don't lose them! {upload_queue} files in the queue.")


def is_backup_active():
    """Check if the backup server (NFS) is currently active."""
    result = subprocess.run(['sudo', 'exportfs'], capture_output=True, text=True)
    return '/path/to/uploads' in result.stdout

if __name__ == '__main__':
    socketio.run(app, debug=True)