from flask import (
    Flask, g, render_template, redirect, url_for, request, flash,
    session
)
import hashlib
import sqlite3
import os
import re
from functools import wraps
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = "create-your-own"

# Database setup
def get_db():
    if 'db' not in g:
        db_path = os.path.join(os.path.dirname(__file__), 'database', 'database.sqlite')
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        cursor = g.db.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user';")
        if not cursor.fetchone():
            with open('CaseCompetition/database/schema.sql') as f:
                cursor.executescript(f.read())

        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'first_name' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN first_name TEXT")
        if 'last_name' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN last_name TEXT")
        if 'email' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN email TEXT")
        if 'account_name' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN account_name TEXT")

        g.db.commit()

    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Login required decorator
def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

# Before request: load user into global context
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        db = get_db()
        g.user = db.execute('SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()

app.before_request(load_logged_in_user)

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about_us.html')

@app.route('/how_to_donate')
def donate():
    return render_template('how_to_donate.html')

@app.route('/rewards')
@login_required
def rewards():
    return render_template('rewards.html')

@app.route('/profile/settings', methods=['GET', 'POST'])
@login_required
def profile_settings():
    db = get_db()
    user_id = session.get('user_id')

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        account_name = request.form['account_name']

        db.execute("UPDATE user SET first_name=?, last_name=?, email=?, account_name=? WHERE id=?",
                   (first_name, last_name, email, account_name, user_id))
        db.commit()
        flash('Profile updated successfully.')
        return redirect(url_for('profile_settings'))

    user = db.execute("SELECT * FROM user WHERE id=?", (user_id,)).fetchone()
    return render_template('profile_settings.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        db = get_db()
        user = db.execute("SELECT * FROM user WHERE username=?", (request.form['username'],)).fetchone()

        if user is None:
            flash('User not found.')
            return render_template('login.html')

        hashed_password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        if hashed_password != user['password']:
            flash('Invalid password.')
            return render_template('login.html')

        session.clear()
        session['user_id'] = user['id']
        flash('You were logged in.')
        return redirect(url_for('home'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You were logged out.')
    return redirect(url_for('home'))

@app.route('/register', methods=['POST', 'GET'])
def register():
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        db = get_db()
        username = request.form['username']

        if len(username) > 10:
            flash("Your username is too long, please try again")
            return render_template('register.html')

        if db.execute("SELECT * FROM user WHERE username=?", (username,)).fetchone():
            flash(f"Username '{username}' already taken", 'error')
            return render_template('register.html')

        if request.form['password1'] != request.form['password2']:
            flash("Passwords do not match, try again.", 'error')
            return render_template('register.html')

        hashed_password = hashlib.sha256(request.form['password1'].encode()).hexdigest()
        db.execute("INSERT INTO user (username, password) VALUES (?, ?)", (username, hashed_password))
        db.commit()

        flash(f"User '{username}' registered, you can now log in.", 'info')
        return redirect(url_for('login'))

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
