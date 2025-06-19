from flask import Flask, render_template, request, redirect, url_for, flash
from models.database import db
from models.database import User, ParkingLot, ParkingSpot
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'a-truly-secret-key-that-is-hard-to-guess'

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
            flash('An account with that email already exists.', 'danger')
            return redirect(url_for('register'))
        
        # New user w hashed password
        hashed_password = generate_password_hash(request.form.get('password'), method='pbkdf2:sha256')
        new_user = User(
            full_name=request.form.get('full_name'),
            username=request.form.get('username'),
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        # Checking entry
        if not user or not check_password_hash(user.password, request.form.get('password')):
            flash("Invalid username or password", 'danger')
            return redirect(url_for('login'))
        
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
    
    all_users = User.query.all()
    all_lots = ParkingLot.query.all()
    return render_template('admin_dashboard.html', users=all_users, lots=all_lots)

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    return f"<h1>Welcome to your Dashboard, {current_user.full_name}!</h1>"


@app.route('/admin/add_lot', methods=['GET', 'POST'])
@login_required
def add_lot():
    if current_user.role != 'Admin':
        return "Access Denied", 403

    if request.method == 'POST':
        new_lot = ParkingLot(
            prime_location_name=request.form.get('prime_location_name'),
            address=request.form.get('address'),
            pin_code=request.form.get('pin_code'),
            price=float(request.form.get('price')),
            maximum_number_of_spots=int(request.form.get('maximum_number_of_spots'))
        )
        db.session.add(new_lot)
        db.session.commit()


        for i in range(new_lot.maximum_number_of_spots):
            new_spot = ParkingSpot(lot_id=new_lot.id, spot_number=i + 1)
            db.session.add(new_spot)

        db.session.commit()
        flash('New parking lot and its spots have been created successfully.', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('add_lot.html')


@app.route('/admin/delete_lot/<int:lot_id>', methods=['POST'])
@login_required
def delete_lot(lot_id):
    if current_user.role != 'Admin':
        flash('Access Denied.', 'danger')
        return redirect(url_for('login'))

    lot_to_delete = ParkingLot.query.get_or_404(lot_id)

    is_any_spot_occupied = any(spot.status == 'O' for spot in lot_to_delete.spots)

    if is_any_spot_occupied:
        flash('Cannot delete lot: One or more spots are currently occupied.', 'warning')
    else:
        db.session.delete(lot_to_delete)
        db.session.commit()
        flash('Parking lot has been successfully deleted.', 'success')

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/edit_lot/<int:lot_id>', methods=['GET', 'POST'])
@login_required
def edit_lot(lot_id):
    if current_user.role != 'Admin':
        return "Access Denied", 403

    lot_to_edit = ParkingLot.query.get_or_404(lot_id)
    old_capacity = lot_to_edit.maximum_number_of_spots

    if request.method == 'POST':
        lot_to_edit.prime_location_name = request.form.get('prime_location_name')
        lot_to_edit.address = request.form.get('address')
        lot_to_edit.pin_code = request.form.get('pin_code')
        lot_to_edit.price = float(request.form.get('price'))
        new_capacity = int(request.form.get('maximum_number_of_spots'))
        lot_to_edit.maximum_number_of_spots = new_capacity

        if new_capacity > old_capacity:
            spots_to_add = new_capacity - old_capacity
            last_spot_num = db.session.query(db.func.max(ParkingSpot.spot_number)).filter_by(lot_id=lot_to_edit.id).scalar() or 0
            for i in range(spots_to_add):
                new_spot = ParkingSpot(lot_id=lot_to_edit.id, spot_number=last_spot_num + i + 1, status='A')
                db.session.add(new_spot)
            flash(f'{spots_to_add} new spots have been added.', 'success')

        elif new_capacity < old_capacity:
            spots_to_remove_count = old_capacity - new_capacity
            
            available_spots_to_remove = ParkingSpot.query.filter_by(lot_id=lot_to_edit.id, status='A').order_by(ParkingSpot.spot_number.desc()).limit(spots_to_remove_count).all()

            if len(available_spots_to_remove) < spots_to_remove_count:
                flash(f'Cannot reduce capacity by {spots_to_remove_count}. Not enough available spots to remove.', 'danger')
            else:
                for spot in available_spots_to_remove:
                    db.session.delete(spot)
                flash(f'{spots_to_remove_count} spots have been removed.', 'success')

        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_lot.html', lot=lot_to_edit)

@app.route('/')
def index():
    return "<h1>Welcome to the Vehicle Parking App!</h1> <a href='/login'>Login</a> <a href='/register'>Register</a>"


if __name__ == '__main__':
    app.run(debug=True)