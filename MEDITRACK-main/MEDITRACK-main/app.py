from flask import Flask, render_template, request, redirect, session, jsonify, url_for, send_from_directory,flash
import sqlite3
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
import os
import datetime
import json
from datetime import datetime
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # for session security

# Define upload folder path
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_NAME = "meditrack.db"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                UserID INTEGER PRIMARY KEY AUTOINCREMENT,
                UserType VARCHAR(50) NOT NULL,
                Username VARCHAR(255) UNIQUE NOT NULL,
                Password VARCHAR(255) NOT NULL,
                Email VARCHAR(255) UNIQUE,
                CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                RelatedID TEXT
            )
        ''')
        # Patients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Patients (
                PatientID TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(6)))),
                UserID INTEGER UNIQUE NOT NULL,
                FirstName VARCHAR(255) NOT NULL,
                LastName VARCHAR(255) NOT NULL,
                DateOfBirth DATE,
                Gender VARCHAR(50),
                Address VARCHAR(255),
                PhoneNumber VARCHAR(20),
                InsuranceProviderID INTEGER,
                FOREIGN KEY (UserID) REFERENCES Users(UserID)
            )
        ''')
        # Reports table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Reports (
                ReportID INTEGER PRIMARY KEY AUTOINCREMENT,
                PatientID TEXT NOT NULL,
                ReportName VARCHAR(255),
                Category VARCHAR(255),
                FileType VARCHAR(50),
                FilePath VARCHAR(255),
                UploadedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (PatientID) REFERENCES Patients(PatientID)
            )
        ''')
        # Doctors table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Doctors (
                DoctorID INTEGER PRIMARY KEY AUTOINCREMENT,
                UserID INTEGER UNIQUE,
                FirstName VARCHAR(255) NOT NULL,
                LastName VARCHAR(255) NOT NULL,
                Specialization VARCHAR(255),
                ContactNumber VARCHAR(20),
                Email VARCHAR(255),
                FOREIGN KEY (UserID) REFERENCES Users(UserID)
            )
        ''')
        # Insurance Providers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS InsuranceProviders (
                InsuranceProviderID INTEGER PRIMARY KEY AUTOINCREMENT,
                ProviderName VARCHAR(255) NOT NULL,
                ContactNumber VARCHAR(20),
                Email VARCHAR(255),
                Address VARCHAR(255)
            )
        ''')
        # Diagnostic Centers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS DiagnosticCenters (
                DiagnosticCenterID INTEGER PRIMARY KEY AUTOINCREMENT,
                CenterName VARCHAR(255) NOT NULL,
                Address VARCHAR(255),
                ContactNumber VARCHAR(20),
                Email VARCHAR(255),
                Specialty VARCHAR(255)
            )
        ''')
        conn.commit()
        cursor.execute('''
    CREATE TABLE IF NOT EXISTS InsuranceRequests (
    RequestID INTEGER PRIMARY KEY AUTOINCREMENT,
    PatientID INTEGER,
    ProviderID INTEGER,
    ClaimAmount REAL,
    Reason TEXT,
    Status TEXT DEFAULT 'Pending'
    )
''')
        conn.commit()
        conn.execute("""
    CREATE TABLE IF NOT EXISTS TestBookings (
        BookingID INTEGER PRIMARY KEY AUTOINCREMENT,
        PatientID INTEGER,
        DiagnosticCenterID INTEGER,
        TestType TEXT,
        TestDate TEXT,
        BookingStatus TEXT DEFAULT 'Pending'
    )
    """)

    conn.commit()
    conn.close()
        

# ----- Routes -----

