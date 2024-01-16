from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('websites.db')
    conn.row_factory = sqlite3.Row
    return conn

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

if __name__ == '__main__':
    app.run(debug=True)
