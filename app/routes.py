from flask import render_template, request, Flask

from app import app


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get the text from the 'test' input box
        input_text = request.form.get('test')
        print(f"Text from input box: {input_text}")  # This prints to the server console
        
    return render_template('index.html')