@app.route('/')
def home():
    return render_template('interface.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    
    if request.method == 'POST':
        # Use request.form.get() with a default value to avoid KeyError
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user_type = request.form.get('user_type', '').strip()
        
        # Validate required fields
        if not username or not password or not user_type:
            error = 'All fields are required.'
            return render_template('login.html', error=error)
        
        # Print debug info
        print(f"Login attempt: Username={username}, UserType={user_type}")
        
        # Connect to database
        conn = get_db_connection()
        
        try:
            # Query to find user by username
            user = conn.execute('SELECT * FROM Users WHERE Username = ?', (username,)).fetchone()
            
            if user:
                print(f"Found user: {dict(user)}")
                
                # Now check if password matches
                if user['Password'] == password:
                    print("Password matches")
                    
                    # Check if user type matches what was selected
                    if user['UserType'] == user_type:
                        print("User type matches")
                        
                        # Store user information in session
                        session['user_id'] = user['UserID']
                        session['user_type'] = user['UserType']
                        session['username'] = user['Username']
                        
                        # Redirect based on user type
                        if user_type == 'Patient':
                            return redirect('/patient_dashboard')
                        elif user_type == 'Doctor':
                            return redirect('/doctor_dashboard')
                        elif user_type == 'InsuranceProvider':
                            return redirect('/insurer_dashboard')
                        elif user_type == 'DiagnosticCenter':
                            return redirect('/diagnostic_dashboard')
                        else:
                            error = f"Unknown user type: {user_type}"
                    else:
                        print(f"User type mismatch: Selected {user_type}, DB has {user['UserType']}")
                        error = 'Invalid user type selected.'
                else:
                    print("Password doesn't match")
                    error = 'Invalid password.'
            else:
                print("No user found with that username")
                error = 'No account found with that username.'
                
        except Exception as e:
            print(f"Database error: {e}")
            error = 'Database error. Please try again.'
        
        finally:
            conn.close()
    
    return render_template('login.html', error=error)
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/patient_signup', methods=['GET', 'POST'])
def patient_signup():
    if request.method == 'GET':
        return render_template('patient_signup.html')  # Your HTML form file

    elif request.method == 'POST':
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form  # for form submission (non-AJAX)

        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        firstname = data.get('firstname')
        lastname = data.get('lastname')
        dob = data.get('dob')
        gender = data.get('gender')
        address = data.get('address')
        phonenumber = data.get('phonenumber')
        insurance = data.get('insurance')

        try:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO Users (UserType, Username, Password, Email)
                    VALUES (?, ?, ?, ?)
                ''', ('Patient', username, password, email))

                user_id = cursor.lastrowid

                cursor.execute('''
                    INSERT INTO Patients (
                        UserID, FirstName, LastName, DateOfBirth, Gender, Address, PhoneNumber, InsuranceProviderID
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, firstname, lastname, dob, gender, address, phonenumber, insurance))

                conn.commit()
            
            # If POST was from a form (not fetch), redirect to dashboard
            if not request.is_json:
                return redirect(url_for('patient_dashboard'))
            return jsonify({'message': 'Signup successful'}), 200

        except Exception as e:
            if request.is_json:
                return jsonify({'error': str(e)}), 500
            return f"Signup failed: {e}", 500



@app.route('/patient_dashboard')
def patient_dashboard():
    if 'user_id' not in session or session['user_type'] != 'Patient':
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db_connection()
    user = conn.execute('SELECT FirstName || " " || LastName as name, PatientID as user_id FROM Patients WHERE UserID = ?', (user_id,)).fetchone()
    conn.close()

    if user:
        return render_template('patient_dashboard.html', name=user['name'], user_id=user['user_id'])
    else:
        return "User not found", 404
@app.route('/diagnostic_centers')
def diagnostic_centers():

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()

    centers = conn.execute(
        "SELECT * FROM DiagnosticCenters"
    ).fetchall()

    conn.close()

    return render_template("diagnostic_centers.html", centers=centers)
@app.route('/book_test/<int:center_id>', methods=['GET','POST'])
def book_test(center_id):

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()

    # ✅ Get actual PatientID from Patients table
    patient = conn.execute(
        "SELECT PatientID FROM Patients WHERE UserID = ?",
        (session['user_id'],)
    ).fetchone()

    if not patient:
        conn.close()
        return "Patient not found"

    patient_id = patient['PatientID']  # ✅ CORRECT

    if request.method == 'POST':

        test_type = request.form['test_type']
        date = request.form['date']

        conn.execute(
            """
            INSERT INTO TestBookings
            (PatientID, DiagnosticCenterID, TestType, TestDate)
            VALUES (?, ?, ?, ?)
            """,
            (patient_id, center_id, test_type, date)  # ✅ FIXED
        )

        conn.commit()
        conn.close()

        return redirect('/patient_dashboard')

    center = conn.execute(
        "SELECT * FROM DiagnosticCenters WHERE DiagnosticCenterID = ?",
        (center_id,)
    ).fetchone()

    conn.close()

    return render_template("book_test.html", center=center)

