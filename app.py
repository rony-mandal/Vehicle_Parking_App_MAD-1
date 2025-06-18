from flask import Flask, render_template, request, redirect, url_for
from models.database import db
from models.database import User
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret_key_here'

db.init_app(app)

# Initializing Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user:
            return "User already exists!"
        # New user w hashed password
        hashed_password = generate_password_hash(request.form.get('password'), method='pbkdf2:sha256')
        new_user = User(
            full_name=request.form.get('full_name'),
            username=request.form.get('username'),
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        # Checking entry
        if not user or not check_password_hash(user.password, request.form.get('password')):
            return "Invalid username or password"
        
        # Logging user
        login_user(user) 
        
        # Redirect based on role 
        if user.role == 'Admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# --- Role-Specific Dashboards ---

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'Admin':
        return "Access Denied", 403
    return "<h1>Welcome to the Admin Dashboard!</h1>"

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    return f"<h1>Welcome to your Dashboard, {current_user.full_name}!</h1>"


@app.route('/')
def index():
    return "<h1>Welcome to the Vehicle Parking App!</h1> <a href='/login'>Login</a> <a href='/register'>Register</a>"

if __name__ == '__main__':
    app.run(debug=True)