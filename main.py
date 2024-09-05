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
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

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
date=""
nationality=""


@app.route("/user/bookticket/payment/<path:subpath>/done", methods=['POST'])
def done(subpath):
    global name,quantity,mobile,museum_name,email,date,nationality
    name = request.form['name'].title()
    quantity = request.form['quantity'].title()
    mobile = request.form['mobile'].title()
    email = request.form['email']
    date = request.form['date']  # For the date of the ticket
    nationality = request.form['nationality'].title()  # For nationality selection

    museum_name=subpath
    # print(name,quan,mob,email)
    return render_template("done.html", subpath=subpath)

@app.route('/download_ticket')
def download_ticket():
    ticket_price = 100
    if nationality.lower() == "foreigner":
        ticket_price *= 0.5  # Apply 50% discount

    total_price = ticket_price * int(quantity)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()

    # Define custom styles
    title_style = ParagraphStyle(
        name="TitleStyle",
        fontSize=24,
        leading=28,
        alignment=1,  # Center alignment
        textColor=colors.darkblue,
        spaceAfter=14
    )

    label_style = ParagraphStyle(
        name="LabelStyle",
        fontSize=14,
        leading=17,
        textColor=colors.darkred,
        spaceAfter=6,
        alignment=1  # Center alignment
    )

    detail_style = ParagraphStyle(
        name="DetailStyle",
        fontSize=12,
        leading=15,
        textColor=colors.black,
        spaceAfter=10,
        alignment=1  # Center alignment
    )

    footer_style = ParagraphStyle(
        name="FooterStyle",
        fontSize=10,
        leading=12,
        textColor=colors.grey,
        spaceAfter=6,
        alignment=1  # Center alignment
    )

    # Draw border around the ticket
    def draw_border(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(2)
        canvas.rect(0.5 * inch, 0.5 * inch, 7.5 * inch, 10 * inch)  # Outer border
        canvas.setLineWidth(1)
        canvas.rect(0.6 * inch, 0.6 * inch, 7.3 * inch, 9.8 * inch)  # Inner border
        canvas.restoreState()

    # Add ticket title
    title = Paragraph(f"<b>{museum_name}</b>", title_style)
    elements.append(title)

    # Spacer
    elements.append(Spacer(1, 0.5 * inch))

    # Add ticket details in a single line, centered
    data = [
        [Paragraph(f"<b>Name:</b>", label_style), Paragraph(name, detail_style)],
        [Paragraph(f"<b>Quantity:</b>", label_style), Paragraph(quantity, detail_style)],
        [Paragraph(f"<b>Mobile:</b>", label_style), Paragraph(mobile, detail_style)],
        [Paragraph(f"<b>Email:</b>", label_style), Paragraph(email, detail_style)],
        [Paragraph(f"<b>Date:</b>", label_style), Paragraph(date, detail_style)],
        [Paragraph(f"<b>Nationality:</b>", label_style), Paragraph(nationality, detail_style)],
        [Paragraph(f"<b>Ticket Price:</b>", label_style), Paragraph(f"Rs {ticket_price:.2f} per ticket", detail_style)],
        [Paragraph(f"<b>Total Price:</b>", label_style), Paragraph(f"Rs {total_price:.2f}", detail_style)],
    ]

    table = Table(data, colWidths=[2.75 * inch, 4.75 * inch])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkred),
        ('TEXTCOLOR', (1, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(table)

    # Footer
    footer = Paragraph("This ticket must be retained", footer_style)
    elements.append(footer)

    footer_note = Paragraph("Thank you for your purchase! Please carry this ticket with you to the museum.", footer_style)
    elements.append(footer_note)

    doc.build(elements, onFirstPage=draw_border)

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