@app.route('/insurance_providers')
def insurance_providers():

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()

    providers = conn.execute(
        "SELECT * FROM InsuranceProviders"
    ).fetchall()

    conn.close()

    return render_template("insurance_providers.html", providers=providers)
@app.route('/claim_insurance/<int:provider_id>', methods=['GET','POST'])
def claim_insurance(provider_id):

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()

    # Get PatientID from Patients table using UserID
    patient = conn.execute(
        "SELECT PatientID FROM Patients WHERE UserID = ?",
        (session['user_id'],)
    ).fetchone()

    if not patient:
        conn.close()
        return "Patient record not found"

    patient_id = patient['PatientID']   # ✅ Actual PatientID

    # Fetch insurance provider
    provider = conn.execute(
        "SELECT * FROM InsuranceProviders WHERE InsuranceProviderID = ?",
        (provider_id,)
    ).fetchone()

    if request.method == 'POST':

        hospital = request.form['hospital']
        treatment_date = request.form['treatment_date']
        amount = request.form['amount']
        reason = request.form['reason']

        conn.execute("""
        INSERT INTO InsuranceRequests
        (PatientID, ProviderID, ClaimAmount, Reason)
        VALUES (?, ?, ?, ?)
        """, (patient_id, provider_id, amount, reason))

        conn.commit()
        conn.close()

        return redirect('/patient_dashboard')

    conn.close()

    return render_template("claim.html", provider=provider)
@app.route('/profile_dashboard')
def profile_dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()

    user = conn.execute(
        "SELECT * FROM Users WHERE UserID=?",
        (session['user_id'],)
    ).fetchone()

    conn.close()

    return render_template("profile.html", user=user)
# ─────────────────────────────────────────────────────────────────────────────
# REPLACE THESE 3 ROUTES IN YOUR app.py
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/diagnostic_dashboard')
def diagnostic_dashboard():
    if 'user_id' not in session or session['user_type'] != 'DiagnosticCenter':
        return redirect('/login')

    conn = get_db_connection()

    # Fetch from Users table — always works regardless of DiagnosticCenters structure
    user = conn.execute(
        'SELECT * FROM Users WHERE UserID = ?',
        (session['user_id'],)
    ).fetchone()

    # Try to get extra center details from DiagnosticCenters by matching Email
    center = None
    if user and user['Email']:
        center = conn.execute(
            'SELECT * FROM DiagnosticCenters WHERE Email = ?',
            (user['Email'],)
        ).fetchone()

    conn.close()

    if not user:
        return redirect('/login')

    return render_template('diagnose_dashboard.html',
        userid        = user['UserID'],
        centername    = user['Username'],
        centerid      = user['RelatedID'],
        centeraddress = (center['Address']       if center else 'N/A'),
        centercontact = (center['ContactNumber'] if center else 'N/A'),
        centeremail   = (user['Email']           or 'N/A')
    )


# ─── API: Search patient by PatientID ────────────────────────────────────────

@app.route('/api/patients/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    if 'user_id' not in session or session['user_type'] != 'DiagnosticCenter':
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    patient = conn.execute('''
        SELECT PatientID,
               FirstName || " " || LastName AS name,
               CAST((julianday("now") - julianday(DateOfBirth)) / 365.25 AS INTEGER) AS age,
               Gender,
               PhoneNumber
        FROM Patients
        WHERE PatientID = ?
    ''', (patient_id,)).fetchone()
    conn.close()

    if not patient:
        return jsonify({'error': 'Patient not found'}), 404

    return jsonify({
        'id':      patient['PatientID'],
        'name':    patient['name'],
        'age':     patient['age'],
        'gender':  patient['Gender'],
        'contact': patient['PhoneNumber'] or 'N/A'
    })


# ─── API: Upload report and save to Reports table ────────────────────────────

@app.route('/api/uploadreport', methods=['POST'])
def api_upload_report():
    if 'user_id' not in session or session['user_type'] != 'DiagnosticCenter':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400

    file       = request.files['file']
    patient_id = request.form.get('patientid')
    category   = request.form.get('category')

    if not patient_id or not category:
        return jsonify({'success': False, 'message': 'Missing patient ID or category'}), 400

    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'File type not allowed. Use PDF, JPG, PNG, DOC.'}), 400

    conn = get_db_connection()

    # Verify patient exists
    patient = conn.execute(
        'SELECT PatientID FROM Patients WHERE PatientID = ?', (patient_id,)
    ).fetchone()

    if not patient:
        conn.close()
        return jsonify({'success': False, 'message': 'Patient not found'}), 404

    # Save file to uploads folder
    original_filename = secure_filename(file.filename)
    timestamp         = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    saved_filename    = f"{patient_id}_{category.replace(' ', '_')}_{timestamp}_{original_filename}"
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], saved_filename))

    filetype = original_filename.rsplit('.', 1)[-1].lower()

    # Insert into Reports table
    conn.execute('''
        INSERT INTO Reports (PatientID, ReportName, Category, FileType, FilePath)
        VALUES (?, ?, ?, ?, ?)
    ''', (patient_id, original_filename, category, filetype, saved_filename))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': f'{category} uploaded successfully'})
