from flask import render_template, request, Flask
from app import app
from app.db import db


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Vulnerable SQL query (SQLi)
        query = f"SELECT * FROM user WHERE username = '{username}' AND password = '{password}'"
        result = db.engine.execute(query).fetchone()

        if result:
            return f'Welcome {result.username}'
        else:
            return 'Invalid credentials'
        
    return render_template('index.html')