import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from models.database import db
from models.database import User, ParkingLot, ParkingSpot, Reservation
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'a-truly-secret-key-that-is-hard-to-guess'

db.init_app(app)

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

        if not user:
            flash('No account found with that email. Please register first.', 'danger')
            return redirect(url_for('register'))
        if not check_password_hash(user.password, request.form.get('password')):
            flash('Incorrect password. Please try again.', 'danger')
            return redirect(url_for('login'))
        
        login_user(user) 
 
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


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'Admin':
        return "Access Denied", 403
    
    all_users = User.query.all()
    all_lots = ParkingLot.query.all()
    all_reservations = Reservation.query.order_by(Reservation.parking_timestamp.desc()).all()
    return render_template('admin_dashboard.html', users=all_users, lots=all_lots, reservations=all_reservations)

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if current_user.role != 'User':
        return "Access Denied", 403
    
    active_res = Reservation.query.filter_by(user_id=current_user.id, leaving_timestamp=None).first()
    all_lots = ParkingLot.query.all()

    return render_template('user_dashboard.html', lots=all_lots, active_reservation=active_res)


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
        return redirect(url_for('admin_dashboard'))

    spot_ids = [spot.id for spot in lot_to_delete.spots]
    has_history = Reservation.query.filter(Reservation.spot_id.in_(spot_ids)).first()
    if has_history:
        flash('Cannot delete lot: Spots in this lot have a reservation history.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
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

    if request.method == 'POST':
        old_capacity = lot_to_edit.maximum_number_of_spots
        
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
            
            spots_ordered = ParkingSpot.query.filter_by(lot_id=lot_to_edit.id, status='A').order_by(ParkingSpot.spot_number.desc()).all()
            
            safe_to_delete = []
            for spot in spots_ordered:
                has_history = Reservation.query.filter_by(spot_id=spot.id).first()
                if not has_history:
                    safe_to_delete.append(spot)
            
            if len(safe_to_delete) < spots_to_remove_count:
                flash(f'Cannot reduce capacity by {spots_to_remove_count}. Not enough unused spots to remove.', 'danger')
            else:
                for i in range(spots_to_remove_count):
                    db.session.delete(safe_to_delete[i])
                flash(f'{spots_to_remove_count} spots have been removed.', 'success')

        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_lot.html', lot=lot_to_edit)


@app.route('/user/park/<int:lot_id>', methods=['POST'])
@login_required
def park_here(lot_id):
    if current_user.role != 'User':
        return "Access Denied", 403

    if Reservation.query.filter_by(user_id=current_user.id, leaving_timestamp=None).first():
        flash('You are already parked somewhere.', 'danger')
        return redirect(url_for('user_dashboard'))

    first_available_spot = ParkingSpot.query.filter_by(lot_id=lot_id, status='A').order_by(ParkingSpot.spot_number).first()

    if not first_available_spot:
        flash('Sorry, this parking lot is full.', 'danger')
        return redirect(url_for('user_dashboard'))

    first_available_spot.status = 'O'
    new_reservation = Reservation(
        user_id=current_user.id,
        spot_id=first_available_spot.id,
        parking_timestamp=datetime.datetime.now()
    )
    db.session.add(new_reservation)
    db.session.commit()

    flash(f'Success! You have been assigned Spot {first_available_spot.spot_number} in {first_available_spot.lot.prime_location_name}.', 'success')
    return redirect(url_for('user_dashboard'))


@app.route('/user/release/<int:reservation_id>', methods=['POST'])
@login_required
def release_spot(reservation_id):
    reservation_to_release = Reservation.query.get_or_404(reservation_id)

    if reservation_to_release.user_id != current_user.id:
        return "Access Denied", 403

    spot = ParkingSpot.query.get(reservation_to_release.spot_id)
    if not spot:
        flash("Could not find the spot associated with this reservation. Please contact an admin.", "danger")
        return redirect(url_for('user_dashboard'))

    spot.status = 'A'
    reservation_to_release.leaving_timestamp = datetime.datetime.now()
    
    lot_price_per_minute = spot.lot.price
    duration = reservation_to_release.leaving_timestamp - reservation_to_release.parking_timestamp
    duration_in_minutes = duration.total_seconds() / 60
    total_cost = duration_in_minutes * lot_price_per_minute
    reservation_to_release.parking_cost = total_cost

    db.session.commit()

    flash(f'Spot {spot.spot_number} has been released. Total cost: ${total_cost:.2f}. Thank you!', 'success')
    return redirect(url_for('user_dashboard'))


@app.route('/user/history')
@login_required
def parking_history():
    if current_user.role != 'User':
        return "Access Denied", 403
    
    completed_reservations = Reservation.query.filter(
        Reservation.user_id == current_user.id,
        Reservation.leaving_timestamp.isnot(None)
    ).order_by(Reservation.parking_timestamp.desc()).all()

    return render_template('parking_history.html', reservations=completed_reservations)


@app.route('/admin/user_history/<int:user_id>')
@login_required
def admin_view_user_history(user_id):
    if current_user.role != 'Admin':
        return "Access Denied", 403
    
    target_user = User.query.get_or_404(user_id)
    user_reservations = Reservation.query.filter_by(user_id=target_user.id).order_by(Reservation.parking_timestamp.desc()).all()
    return render_template('admin_view_user_history.html', target_user=target_user, reservations=user_reservations)


@app.route('/')
def index():
    return "<h1>Welcome to the Vehicle Parking App!</h1> <a href='/login'>Login</a> <a href='/register'>Register</a>"


if __name__ == '__main__':
    app.run(debug=True)