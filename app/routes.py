from flask import render_template, request, jsonify
from app import app
from app.db import db
from sqlalchemy import text
import os
import magic

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None  # Initialize result to None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Vulnerable SQL query (SQLi)
        query = f"SELECT * FROM user WHERE username = '{username}' AND password = '{password}'"

        # Use session.execute() with text() to run the query
        try:
            result = db.session.execute(text(query)).fetchall()  # Get all results

            # Format the result for display
            formatted_result = [f"<User {row.username}>" for row in result]

            if not formatted_result:
                result = 'Invalid credentials or no users found.'
        except Exception as e:
            result = f'Error: {str(e)}'

    return render_template('index.html', result=result)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if the request contains a file
        print(request.files)
        if 'uploaded_file' not in request.files:
            return jsonify({'error': 'No file part.'}), 400
        
        file = request.files['uploaded_file']
        
        # If no file was selected
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        # Temporarly upload file
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        
        # Check MIME type
        mime = magic.Magic()
        mime_type = mime.from_file(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))  # Read the first 1024 bytes for MIME type detection
        print(mime_type)

        # Allow only specific MIME types
        if mime_type.startswith('JPEG') or mime_type.startswith('PNG'):
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
            return jsonify({'success': f'File {file.filename} successfully uploaded!'}), 200
        else:
            return jsonify({'error': 'Invalid file type. Only .png, .jpg, and .img are allowed.'}), 400
    
    # For GET requests, render the file upload form
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)