import sqlite3
from enum import Enum

from flask import (Flask, render_template, request, session, g, redirect, flash, url_for, abort, jsonify)

#configuration
DATABASE = 'flaskr.db'
USERNAME = 'admin'
PASSWORD = 'admin'
SECRET_KEY = 'change_me'

app = Flask(__name__)

# load the config
app.config.from_object(__name__)

class Status(Enum):
   Failure=0
   Success=1


def connect_db():
    """Connects to the database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
   """Open database connection"""
   if not hasattr(g, 'sqlite_db'):
       g.sqlite_db = connect_db()
   return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/')
def index():
    """Searches the database for entries, then displays them."""
    db = get_db()
    cur = db.execute('select * from entries order by id desc')
    entries = cur.fetchall()
    return render_template('index.html', entries=entries)

@app.route('/login', methods=['GET', 'POST'])
def login():
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
def logout():
    """User logout/authentication/session management"""
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
def add_entry():
    """Adds a new post to the database."""
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute(
        'insert into entries (title ,text) values (?, ?)',
        [request.form['title'], request.form['text']]
    )
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('index'))

@app.route('/delete/<post_id>', methods=['GET'])
def delete_entry(post_id):
    """Deletes a post from the database"""
    try:
        db = get_db()
        db.execute(f'delete from entries where id={post_id}')
        db.commit()
        result = {'status': Status.Success.value, 'message': 'Post Deleted'}
    except Exception as e:
        result = {'status': Status.Failure.value, 'message': repr(e)}
    return jsonify(result)



if __name__ == '__main__':
    app.run()
