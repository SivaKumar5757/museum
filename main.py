from flask import Flask, render_template, redirect, url_for, flash, session, request, jsonify ,make_response
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo
from sqlalchemy import or_
import coursedata
from chatbot import get_response
from chatbot import plac
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import io
app = Flask(__name__)
app.config['SECRET_KEY'] = 't\(,$}K*4;pXmxdL:3wyS^hd<g0$a`Os'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
db = SQLAlchemy(app)
# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(80), nullable=False)

# Define the RegistrationForm
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

# Define the LoginForm
class LoginForm(FlaskForm):
    email_or_username = StringField('Email or Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

# Routes
@app.route("/")
def startup():
    return redirect(url_for('guest'))

@app.route("/home")
def guest():
    session['logged_in'] = False
    return render_template("guest.html", categories=coursedata.categories, courses=coursedata.courses)
@app.route("/user")
def user():
    return render_template("home.html", categories=coursedata.categories, courses=coursedata.courses)

@app.route('/user/chat/<path:bot>')
def index(bot):
    initial_message = "I'm here to explain any learning related queries and make your life shine."
    if session.get('logged_in'):
        username = session.get('username', 'there')
        initial_message = f"Hello {username}, {initial_message}"
    return render_template('index.html', initial_message=initial_message)

@app.route('/user/chat/<path:bot>', methods=['POST'])
def chat(bot):
    user_message = request.json.get('message')
    if user_message:
        response = get_response(user_message)
        return jsonify({'response': response[0],'link':response[1]})
    else:
        return jsonify({'response': 'Please provide a valid message.'}), 400

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            return redirect(url_for('register'))
        else:
            user = User(username=form.username.data, email=form.email.data, password=form.password.data)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('user'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(or_(User.email == form.email_or_username.data, User.username == form.email_or_username.data)).first()
        if user and user.password == form.password.data:
            session['logged_in'] = True
            session['username'] = user.username
            return redirect(url_for('user'))
        else:
            return redirect(url_for('login'))
    return render_template('login.html', form=form)
@app.route("/user/bookticket/<path:subpath>")
def bookticket(subpath):

    return render_template("ticket.html", subpath=subpath,mus=subpath.split(",")[1],pl=plac[subpath])

@app.route("/user/bookticket/payment/<path:subpath>")
def payment(subpath):
    return render_template("payment.html", subpath=subpath)
name = ""
quantity = ""
mobile = ""
email = ""
museum_name = ""

@app.route("/user/bookticket/payment/<path:subpath>/done", methods=['POST'])
def done(subpath):
    global name,quantity,mobile,museum_name,email
    name = request.form['name'].title()
    quantity = request.form['quantity'].title()
    mobile = request.form['mobile'].title()
    email = request.form['email']
    museum_name=subpath
    # print(name,quan,mob,email)
    return render_template("done.html", subpath=subpath)

@app.route('/download_ticket')
def download_ticket():

    ticket_price = 100 
    total_price = ticket_price * int(quantity)

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 20)
    p.drawString(1 * inch, height - 1.5 * inch, f"{museum_name} Ticket")
    
    p.setFont("Helvetica", 12)
    p.drawString(1 * inch, height - 2 * inch, f"Name: {name}")
    p.drawString(1 * inch, height - 2.3 * inch, f"Quantity of Tickets: {quantity}")
    p.drawString(1 * inch, height - 2.6 * inch, f"Mobile Number: {mobile}")
    p.drawString(1 * inch, height - 2.9 * inch, f"Email: {email}")

    p.setFont("Helvetica-Bold", 12)
    p.drawString(1 * inch, height - 3.7 * inch, f"Ticket Price: Rs {ticket_price} per ticket")
    p.drawString(1 * inch, height - 4 * inch, f"Total Price: Rs {total_price}")

    p.setFont("Helvetica-Oblique", 10)
    p.drawString(1 * inch, height - 4.5 * inch, "Thank you for your purchase!")
    p.drawString(1 * inch, height - 4.8 * inch, "Please carry this ticket with you to the museum.")
    p.drawString(1 * inch, height - 6 * inch, "Made by Code Alchemist")


    p.showPage()
    p.save()

    pdf = buffer.getvalue()
    buffer.close()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=Museum_Ticket.pdf'

    return response



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
