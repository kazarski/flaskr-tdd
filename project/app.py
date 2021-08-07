import os
from enum import Enum
from pathlib import Path
from functools import wraps
from typing import Union

from flask import Flask, render_template, request, session, redirect, flash, url_for, jsonify, Response
from flask_sqlalchemy import SQLAlchemy

basedir = Path(__file__).resolve().parent.parent

# configuration
DATABASE = 'flaskr.db'
USERNAME = 'admin'
PASSWORD = 'admin'
SECRET_KEY = 'change_me'
SQLALCHEMY_DATABASE_URI = os.getenv(
    'DATABASE_URL',
    f'sqlite:///{Path(basedir).joinpath(DATABASE)}'
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Create and initialize a new Flask app
app = Flask(__name__)

# load the config
app.config.from_object(__name__)

# init sqlalchemy
db = SQLAlchemy(app)

from project import models


class Status(Enum):
    Failure = 0
    Success = 1


@app.route('/')
def index():
    """Searches the database for entries, then displays them."""
    entries = db.session.query(models.Post)
    return render_template('index.html', entries=entries)


@app.route('/login', methods=['GET', 'POST'])
def login() -> Union[Response, str]:
    """User login/authentication/session management."""
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('index'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout() -> Response:
    """User logout/authentication/session management"""
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('index'))


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please log in')
            return jsonify({'status': Status.Failure.value, 'message': 'Please log in'}), 401
        return f(*args, **kwargs)

    return decorated_function


@app.route('/add', methods=['POST'])
@login_required
def add_entry() -> Response:
    """Adds a new post to the database."""
    new_entry = models.Post(request.form['title'], request.form['text'])
    db.session.add(new_entry)
    db.session.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('index'))


@app.route('/delete/<post_id>', methods=['GET'])
@login_required
def delete_entry(post_id: int) -> Response:
    """Deletes a post from the database"""
    try:
        db.session.query(models.Post).filter_by(id=post_id).delete()
        db.session.commit()
        result = {'status': Status.Success.value, 'message': 'Post Deleted'}
    except Exception as e:
        result = {'status': Status.Failure.value, 'message': repr(e)}
    return jsonify(result)


@app.route('/search', methods=['GET'])
def search() -> str:
    query = request.args.get('query')
    entries = db.session.query(models.Post)
    if query:
        return render_template('search.html', entries=entries, query=query)
    return render_template('search.html')


if __name__ == '__main__':
    app.run()
