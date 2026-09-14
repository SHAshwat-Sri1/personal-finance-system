from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

# -----------------------------------------------------------
# 1. REGISTER ROUTE
# -----------------------------------------------------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # If already logged in, no need to register again
    if current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if user with that email/username already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already registered! Please log in.', 'danger')
            return redirect(url_for('auth.register'))

        # Security: Never store plain text passwords! Hash it first:
        hashed_pw = generate_password_hash(password)

        new_user = User(username=username, email=email, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

# -----------------------------------------------------------
# 2. LOGIN ROUTE
# -----------------------------------------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return f"<h1>Hello {current_user.username}! You are already logged in. <a href='/auth/logout'>Logout</a></h1>"

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        # Check if user exists AND the password matches the hash
        if user and check_password_hash(user.password_hash, password):
            login_user(user)  # Creates the session cookie!
            flash(f'Welcome back, {user.username}!', 'success')
            return f"<h1>Success! Welcome {user.username}! <a href='/auth/logout'>Click here to Logout</a></h1>"
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('login.html')

# -----------------------------------------------------------
# 3. LOGOUT ROUTE
# -----------------------------------------------------------
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
