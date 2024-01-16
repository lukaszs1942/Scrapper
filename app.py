from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime

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
    row1 = conn.execute('SELECT content FROM website_versions WHERE id = ?', (id1,)).fetchone()
    row2 = conn.execute('SELECT content FROM website_versions WHERE id = ?', (id2,)).fetchone()
    conn.close()

    # Check if rows exist and have content
    if row1 is None or row2 is None or row1['content'] is None or row2['content'] is None:
        return "One or both of the specified records do not exist or have no content."

    # Extract content from the rows
    content1 = row1['content']
    content2 = row2['content']

    diff = difflib.ndiff(content1.splitlines(), content2.splitlines())
    return render_template('diff.html', diff=diff)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_url(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM website_versions WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route('/scrape_and_save', methods=['POST'])
def scrape_and_save():
    url_to_scrape = request.form.get('url_to_scrape')

    # Fetch the webpage content
    response = requests.get(url_to_scrape)
    soup = BeautifulSoup(response.content, 'html.parser')
    scraped_content = soup.prettify()

    # Save to database
    conn = get_db_connection()
    conn.execute('INSERT INTO website_versions (url, content, timestamp) VALUES (?, ?, ?)', 
                 (url_to_scrape, scraped_content, datetime.now()))  # Correct usage
    conn.commit()
    conn.close()

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
