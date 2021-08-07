import json
import pytest
from pathlib import Path
from project.app import app, db, Status

TEST_DB = 'test.db'


@pytest.fixture
def client():
    BASE_DIR = Path(__file__).resolve().parent.parent
    app.config['TESTING'] = True
    app.config['DATABASE'] = BASE_DIR.joinpath(TEST_DB)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{BASE_DIR.joinpath(TEST_DB)}'

    db.create_all()  # setup
    yield app.test_client()  # tests run here
    db.drop_all()


def login(client, username, password):
    """Login helper function"""
    return client.post(
        '/login',
        data=dict(username=username, password=password),
        follow_redirects=True,
    )


def logout(client):
    """Logout helper function"""
    return client.get('/logout', follow_redirects=True)


def search(client, query):
    return client.get(
        '/search',
        data=dict(query=query),
        follow_redirects=True
    )


def add_entry(client, title, text):
    return client.post(
        '/add',
        data=dict(title=title, text=text),
        follow_redirects=True,
    )


def test_index(client):
    response = client.get('/', content_type='html/text')
    assert response.status_code == 200


def test_database(client):
    """Initial test, ensure that the database exists"""
    assert Path('flaskr.db').is_file()


def test_empty_db(client):
    """Ensure database is blank"""
    rv = client.get('/')
    assert b'No entries yet. Add some!' in rv.data


def test_login_logout(client):
    """Test login and logout using helper functions"""
    rv = login(client, app.config['USERNAME'], app.config['PASSWORD'])
    assert b'You were logged in' in rv.data
    rv = logout(client)
    assert b'You were logged out' in rv.data
    rv = login(client, app.config['USERNAME'] + 'x', app.config['PASSWORD'])
    assert b'Invalid username' in rv.data
    rv = login(client, app.config['USERNAME'], app.config['PASSWORD'] + 'x')
    assert b'Invalid password' in rv.data


def test_messages(client):
    """Ensure that user can post messages"""
    login(client, app.config['USERNAME'], app.config['PASSWORD'])
    rv = add_entry(client, '<Hello>', '<strong>HTML</strong> allowed here')
    assert b'No entries here so far' not in rv.data
    assert b'&lt;Hello&gt;' in rv.data
    assert b'<strong>HTML</strong> allowed here' in rv.data


def test_delete_message(client):
    """Ensure the messages are being deleted"""
    rv = client.get('/delete/1')
    data = json.loads(rv.data)
    assert data['status'] == Status.Success.value


def test_search(client):
    """Ensure that the search returns the correct entries"""
    test_titles = ['title1', 'title2', 'title3']
    test_texts = ['text1', 'text2', 'text3']
    for title, text in zip(test_titles, test_texts):
        add_entry(client, title, text)

    # Test empty query
    rv = search(client, query='')
    for title, text in zip(test_titles, test_texts):
        assert title in rv.data and text in rv.data

