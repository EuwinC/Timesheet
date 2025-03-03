from flask import Flask, jsonify, request, session, redirect, url_for
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import json
import pandas as pd
import logging
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Enable CORS for WordPress server
CORS(app, resources={r"/api/*": {"origins": "http://192.168.168.13"}})

logging.basicConfig(level=logging.DEBUG)

users = {}

DATABASE_FOLDER = 'database'
TIMESHEET_FOLDER = 'database/timesheet_data'
EMPLOYEE_FILE = 'database/user_data/employee.json'
CUSTOMER_FILE = 'database/customer_data/customer_type.json'

def ensure_database_folder():
    if not os.path.exists(DATABASE_FOLDER):
        os.makedirs(DATABASE_FOLDER)

def save_users():
    with open(os.path.join(DATABASE_FOLDER, 'users.json'), 'w') as file:
        json.dump(users, file)

def load_users():
    global users
    try:
        with open(os.path.join(DATABASE_FOLDER, 'users.json'), 'r') as file:
            users = json.load(file)
    except FileNotFoundError:
        users = {}

# Middleware to check authentication
def require_login(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Please log in first.", "status": "unauthorized"}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the Flask API!", "status": "success"})

# API Routes
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user_id = data.get('user_id')
    password = data.get('password')
    load_users()
    if user_id not in users or not check_password_hash(users[user_id]['password'], password):
        return jsonify({"error": "Invalid user ID or password.", "status": "failure"}), 401
    session['user_id'] = user_id
    return jsonify({"message": "Login successful.", "status": "success", "user_id": user_id}), 200

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    user_id = data.get('user_id')
    password = data.get('password')
    load_users()
    if user_id in users:
        return jsonify({"error": "User ID already exists.", "status": "failure"}), 400
    hashed_password = generate_password_hash(password)
    users[user_id] = {'name': name, 'password': hashed_password}
    save_users()
    return jsonify({"message": "Registration successful. Please log in.", "status": "success"}), 201

@app.route('/api/dashboard', methods=['GET', 'POST'])
@require_login
def dashboard():
    json_files = [f for f in os.listdir(DATABASE_FOLDER) if f.endswith('.json') and f != 'users.json']
    selected_file = None
    timesheet = []
    selected_year = request.args.get('year', datetime.now().year, type=int)
    selected_month = request.args.get('month', datetime.now().month, type=int)

    if request.method == 'POST':
        data = request.get_json()
        selected_file = data.get('json_file')
        selected_year = data.get('year', selected_year)
        selected_month = data.get('month', selected_month)
        if selected_file:
            with open(os.path.join(DATABASE_FOLDER, selected_file), 'r') as file:
                timesheet = json.load(file)
    
    filtered_timesheet = [t for t in timesheet if t.get('Year') == selected_year and t.get('Month') == selected_month]
    return jsonify({
        "json_files": json_files,
        "timesheet": filtered_timesheet,
        "selected_file": selected_file,
        "selected_year": selected_year,
        "selected_month": selected_month
    })

def load_employees():
    with open(EMPLOYEE_FILE, 'r') as file:
        return json.load(file)

def save_employees(employees):
    with open(EMPLOYEE_FILE, 'w') as file:
        json.dump(employees, file, indent=4)

def load_customers():
    with open(CUSTOMER_FILE, 'r') as file:
        return json.load(file)

def save_customers(customers):
    with open(CUSTOMER_FILE, 'w') as file:
        json.dump(customers, file, indent=4)

@app.route('/api/preview', methods=['POST'])
@require_login
def preview():
    file = request.files.get('file')
    if file:
        df = pd.read_excel(file)
        df.fillna('', inplace=True)
        return jsonify({"data": df.to_dict(orient='records')})
    return jsonify({"message": "No file provided."}), 400

@app.route('/api/settings', methods=['GET'])
@require_login
def settings():
    employees = load_employees()
    customer_types = load_customers()
    return jsonify({
        "current_customer": "Current Customer Name",
        "people_list": employees,
        "customer_types": customer_types
    })

@app.route('/api/add_person', methods=['POST'])
@require_login
def add_person():
    data = request.get_json()
    name = data.get('new_person_name')
    staff_number = data.get('new_person_staff_number')
    employees = load_employees()
    
    if any(e['Name'] == name and e['Staff Number'] == staff_number for e in employees):
        return jsonify({"error": "Person already exists!", "status": "failure"}), 400
    
    employees.append({"Name": name, "Staff Number": staff_number})
    save_employees(employees)
    return jsonify({"message": "Person added successfully!", "status": "success"}), 200

@app.route('/api/remove_person', methods=['POST'])
@require_login
def remove_person():
    data = request.get_json()
    name = data.get('remove_person')
    employees = load_employees()
    employees = [e for e in employees if e['Name'] != name]
    save_employees(employees)
    return jsonify({"message": "Person removed successfully!", "status": "success"}), 200

