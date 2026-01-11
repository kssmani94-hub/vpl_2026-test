import os
import csv
from io import StringIO
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- 1. Configuration ---
app.config['SECRET_KEY'] = 'vpl_2026_admin_super_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vpl_database.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# Ensure the upload directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)

# --- 2. Database Model (Capturing All 17+ Fields) ---
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vpl_id = db.Column(db.String(20), unique=True)
    full_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    ch_reg_same = db.Column(db.String(10)) # "Yes" or "No"
    ch_mobile = db.Column(db.String(15), nullable=False)
    ch_name = db.Column(db.String(100), nullable=False)
    current_team = db.Column(db.String(100), nullable=False)
    prev_team = db.Column(db.String(100))
    role = db.Column(db.String(50), nullable=False)
    style = db.Column(db.String(100), nullable=False)
    photo = db.Column(db.String(200), nullable=False) # Renamed to VPL-XXX.jpg
    shirt_name = db.Column(db.String(50), nullable=False)
    shirt_number = db.Column(db.Integer, nullable=False)
    shirt_size = db.Column(db.String(10), nullable=False)
    sleeves = db.Column(db.String(20), nullable=False)
    comments = db.Column(db.Text)
    status = db.Column(db.String(20), default='Registered')

# Create the database file
with app.app_context():
    db.create_all()

# --- 3. Routes ---

@app.route('/')
def home():
    """Public Home Page."""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Public Registration with 10-digit validation and Success Message."""
    if request.method == 'POST':
        phone = request.form.get('phone')
        ch_mobile = request.form.get('ch_mobile')
        
        # 10-Digit Validation
        if len(phone) != 10 or len(ch_mobile) != 10:
            flash('Error: Phone numbers must be exactly 10 digits!')
            return redirect(url_for('register'))

        # Generate Custom VPL ID
        last_player = Player.query.order_by(Player.id.desc()).first()
        next_id_num = 1 if not last_player else last_player.id + 1
        formatted_vpl_id = f"VPL-{next_id_num:03d}"

        # Handle Photo Upload & Rename
        file = request.files.get('photo')
        if file:
            ext = file.filename.rsplit('.', 1)[1].lower()
            new_photo_filename = f"{formatted_vpl_id}.{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_photo_filename))
        else:
            flash('Photo is required.')
            return redirect(url_for('register'))

        try:
            new_player = Player(
                vpl_id=formatted_vpl_id,
                full_name=request.form.get('full_name'),
                age=request.form.get('age'),
                phone=phone,
                ch_reg_same=request.form.get('ch_reg'),
                ch_mobile=ch_mobile,
                ch_name=request.form.get('ch_name'),
                current_team=request.form.get('current_team'),
                prev_team=request.form.get('prev_team'),
                role=request.form.get('role'),
                style=request.form.get('style'),
                photo=new_photo_filename,
                shirt_name=request.form.get('shirt_name'),
                shirt_number=request.form.get('shirt_number'),
                shirt_size=request.form.get('shirt_size'),
                sleeves=request.form.get('sleeves'),
                comments=request.form.get('comments')
            )
            db.session.add(new_player)
            db.session.commit()
            flash('Registration completed successfully!')
            return redirect(url_for('register'))
        except Exception as e:
            db.session.rollback()
            flash(f'Database Error: {str(e)}')
            return redirect(url_for('register'))

    return render_template('register.html')

# --- 4. Admin Security Section ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin Login Portal."""
    if request.method == 'POST':
        # Default Admin Credentials
        if request.form.get('username') == 'admin' and request.form.get('password') == 'Siva2124':
            session['logged_in'] = True
            flash('Welcome, Admin!')
            return redirect(url_for('players'))
        else:
            flash('Invalid Username or Password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/players')
def players():
    """Secure Admin-Only Player List."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    all_players = Player.query.all()
    return render_template('players.html', players=all_players)

@app.route('/export_players')
def export_players():
    """Secure Route to Download Excel (CSV) Data."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    players = Player.query.all()
    si = StringIO()
    cw = csv.writer(si)
    
    # Column Headers
    cw.writerow([
        'VPL ID', 'Full Name', 'Age', 'Phone', 'CH Same?', 'CH Mobile', 
        'CH Name', 'Current Team', 'Prev Team', 'Role', 'Style', 
        'Shirt Name', 'Shirt No', 'Size', 'Sleeves', 'Comments'
    ])
    
    # Row Data
    for p in players:
        cw.writerow([
            p.vpl_id, p.full_name, p.age, p.phone, p.ch_reg_same, p.ch_mobile, 
            p.ch_name, p.current_team, p.prev_team, p.role, p.style, 
            p.shirt_name, p.shirt_number, p.shirt_size, p.sleeves, p.comments
        ])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=VPL_Season2_Registrations.csv"
    output.headers["Content-type"] = "text/csv"
    return output

if __name__ == '__main__':
    app.run(debug=True)