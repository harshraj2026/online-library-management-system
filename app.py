from flask import Flask, render_template, request, redirect, session
import mysql.connector
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "library_secret"


# Database Connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="@Harsh1608",
    database="library_db"
)

cursor = db.cursor(dictionary=True)

# Login Page
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user['user_id']
            session['role'] = user['role']
            session['name'] = user['name']
            return redirect('/dashboard')
        else:
            return "Invalid Credentials"

    return render_template('login.html')


# Dashboard
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', name=session['name'], role=session['role'])


# Search Book
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        keyword = request.form['keyword']
        cursor.execute("SELECT * FROM books WHERE title LIKE %s", ('%' + keyword + '%',))
        books = cursor.fetchall()
        return render_template('search.html', books=books)

    return render_template('search.html', books=None)


# Issue Book
@app.route('/issue/<int:book_id>')
def issue(book_id):
    cursor.execute("SELECT * FROM books WHERE book_id=%s", (book_id,))
    book = cursor.fetchone()

    if book['status'] == "Available":
        issue_date = datetime.now().date()
        due_date = issue_date + timedelta(days=14)

        cursor.execute("""
            INSERT INTO transactions (user_id, book_id, issue_date, due_date)
            VALUES (%s, %s, %s, %s)
        """, (session['user_id'], book_id, issue_date, due_date))

        cursor.execute("UPDATE books SET status='Not Available' WHERE book_id=%s", (book_id,))
        db.commit()

        return "Book Issued Successfully"
    else:
        return "Book Not Available"


# Return Book
@app.route('/return/<int:book_id>')
def return_book(book_id):
    today = datetime.now().date()

    cursor.execute("""
        SELECT * FROM transactions 
        WHERE book_id=%s AND return_date IS NULL
    """, (book_id,))
    transaction = cursor.fetchone()

    due_date = transaction['due_date']
    fine = 0

    if today > due_date:
        late_days = (today - due_date).days
        fine = late_days * 5

    cursor.execute("""
        UPDATE transactions 
        SET return_date=%s, fine=%s 
        WHERE transaction_id=%s
    """, (today, fine, transaction['transaction_id']))

    cursor.execute("UPDATE books SET status='Available' WHERE book_id=%s", (book_id,))
    db.commit()

    return f"Book Returned. Fine: ₹{fine}"


if __name__ == "__main__":
    app.run(debug=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