@app.route('/api/add_customer', methods=['POST'])
@require_login
def add_customer():
    data = request.get_json()
    customer_name = data.get('new_customer_name')
    customer_type = data.get('new_customer_type')
    customers = load_customers()
    
    if customer_name in customers:
        return jsonify({"error": "Customer already exists!", "status": "failure"}), 400
    
    customers[customer_name] = customer_type
    save_customers(customers)
    return jsonify({"message": "Customer added successfully!", "status": "success"}), 200

@app.route('/api/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if not file or not file.filename.endswith('.xlsx'):
        return jsonify({"error": "Invalid file format. Please upload an Excel file.", "status": "failure"}), 400
    
    try:
        df = pd.read_excel(file, sheet_name='Result')
        # Handle potential NaN or non-numeric values
        year = df.iloc[2, 1]
        month = df.iloc[2, 3]
        if pd.isna(year) or pd.isna(month):
            return jsonify({"error": "Year or month is missing in the Excel file.", "status": "failure"}), 400
        year = int(float(year))  # Convert to float first to handle decimals
        month = int(float(month))
        dates = df.iloc[6, 1:]
        time_slots = df.iloc[7, 1:]
        name = df.iloc[8, 0].replace(' ', '_')
        timesheet_data = []
        json_filename = os.path.join(TIMESHEET_FOLDER, f'{name}.json')

        # Ensure directory exists
        os.makedirs(TIMESHEET_FOLDER, exist_ok=True)

        # Load existing data if the file exists
        try:
            with open(json_filename, 'r') as json_file:
                timesheet_data = json.load(json_file)
                exist = set()
                for task in timesheet_data:
                    y = str(task['Year'])
                    m = str(task['Month']) if task['Month'] >= 10 else '0' + str(task['Month'])
                    d = str(task['Date']) if task['Date'] >= 10 else '0' + str(task['Date'])
                    exist.add(y + m + d + task['time_slots'])
        except FileNotFoundError:
            exist = set()

        for col in range(1, df.shape[1]):
            date = dates[col-1]
            if pd.isna(date):
                continue  # Skip if date is NaN
            date = int(float(date))  # Handle potential floats
            key = f"{date:02d}{month:02d}{year % 100:02d}{time_slots[col-1]}"
            if df.iloc[8, col] not in ['/', 'AL', 'SL', 'CL']:
                task_data = df.iloc[8, col].split('|')
                if len(task_data) < 4:
                    task_data.extend([None] * (4 - len(task_data)))
                task = {
                    'Year': year, 'Month': month, 'Date': date, 'time_slots': time_slots[col-1],
                    'Location': task_data[0], 'Customer': task_data[1], 'Job_Type': task_data[2],
                    'Work_Detail': task_data[3], 'SO': task_data[4] if len(task_data) > 4 else None
                }
            else:
                task = {
                    'Year': year, 'Month': month, 'Date': date, 'time_slots': time_slots[col-1],
                    'off': "Public Holiday" if df.iloc[8, col] == '/' else df.iloc[8, col]
                }
            if key not in exist:
                timesheet_data.append(task)
                exist.add(key)

        timesheet_data = sorted(timesheet_data, key=lambda x: (x['Year'], x['Month'], x['Date'], x['time_slots']))
        with open(json_filename, 'w') as json_file:
            json.dump(timesheet_data, json_file, indent=4)
        return jsonify({"message": "Excel file uploaded and tasks added successfully.", "status": "success"}), 200
    except Exception as e:
        logging.error(f'Error processing file: {e}')
        return jsonify({"error": f"An error occurred while processing the file: {str(e)}", "status": "failure"}), 500
@app.route('/api/statistics', methods=['GET', 'POST'])
def statistics():  # Removed @require_login
    years = [2024, 2025,2026,2027,2028,2029,2030,2031,2032,2033,2034,2035,2036,2037,2038,2039,2040,2041,2042,2043,2044,2045,2046,2047]
    months = list(range(1, 13))
    selected_year = request.args.get('year', datetime.now().year, type=int)
    selected_month = request.args.get('month', datetime.now().month, type=int)
    selected_job_type = request.args.get('job_type', 'PS')
    selected_file = request.args.get('timesheet_file', 'SSS_Team')  # Default to SSS_Team

    if request.method == 'POST':
        data = request.get_json() or request.form
        selected_year = int(data.get('year', selected_year))
        selected_month = int(data.get('month', selected_month))
        selected_job_type = data.get('job_type', 'PS')
        selected_file = data.get('timesheet_file', 'SSS_Team')

    employees = load_employees()
    total_employees = len(employees)
    customer_pairs = load_customers()
    timesheet_dir = TIMESHEET_FOLDER
    timesheet_files = [f for f in os.listdir(timesheet_dir) if f.endswith('.json')]

    onsite_count, office_count, ps_count, ma_count, internal_count, presales_count = 0, 0, 0, 0, 0, 0
    timesheet_submitted = set()
    customer_types = ['THU', 'FSI', 'EDU/NGO', 'GOV', 'Others']
    customer_data = {c: {'PS': 0.0, 'Pre-Sales': 0.0, 'MA': 0.0} for c in customer_types}
    customer_data['TBC'] = {'MA': 0.0}

    monthly_projects = {}
    total_working_days = 0
    off = {'AL':0,'CL':0,'SL':0,'Public Holiday':0}
    if selected_file == 'SSS_Team':  # Replacing 'overview' with 'SSS_Team'
        for tf in timesheet_files:
            with open(os.path.join(timesheet_dir, tf), 'r') as file:
                timesheet_data = json.load(file)
                for entry in timesheet_data:
                    if entry['Year'] == selected_year and entry['Month'] == selected_month:
                        timesheet_submitted.add(tf)
                        if entry.get('Location') == 'Onsite':
                            onsite_count += 0.5
                        elif entry.get('Location') == 'Office':
                            office_count += 0.5
                        job_type = entry.get('Job_Type')
                        
                        if job_type == 'PS':
                            ps_count += 0.5
                        elif job_type == 'MA':
                            ma_count += 0.5
                        elif job_type == 'Internal':
                            internal_count += 0.5
                        elif job_type == 'Pre-Sales':
                            presales_count += 0.5
                        customer = entry.get('Customer')
                        if customer in customer_pairs:
                            cat = customer_pairs[customer]
                            if job_type in customer_data[cat]:
                                customer_data[cat][job_type] += 0.5
                        if 'Customer' in entry and 'Work_Detail' in entry and 'SO' in entry:
                            total_working_days += 0.5
                            project_key = (entry['Customer'], entry['Work_Detail'], entry['SO'])
                            if project_key not in monthly_projects:
                                monthly_projects[project_key] = {
                                    'customer': entry['Customer'], 'name': entry['Work_Detail'], 'so': entry['SO'], 'frequency': 0
                                }
                            monthly_projects[project_key]['frequency'] += 0.5
    else:
        with open(os.path.join(timesheet_dir, selected_file + '.json'), 'r') as file:
            timesheet_data = json.load(file)
            for entry in timesheet_data:
                if entry['Year'] == selected_year and entry['Month'] == selected_month:
                    timesheet_submitted.add(selected_file + '.json')
                    if entry.get('Location') == 'Onsite':
                        onsite_count += 0.5
                    elif entry.get('Location') == 'Office':
                        office_count += 0.5
                    if 'off' in entry:
                        if entry['off'] in off:
                            off[entry['off']] += 0.5
                    job_type = entry.get('Job_Type')
                    if job_type == 'PS':
                        ps_count += 0.5
                    elif job_type == 'MA':
                        ma_count += 0.5
                    elif job_type == 'Internal':
                        internal_count += 0.5
                    elif job_type == 'Pre-Sales':
                        presales_count += 0.5
                    customer = entry.get('Customer')
                    if customer in customer_pairs:
                        cat = customer_pairs[customer]
                        if job_type in customer_data[cat]:
                            customer_data[cat][job_type] += 0.5
                    if 'Customer' in entry and 'Work_Detail' in entry and 'SO' in entry:
                        total_working_days += 0.5
                        project_key = (entry['Customer'], entry['Work_Detail'], entry['SO'])
                        if project_key not in monthly_projects:
                            monthly_projects[project_key] = {
                                'customer': entry['Customer'], 'name': entry['Work_Detail'], 'so': entry['SO'], 'frequency': 0
                            }
                        monthly_projects[project_key]['frequency'] += 0.5

    total_entries = onsite_count + office_count
    total_job_entries = ps_count + ma_count + internal_count + presales_count

    monthly_projects_list = [
        {
            'customer': project['customer'], 'name': project['name'], 'so': project['so'],
            'frequency': project['frequency'], 'percentage': (project['frequency'] / total_working_days * 100) if total_working_days > 0 else 0
        }
        for project in monthly_projects.values()
    ]

    return jsonify({
        "years": years, "months": months, "selected_year": selected_year, "selected_month": selected_month,
        "onsite_percentage": (onsite_count / total_entries * 100) if total_entries > 0 else 0,
        "office_percentage": (office_count / total_entries * 100) if total_entries > 0 else 0,
        "timesheet_count": len(timesheet_submitted),
        "ps_percentage": (ps_count / total_job_entries * 100) if total_job_entries > 0 else 0,
        "ma_percentage": (ma_count / total_job_entries * 100) if total_job_entries > 0 else 0,
        "internal_percentage": (internal_count / total_job_entries * 100) if total_job_entries > 0 else 0,
        "presales_percentage": (presales_count / total_job_entries * 100) if total_job_entries > 0 else 0,
        "customer_data": customer_data, "selected_job_type": selected_job_type,
        "monthly_projects": monthly_projects_list,
        "timesheet_files": [f[:-5].replace('_', ' ') for f in timesheet_files],  # Remove .json and replace _ with space
        "selected_file": selected_file,
        "off": off if selected_file != 'SSS_Team' else None,
        "status": "success"
    })

@app.route('/api/logout', methods=['POST'])
@require_login
def logout():
    session.pop('user_id', None)
    return jsonify({"message": "Logged out successfully.", "status": "success"}), 200

# For production deployment with waitress
if __name__ == '__main__':
    from waitress import serve
    ensure_database_folder()
    load_users()
    serve(app, host='0.0.0.0', port=5000)
