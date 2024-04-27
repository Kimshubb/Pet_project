#!/usr/bin/python
"""Start our flask app"""
from flask import Flask, render_template, request, url_for, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from forms import Sign_inForm, User_registrationForm
from flask_login import UserMixin

"""Create an instance of the Flask class"""
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jpserp_kisii.db'
app.config ['SECRET_KEY'] = 'jps_erp'

db = SQLAlchemy(app)    

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(10), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    #school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    def __repr__(self):
        return f"User('{self.username}', '{self.role}')"


@app.route("/", strict_slashes=False)
def sign_in():
    form = Sign_inForm()
    return render_template('signin.html', form=form)

@app.route("/register", methods=['GET', 'POST'], strict_slashes=False)
def register():
    form = User_registrationForm()
    if form.validate_on_submit():
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('sign_in'))
    return render_template('register.html', form=form)
    
"""
@app.route('/login', strict_slashes=False)
def login():
    username = request.form['username']
    password = request.foorm['password']

    if username in users and users[username] == password:
        return redirect(url_for('dashboard'))
    else:
        return render.template(signin.html, error='Invalid username or password!')
    
@app.route('/', strict_slashes=False)
def dashboard():
    return render_template('dashboard.html')
"""
if __name__ == '__main__':
    app.run(debug=True)

