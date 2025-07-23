# Vehicle_Parking_App_MAD-1

This project is a multi-user Vehicle Parking App developed using Flask and SQLite. It allows administrators to manage parking lots and users, and allows users to register, find, park, and release parking spots.

---

### Requirements

All required Python libraries are listed in the `requirements.txt` file. The primary frameworks used are:
* Flask
* Flask-Login
* Flask-SQLAlchemy

---

### Setup and Execution

Follow these steps to set up and run the application on your local machine.

#### 1. Set Up a Virtual Environment

It is recommended to run the application in a virtual environment.

```bash
# Create a virtual environment named 'venv'
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### 2. Install Dependencies

Install all the required packages using the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

#### 3. Create the Database

Before running the app for the first time, you must create the database and the predefined Admin user.

```bash
python create_db.py
```

This will generate a `parking_app.db` file in your project directory. You only need to run this script once.

#### 4. Run the Application

Start the Flask development server.

```bash
python app.py
```

The application will now be running at `http://127.0.0.1:5000`.

---

### Application Usage

Once the application is running, you can start using it.

* **Admin Login:**
  * **Username:** `admin@parkingapp.com`
  * **Password:** `admin_password`

* **User Registration:**
  * Navigate to the registration page to create a new user account.