# ─────────────────────────────
# GET BOOKINGS
# ─────────────────────────────
@app.route('/api/testbookings', methods=['GET'])
def get_test_bookings():

    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()

    user = conn.execute(
        "SELECT RelatedID, UserType FROM Users WHERE UserID = ?",
        (session['user_id'],)
    ).fetchone()

    if not user or user['UserType'] != 'DiagnosticCenter':
        conn.close()
        return jsonify({'error': 'Access denied'}), 403

    center_id = user['RelatedID']

    bookings = conn.execute('''
        SELECT tb.BookingID, tb.PatientID, tb.TestType, tb.TestDate, tb.BookingStatus,
               p.FirstName || ' ' || p.LastName AS PatientName
        FROM TestBookings tb
        JOIN Patients p ON tb.PatientID = p.PatientID
        WHERE tb.DiagnosticCenterID = ?
        ORDER BY tb.TestDate DESC
    ''', (center_id,)).fetchall()

    conn.close()

    return jsonify([dict(b) for b in bookings])

# ─────────────────────────────
# UPDATE STATUS
# ─────────────────────────────
@app.route('/api/update_booking_status', methods=['POST'])
def update_booking_status():

    if 'user_id' not in session:
        return jsonify({'success': False}), 401

    data = request.get_json()
    booking_id = data.get('booking_id')
    status = data.get('status')

    if status not in ['Accepted', 'Rejected']:
        return jsonify({'success': False}), 400

    conn = get_db_connection()

    user = conn.execute(
        "SELECT RelatedID FROM Users WHERE UserID=?",
        (session['user_id'],)
    ).fetchone()

    center_id = user['RelatedID']

    conn.execute('''
        UPDATE TestBookings
        SET BookingStatus = ?
        WHERE BookingID = ? AND DiagnosticCenterID = ?
    ''', (status, booking_id, center_id))

    conn.commit()
    conn.close()

    return jsonify({'success': True})


# ===============================
# INSURANCE DASHBOARD
# ===============================
@app.route('/insurer_dashboard')
def insurer_dashboard():
    if 'user_id' not in session or session['user_type'] != 'InsuranceProvider':
        return redirect('/login')

    conn = get_db_connection()

    user = conn.execute(
        'SELECT * FROM Users WHERE UserID = ?',
        (session['user_id'],)
    ).fetchone()

    provider = conn.execute(
        'SELECT * FROM InsuranceProviders WHERE InsuranceProviderID = ?',
        (user['RelatedID'],)
    ).fetchone()

    conn.close()

    return render_template('insurance_dashboard.html',
        providerid      = provider['InsuranceProviderID'],
        providername    = provider['ProviderName'],
        providercontact = provider['ContactNumber'],
        provideremail   = provider['Email'],
        provideraddress = provider['Address']
    )


# ===============================
# GET PATIENT
# ===============================
@app.route('/api/insurer/patient/<patient_id>')
def insurer_get_patient(patient_id):

    if 'user_id' not in session or session['user_type'] != 'InsuranceProvider':
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()

    patient = conn.execute('''
        SELECT PatientID,
               FirstName || ' ' || LastName AS name,
               Gender,
               PhoneNumber
        FROM Patients
        WHERE PatientID = ?
    ''', (patient_id,)).fetchone()

    conn.close()

    if not patient:
        return jsonify({'error': 'Patient not found'}), 404

    return jsonify(dict(patient))


