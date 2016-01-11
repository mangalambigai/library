from datetime import date, timedelta
from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
app = Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Student, Book, Checkout

from flask import session as login_session
import random, string

# Imports for OAUTH
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "library Application"

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        print request.args.get('state')
        print login_session['state']
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/'
        return response
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

#Connect to Database and create database session
engine = create_engine('sqlite:///library.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()



#CRUD for books
@app.route('/')
@app.route('/book/')
def showBooks():
    books = session.query(Book).order_by(asc(Book.name))
    return render_template('books.html', books=books, username = login_session['username'])

@app.route('/book/new/', methods=['GET', 'POST'])
def newBook():
    if request.method == 'POST':
        newBook = Book(name=request.form['name'], author = request.form['author'], subject = request.form['subject'])
        session.add(newBook)
        session.commit()
        return redirect(url_for('showBooks'))
    else:
        return render_template('newbook.html', username = login_session['username'])

@app.route('/book/<int:book_id>/')
def showBook(book_id):
    return 'details of book '+book_id

@app.route('/book/<int:book_id>/edit/', methods=['GET', 'POST'])
def editBook(book_id):
    book = session.query(Book).filter_by(id=book_id).one()
    if request.method == 'POST':
        book.name = request.form['name']
        book.author = request.form['author']
        book.subject = request.form['subject']
        session.add(book)
        session.commit()
        return redirect(url_for('showBooks'))
    else:
        return render_template('editbook.html', book_id = book_id, book=book, username = login_session['username'])

@app.route('/book/<int:book_id>/delete/', methods=['GET', 'POST'])
def deleteBook(book_id):
    book = session.query(Book).filter_by(id = book_id).one()
    if request.method == 'POST':
        session.delete(book)
        session.commit()
        return redirect(url_for('showBooks'))
    else:
        return render_template('deleteBook.html', book_id = book_id, book=book, username = login_session['username'])

#CRUD for students
@app.route('/student/')
def showStudents():
    students = session.query(Student).order_by(asc(Student.name))
    return render_template('students.html', students=students, username = login_session['username'])

@app.route('/student/new/', methods=['POST', 'GET'])
def newStudent():
    if request.method == 'POST':
        newStudent = Student(name=request.form['name'], email = request.form['email'], cellphone = request.form['cellphone'])
        session.add(newStudent)
        session.commit()
        return redirect(url_for('showStudents'))
    else:
        return render_template('newstudent.html', username = login_session['username'])

@app.route('/student/<int:student_id>/')
def showStudent(student_id):
    student = session.query(Student).filter_by(id= student_id).one()
    checkouts = session.query(Checkout).filter_by(student_id = student_id).all()
    return render_template('student.html', student_id = student_id, student=student, checkouts = checkouts, username = login_session['username'])

@app.route('/student/<int:student_id>/edit/', methods=['POST', 'GET'])
def editStudent(student_id):
    student = session.query(Student).filter_by(id=student_id).one()
    if request.method == 'POST':
        student.name = request.form['name']
        student.email = request.form['email']
        student.cellphone = request.form['cellphone']
        session.add(student)
        session.commit()
        return redirect(url_for('showStudents'))
    else:
        return render_template('editstudent.html', student_id = student_id, student=student, username = login_session['username'])

@app.route('/student/<int:student_id>/delete/', methods=['POST', 'GET'])
def deleteStudent(student_id):
    student = session.query(Student).filter_by(id=student_id).one()
    if request.method == 'POST':
        session.delete(student)
        session.commit()
        return redirect(url_for('showStudents'))
    else:
        return render_template('deletestudent.html', student_id = student_id, student=student, username = login_session['username'])

#Checkouts
@app.route('/checkout/list/')
def showCheckouts():
    checkouts = session.query(Checkout, Student, Book).join(Book).join(Student).all()
    return render_template('viewcheckouts.html', checkouts = checkouts, username = login_session['username'])

@app.route('/checkout/<int:student_id>/')
def checkout(student_id):
    student = session.query(Student).filter_by(id = student_id).one()
#TODO: list only not checked out books

    books = session.query(Book).all()
    checkouts = session.query(Book, Checkout).join(Checkout).filter_by(student_id = student_id).all()

    return render_template('checkout.html', checkouts = checkouts, student_id = student_id, student = student, books = books, username = login_session['username'])

@app.route('/checkout/<int:student_id>/<int:book_id>', methods=['POST'])
def checkoutBook(student_id, book_id):
    today = date.today()
    due_date = today + timedelta(days = 28)
    newCheckout = Checkout(
        student_id = student_id,
        book_id = book_id,
        checkout_date = today,
        due_date = due_date)
    session.add(newCheckout)
    session.commit()
    return redirect(url_for('checkout', student_id = student_id))

@app.route('/returnbook/<int:book_id>', methods=['POST'])
def returnBook(book_id):
    checkout = session.query(Checkout).filter_by(book_id = book_id).one()
    session.delete(checkout)
    session.commit()
    return redirect(url_for('showCheckouts'))

#TODO: renew
#@app.route('/checkout/<int:checkout_id>/renew')
#def renewCheckout(checkout_id):
#    return 'renew a checkout'
#TODO: place hold
#@app.route('/placehold/')
#def placeHold():
#    return 'place a hold'

if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 5000)
