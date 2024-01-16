from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
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
def compare_contents(old_content, new_content):
    # Split the content into lines for comparison
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()

    # Compute the difference using difflib
    diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=''))

    # Join the diff lines to get the result as a string
    return '\n'.join(diff)

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

        # Perform the initial scrape of the website
        initial_content = scrape_website(url)

        # Store the initial content in the database
        conn = get_db_connection()
        conn.execute('INSERT INTO website_versions (url) VALUES (?)', (url,))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    return render_template('add.html')

@app.route('/show_diff')
def show_diff():
    id1 = request.args.get('id1')
    id2 = request.args.get('id2')
    
    # Fetch contents from the database
    conn = get_db_connection()
    content1 = conn.execute('SELECT content FROM website_versions WHERE id = ?', (id1,)).fetchone()
    content2 = conn.execute('SELECT content FROM website_versions WHERE id = ?', (id2,)).fetchone()
    conn.close()

    # Check if contents are available
    if not content1 or not content2:
        return "One or both of the contents are not available."

    # Compute the difference
    diff = list(ndiff(content1['content'].splitlines(), content2['content'].splitlines()))

    # Pass the diff to the template
    return render_template('diff.html', diff=diff)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_url(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM website_versions WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route('/rescrape/<int:url_id>', methods=['POST'])
def rescrape(url_id):

    # Fetch the URL from the database
    conn = get_db_connection()
    url_record = conn.execute('SELECT url FROM website_versions WHERE id = ?', (url_id,)).fetchone()

    if not url_record:
        conn.close()
        return "URL not found."

    # Perform the scraping
    new_content = scrape_website(url_record['url'])

    # Get the latest version's content from the database for comparison
    latest_content = conn.execute('SELECT content FROM website_versions WHERE url = ? ORDER BY timestamp DESC LIMIT 1', (url_record['url'],)).fetchone()

    # Compare and store the diff
    if latest_content:
        diff = compare_contents(latest_content['content'], new_content)
        # Store the diff and the new content in the database
        conn.execute('INSERT INTO website_versions (url, content, diff, timestamp) VALUES (?, ?, ?, ?)', 
                     (url_record['url'], new_content, diff, datetime.now()))
    else:
        # If no previous versions, just store the new content
        conn.execute('INSERT INTO website_versions (url, content, timestamp) VALUES (?, ?, ?)', 
                     (url_record['url'], new_content, datetime.now()))

    conn.commit()
    conn.close()

    # Redirect to a new page to show results
    return redirect(url_for('show_results', url_id=url_id))

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

def scrape_website(url):
    # Send a GET request to the URL
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code != 200:
        return "Failed to retrieve the webpage"

    # Parse the content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Return the prettified HTML content
    return soup.prettify()

@app.route('/show_results/<int:url_id>')
def show_results(url_id):
    # Fetch the URL from the database
    conn = get_db_connection()
    url_record = conn.execute('SELECT * FROM website_versions WHERE id = ?', (url_id,)).fetchone()

    if not url_record:
        conn.close()
        return "URL not found."

    # Fetch the latest version from the database
    latest_version = conn.execute('SELECT * FROM website_versions WHERE url = ? ORDER BY timestamp DESC LIMIT 1', (url_record['url'],)).fetchone()

    # Fetch all versions from the database
    versions = conn.execute('SELECT * FROM website_versions WHERE url = ? ORDER BY timestamp DESC', (url_record['url'],)).fetchall()

    conn.close()

    # Render the results template
    return render_template('results.html', url_record=url_record, latest_version=latest_version, versions=versions)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
