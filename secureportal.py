from flask import Flask, request, redirect, url_for, render_template_string, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os, re, logging

# Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'replace_with_your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///secureportal.db'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload
ALLOWED_EXTENSIONS = {'pdf'}

db = SQLAlchemy(app)
logging.basicConfig(level=logging.INFO)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'user' or 'admin'
    documents = db.relationship('Document', backref='uploader', lazy=True)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Helper Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

def valid_password(password):
    # Must be at least 8 characters, one uppercase, one lowercase, one special character.
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[\W_]', password):
        return False
    return True

# Error Handlers - Generic error messages
@app.errorhandler(Exception)
def handle_exception(e):
    logging.error("Exception occurred", exc_info=e)
    return render_template_string('''
        <!doctype html>
        <html lang="en">
        <head><meta charset="utf-8"><title>Error</title></head>
        <body>
            <h2>An error occurred</h2>
            <p>Please try again later.</p>
            <p><a href="{{ url_for('index') }}">Home</a></p>
        </body>
        </html>
    '''), 500

@app.errorhandler(404)
def not_found_error(e):
    return render_template_string('''
        <!doctype html>
        <html lang="en">
        <head><meta charset="utf-8"><title>Not Found</title></head>
        <body>
            <h2>Page not found</h2>
            <p>The page you are looking for does not exist.</p>
            <p><a href="{{ url_for('index') }}">Home</a></p>
        </body>
        </html>
    '''), 404

# Routes

# Home page
@app.route('/')
def index():
    user = current_user()
    if user:
        return render_template_string('''
            <!doctype html>
            <html lang="en">
            <head>
              <meta charset="utf-8">
              <title>SecurePortal Home</title>
            </head>
            <body>
              <h2>Welcome {{ user.username }} ({{ user.role }})</h2>
              <p><a href="{{ url_for('upload') }}">Upload Document</a></p>
              <p><a href="{{ url_for('documents') }}">View Documents</a></p>
              <p><a href="{{ url_for('logout') }}">Logout</a></p>
            </body>
            </html>
        ''', user=user)
    return render_template_string('''
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <title>SecurePortal</title>
        </head>
        <body>
          <h2>SecurePortal</h2>
          <p><a href="{{ url_for('login') }}">Login</a></p>
          <p><a href="{{ url_for('register') }}">Register</a></p>
        </body>
        </html>
    ''')

# Registration route (HTML and JavaScript for client-side validation)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        if not username or not password:
            flash('Username and password required.')
            return redirect(url_for('register'))
        if not valid_password(password):
            flash('Password must be at least 8 characters long, include one uppercase letter, one lowercase letter, and one special character.')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('register'))
        password_hash = generate_password_hash(password)
        new_user = User(username=username, password_hash=password_hash, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please login.')
        return redirect(url_for('login'))
    return render_template_string('''
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <title>Register</title>
          <script>
            function validatePassword() {
                var pwd = document.getElementById("password").value;
                var msg = "";
                if(pwd.length < 8){
                  msg = "Password must be at least 8 characters.";
                } else if(!(/[A-Z]/.test(pwd))){
                  msg = "Password must include at least one uppercase letter.";
                } else if(!(/[a-z]/.test(pwd))){
                  msg = "Password must include at least one lowercase letter.";
                } else if(!(/[\W_]/.test(pwd))){
                  msg = "Password must include at least one special character.";
                }
                document.getElementById("pwdMsg").innerText = msg;
                return msg === "";
            }
          </script>
        </head>
        <body>
          <h2>Register</h2>
          <form method="post" onsubmit="return validatePassword();">
              Username: <input type="text" name="username" required><br>
              Password: <input type="password" name="password" id="password" required onkeyup="validatePassword();"><br>
              <span id="pwdMsg" style="color:red;"></span><br>
              Role:
              <select name="role">
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
              </select><br>
              <input type="submit" value="Register">
          </form>
          <p><a href="{{ url_for('index') }}">Home</a></p>
        </body>
        </html>
    ''')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash('Logged in successfully.')
            return redirect(url_for('index'))
        flash('Invalid credentials.')
        return redirect(url_for('login'))
    return render_template_string('''
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <title>Login</title>
        </head>
        <body>
          <h2>Login</h2>
          <form method="post">
              Username: <input type="text" name="username" required><br>
              Password: <input type="password" name="password" required><br>
              <input type="submit" value="Login">
          </form>
          <p><a href="{{ url_for('index') }}">Home</a></p>
        </body>
        </html>
    ''')

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out.')
    return redirect(url_for('index'))

# Document upload route (Only PDF allowed)
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    user = current_user()
    if not user:
        flash('Please log in to upload documents.')
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file provided.')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file.')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            new_doc = Document(filename=filename, uploader_id=user.id)
            db.session.add(new_doc)
            db.session.commit()
            flash('File successfully uploaded.')
            return redirect(url_for('documents'))
        else:
            flash('Only PDF files are allowed.')
            return redirect(request.url)
    return render_template_string('''
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <title>Upload Document</title>
        </head>
        <body>
          <h2>Upload Document (PDF only)</h2>
          <form method="post" enctype="multipart/form-data">
              <input type="file" name="file" accept="application/pdf" required><br>
              <input type="submit" value="Upload">
          </form>
          <p><a href="{{ url_for('index') }}">Home</a></p>
        </body>
        </html>
    ''')

# Documents viewing route with least privilege access
@app.route('/documents')
def documents():
    user = current_user()
    if not user:
        flash('Please log in to view documents.')
        return redirect(url_for('login'))
    if user.role == "admin":
        docs = Document.query.all()
    else:
        docs = Document.query.filter_by(uploader_id=user.id).all()
    return render_template_string('''
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <title>Documents</title>
        </head>
        <body>
          <h2>Uploaded Documents</h2>
          <ul>
              {% for doc in docs %}
              <li>{{ doc.filename }} - 
                  <a href="{{ url_for('download_file', filename=doc.filename) }}">Download</a>
              </li>
              {% else %}
              <li>No documents found.</li>
              {% endfor %}
          </ul>
          <p><a href="{{ url_for('index') }}">Home</a></p>
        </body>
        </html>
    ''', docs=docs)

# Download route
@app.route('/uploads/<filename>')
def download_file(filename):
    user = current_user()
    if not user:
        flash('Please log in to download files.')
        return redirect(url_for('login'))
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=False)