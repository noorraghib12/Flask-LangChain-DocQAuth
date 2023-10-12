from flask import Blueprint, render_template, request, flash,redirect, url_for,current_app
from .models import User, Queries
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user,login_required,logout_user,current_user
auth=Blueprint('auth',__name__)

@auth.route('/login',methods=["GET","POST"])
def login():
    if request.method == 'POST':
        email=request.form.get('email')
        password=request.form.get('password')
        user=User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password,password):
                flash("Logged in successfully!",category='success')
                login_user(user,remember=True)
                return redirect(url_for('views.home'))
            else:
                flash("Password is Incorrect", category='error')
        else:
            flash("Email does not exist", category='user')
        
    return render_template('login.html',user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out Succesfully!",category='success')
    return redirect(url_for('auth.login'))

@auth.route('/signup',methods=["GET","POST"])
def signup():
    if request.method=="POST":
        firstname=request.form.get('firstName')
        email=request.form.get('email')
        password1=request.form.get('password1')
        password2=request.form.get('password2')
        user=User.query.filter_by(email=email).first()
        if user:
            flash("Sorry, a user with this email already exists, please choose a different email address",category='error')
            return redirect(url_for('auth.signup'))
        elif len(email)<10:
            flash("Email is too short", category="error")
        elif " " in email:
            flash("Avoid using blankspaces in emails",category='error')
        elif len(password1)<8:
            flash("The password must be atleast of 8 characters in length", category='error')
        elif password2!=password1:
            flash("Sorry your passwords dont match",category="error")
        else:
            new_user=User(email=email,password=generate_password_hash(password1,method='sha256'),first_name=firstname)
            db.session.add(new_user)
            db.session.commit()
            flash("Account Created!",category='success')
            login_user(new_user,remember=True)
            new_query=Queries(query="hi",answer="As an AI model, I dont know how to reply to that.",user_id=current_user.id)
            db.session.add(new_query)
            db.session.commit()
            flash("Chat Created!",category='success')
            return redirect(url_for('views.home'))

    return render_template("signup.html",user=current_user)