# ===============================
# GET INSURANCE REQUESTS
# ===============================
@app.route('/api/insurer/requests/<patient_id>')
def insurer_get_requests(patient_id):

    if 'user_id' not in session or session['user_type'] != 'InsuranceProvider':
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()

    user = conn.execute(
        "SELECT RelatedID FROM Users WHERE UserID=?",
        (session['user_id'],)
    ).fetchone()

    provider_id = user['RelatedID']

    requests = conn.execute('''
        SELECT *
        FROM InsuranceRequests
        WHERE PatientID = ? AND ProviderID = ?
    ''', (patient_id, provider_id)).fetchall()

    conn.close()

    return jsonify({'requests': [dict(r) for r in requests]})


# ===============================
# UPDATE STATUS
# ===============================
@app.route('/api/update_insurance_status', methods=['POST'])
def update_insurance_status():

    if 'user_id' not in session or session['user_type'] != 'InsuranceProvider':
        return jsonify({'success': False}), 401

    data = request.get_json()

    conn = get_db_connection()

    user = conn.execute(
        "SELECT RelatedID FROM Users WHERE UserID=?",
        (session['user_id'],)
    ).fetchone()

    provider_id = user['RelatedID']

    conn.execute('''
        UPDATE InsuranceRequests
        SET Status = ?
        WHERE RequestID = ? AND ProviderID = ?
    ''', (data['status'], data['request_id'], provider_id))

    conn.commit()
    conn.close()

    return jsonify({'success': True})
# ===============================
# GET REPORTS
# ===============================
@app.route('/api/insurer/reports/<patient_id>')
def insurer_get_reports(patient_id):

    if 'user_id' not in session or session['user_type'] != 'InsuranceProvider':
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()

    reports = conn.execute('''
        SELECT *
        FROM Reports
        WHERE PatientID = ?
    ''', (patient_id,)).fetchall()

    conn.close()

    return jsonify({'reports': [dict(r) for r in reports]})
@app.route('/api/insurer/requests', methods=['GET'])
def insurer_get_all_requests():

    if 'user_id' not in session or session['user_type'] != 'InsuranceProvider':
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()

    user = conn.execute(
        "SELECT RelatedID FROM Users WHERE UserID=?",
        (session['user_id'],)
    ).fetchone()

    provider_id = user['RelatedID']

    requests = conn.execute('''
        SELECT ir.*, 
               p.FirstName || ' ' || p.LastName AS PatientName
        FROM InsuranceRequests ir
        JOIN Patients p ON ir.PatientID = p.PatientID
        WHERE ir.ProviderID = ?
        ORDER BY ir.RequestID DESC
    ''', (provider_id,)).fetchall()

    conn.close()

    return jsonify({'requests': [dict(r) for r in requests]})

@app.route('/interface_dashboard')
def interface_dashboard():
    return render_template('interface.html')

@app.route('/upload_report', methods=['POST'])
def upload_report():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"})

    file = request.files['file']
    patient_id = request.form.get('patient_id')
    category = request.form.get('category')

    if file.filename == '':
        return jsonify({"success": False, "error": "Empty filename"})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Create unique filename with timestamp to avoid overwriting
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        filetype = filename.split('.')[-1]

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO Reports (PatientID, ReportName, Category, FileType, FilePath)
            VALUES (?, ?, ?, ?, ?)
        ''', (patient_id, filename, category, filetype, unique_filename))
        conn.commit()
        conn.close()

        return jsonify({"success": True})
    
    return jsonify({"success": False, "error": "Invalid file type"})
@app.route('/doctor_dashboard')
def doctor_dashboard():
    if 'user_id' not in session:
        print("User not in session, redirecting to login")
        return redirect('/login')
    
    if session['user_type'] != 'Doctor':
        print(f"Wrong user type: {session['user_type']}, redirecting to login")
        return redirect('/login')
    
    user_id = session['user_id']
    conn = get_db_connection()
    
    # Check if doctor exists in Doctors table
    doctor = conn.execute('SELECT * FROM Doctors WHERE UserID = ?', (user_id,)).fetchone()
    
    # If doctor doesn't exist in Doctors table, create a simple profile
    if not doctor:
        print(f"Doctor not found in Doctors table for UserID: {user_id}")
        # Get user info
        user = conn.execute('SELECT * FROM Users WHERE UserID = ?', (user_id,)).fetchone()
        if user:
            try:
                # Create a placeholder doctor record
                conn.execute('''
                    INSERT INTO Doctors (UserID, FirstName, LastName, Specialization, ContactNumber, Email)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, "Doctor", "User", "General", "", user['Email'] if user['Email'] else ""))
                conn.commit()
                print(f"Created placeholder doctor record for UserID: {user_id}")
            except Exception as e:
                print(f"Error creating doctor record: {e}")
    
    conn.close()
    
    return render_template('doctor_dashboard.html')

