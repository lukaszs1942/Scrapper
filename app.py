from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import difflib

app = Flask(__name__)

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('websites.db')
    conn.row_factory = sqlite3.Row
    return conn

# Function to initialize the database
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS website_versions (
            id INTEGER PRIMARY KEY,
            url TEXT,
            content TEXT,
            timestamp DATETIME
        )
    ''')
    conn.commit()
    conn.close()

# Call init_db() to ensure the database and table are created
init_db()


@app.route('/')
def index():
    conn = get_db_connection()
    urls = conn.execute('SELECT * FROM website_versions').fetchall()
    conn.close()
    return render_template('index.html', urls=urls)

@app.route('/add', methods=('GET', 'POST'))
def add_url():
    if request.method == 'POST':
        url = request.form['url']
        conn = get_db_connection()
        conn.execute('INSERT INTO website_versions (url) VALUES (?)', (url,))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    return render_template('add.html')

@app.route('/diff/<int:id1>/<int:id2>')
def show_diff(id1, id2):
    conn = get_db_connection()
    content1 = conn.execute('SELECT content FROM website_versions WHERE id = ?', (id1,)).fetchone()
    content2 = conn.execute('SELECT content FROM website_versions WHERE id = ?', (id2,)).fetchone()
    conn.close()

    if not content1 or not content2:
        return "One or both of the specified records do not exist."

    diff = difflib.ndiff(content1['content'].splitlines(), content2['content'].splitlines())
    return render_template('diff.html', diff=diff)

if __name__ == '__main__':
    app.run(debug=True)
