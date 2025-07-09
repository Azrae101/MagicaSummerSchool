from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about_us.html')

@app.route('/how_to_donate')
def donate():
    return render_template('how_to_donate.html')

if __name__ == '__main__':
    app.run(debug=False)  # Change to False for production