# API Routes
@app.route('/api/doctor/details')
def get_doctor_details():
    if 'user_id' not in session or session['user_type'] != 'Doctor':
        return jsonify({"error": "Not authenticated"}), 401
    
    user_id = session['user_id']
    conn = get_db_connection()
    doctor = conn.execute('''
        SELECT DoctorID, FirstName, LastName, Specialization, ContactNumber, Email
        FROM Doctors
        WHERE UserID = ?
    ''', (user_id,)).fetchone()
    conn.close()
    
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404
    
    return jsonify({
        "doctorId": doctor['DoctorID'],
        "firstName": doctor['FirstName'],
        "lastName": doctor['LastName'],
        "specialization": doctor['Specialization'],
        "contactNumber": doctor['ContactNumber'],
        "email": doctor['Email']
    })
@app.route('/uploads/<filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Update report viewing routes
@app.route('/view_report/<filename>')
def view_report(filename):
    return redirect(url_for('serve_file', filename=filename))

# Update the /api/patient/reports endpoint to include full URLs
@app.route('/api/patient/reports')
def get_patient_reports():
    if 'user_id' not in session or session['user_type'] != 'Doctor':
        return jsonify({"error": "Not authenticated"}), 401
    
    patient_id = request.args.get('patientId')
    category = request.args.get('category')
    
    if not patient_id:
        return jsonify({"error": "Patient ID is required"}), 400
    
    conn = get_db_connection()
    
    # Verify patient exists
    patient = conn.execute('SELECT PatientID FROM Patients WHERE PatientID = ?', (patient_id,)).fetchone()
    
    if not patient:
        conn.close()
        return jsonify({"error": "Patient not found", "reports": []}), 404
    
    # Get reports for the patient
    if category and category.lower() != 'all':
        reports = conn.execute('''
            SELECT ReportID, PatientID, ReportName as fileName, Category as category, 
                   FilePath as filePath, FileType as fileType, UploadedAt as uploadedAt
            FROM Reports 
            WHERE PatientID = ? AND Category = ?
            ORDER BY UploadedAt DESC
        ''', (patient_id, category)).fetchall()
    else:
        reports = conn.execute('''
            SELECT ReportID, PatientID, ReportName as fileName, Category as category, 
                   FilePath as filePath, FileType as fileType, UploadedAt as uploadedAt
            FROM Reports 
            WHERE PatientID = ?
            ORDER BY UploadedAt DESC
        ''', (patient_id,)).fetchall()

    conn.close()

    report_list = []
    for report in reports:
        report_dict = dict(report)
        # Add full URL for file access
        report_dict['fileUrl'] = url_for('serve_file', filename=report_dict['filePath'], _external=True)
        report_list.append(report_dict)

    return jsonify({
        "success": True,
        "reports": report_list
    })
@app.route('/api/add_prescription', methods=['POST'])
def add_prescription():

    if 'user_id' not in session or session['user_type'] != 'Doctor':
        return jsonify({"error": "Unauthorized"}), 403

    patient_id = request.form.get("patient_id")
    file = request.files.get("prescription_file")

    if not patient_id:
        return jsonify({"error": "Patient ID missing"}), 400

    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    filename = secure_filename(file.filename)

    if filename == "":
        return jsonify({"error": "Invalid filename"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, filename)

    file.save(filepath)

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO Reports
        (PatientID, ReportName, Category, FileType, FilePath, UploadedAt)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        patient_id,
        filename,
        "Prescription",
        filename.split('.')[-1],
        filename,
        datetime.now()
    ))

    conn.commit()
    conn.close()

    return jsonify({"message": "Prescription uploaded successfully"})
if __name__ == '__main__':
    init_db()  # Optional: ensures DB is set up
    app.run(debug=True)

