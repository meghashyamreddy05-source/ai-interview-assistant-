import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader

app = Flask(__name__)
app.secret_key = "ai_prep_final_v1"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///interview_assistant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Resume Storage
UPLOAD_FOLDER = 'uploads/resumes'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    hashed_pw = bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8')
    new_user = User(full_name=request.form.get('full_name'), mobile=request.form.get('mobile'),
                    email=request.form.get('email'), password=hashed_pw)
    try:
        db.session.add(new_user)
        db.session.commit()
        session['user_name'] = new_user.full_name
        return redirect(url_for('dashboard'))
    except:
        return "Registration Error"

@app.route('/dashboard')
def dashboard():
    if 'user_name' not in session: return redirect(url_for('login'))
    return render_template('dashboard.html', name=session['user_name'])

@app.route('/setup/<domain>')
def setup_page(domain):
    if 'user_name' not in session: return redirect(url_for('login'))
    return render_template('setup.html', domain=domain)

# --- PAGE 4 ROUTE (Fixed for 404) ---
@app.route('/analyze_resume', methods=['POST'])
def analyze_resume():
    if 'user_name' not in session: return redirect(url_for('login'))
    
    file = request.files.get('resume')
    if file:
        filename = secure_filename(f"{session['user_name']}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    session['selected_role'] = request.form.get('job_role')
    session['difficulty'] = request.form.get('level')

    # Mock Analysis
    score = 82
    suggestions = [
        {"type": "Action", "text": "Use more power verbs like 'Executed' or 'Streamlined'."},
        {"type": "Keywords", "text": "Add skills specific to " + session['selected_role']}
    ]
    return render_template('ats_checker.html', score=score, suggestions=suggestions)

@app.route('/interview')
def interview_room():
    if 'user_name' not in session: return redirect(url_for('login'))
    role = session.get('selected_role', 'Professional')
    questions = [f"Describe your journey as a {role}.", "What is your biggest strength?", 
                 "Tell me about a time you failed.", "How do you handle pressure?", 
                 "Why should we hire you?", "Where do you see yourself in 3 years?", 
                 "What is your work ethic?", "How do you learn new tools?", 
                 "Describe a team conflict.", "Do you have questions for us?"]
    return render_template('interview.html', questions=questions)

@app.route('/submit_interview', methods=['POST'])
def submit_interview():
    session['interview_results'] = request.json.get('responses')
    return jsonify({"status": "success", "redirect": url_for('final_results')})

@app.route('/results')
def final_results():
    if 'user_name' not in session: return redirect(url_for('login'))
    responses = session.get('interview_results', [])
    total_score = sum([10 if len(i['answer'].split()) > 15 else 5 for i in responses])
    return render_template('results.html', percentage=total_score, details=responses)

if __name__ == '__main__':
    app.run(debug=True)