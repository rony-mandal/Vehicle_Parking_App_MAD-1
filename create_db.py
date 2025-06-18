from app import app, db
from models.database import User
from werkzeug.security import generate_password_hash

with app.app_context():
    print("Creating database tables...")
    db.create_all()
    print("Tables created.")

    #admin user existence check
    if not User.query.filter_by(username='admin@parkingapp.com').first():
        print("Creating admin user...")

        #hashing admin pwd
        hashed_password = generate_password_hash('admin_password', method='pbkdf2:sha256')
        admin = User(
            username='admin@parkingapp.com',
            password= hashed_password, 
            full_name='Admin User',
            role='Admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created.")
    else:
        print("Admin user already exists.")