from flask import render_template, request, Flask
from app import app
from app.db import db
from sqlalchemy import text

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
