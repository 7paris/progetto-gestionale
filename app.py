from flask import Flask, request, redirect, url_for, render_template, send_from_directory, session
import os, shutil
from functools import wraps
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask.sessions import SecureCookieSessionInterface

# --- FIX Flask 2.3+ partitioned bug ---
class FixedSessionInterface(SecureCookieSessionInterface):
    def save_session(self, *args, **kwargs):
        if 'partitioned' in kwargs:
            kwargs.pop('partitioned')
        super().save_session(*args, **kwargs)

# --- APP ---
app = Flask(__name__)
app.secret_key = 'una_chiave_segretissima'
app.session_interface = FixedSessionInterface()  # applica il fix

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- DECORATOR LOGIN REQUIRED ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# --- LOGIN ---
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    error=None
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT password_hash, is_admin FROM users WHERE username=?', (username,))
        res = c.fetchone()
        conn.close()
        if res and check_password_hash(res[0], password):
            session['logged_in']=True
            session['username']=username
            session['is_admin'] = bool(res[1])
            return redirect(url_for('index'))
        else:
            error="Username o password sbagliati"
    return render_template('login.html', error=error)

@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- FILES & CARTELLE ---
@app.route('/files')
@login_required
def index():
    folders = [f for f in os.listdir(UPLOAD_FOLDER) if os.path.isdir(os.path.join(UPLOAD_FOLDER, f))]
    return render_template('index.html', folders=folders, admin=session.get('is_admin', False))

@app.route('/folder/<path:folder_path>', methods=['GET','POST'])
@login_required
def view_folder(folder_path):
    folder_full_path = os.path.join(UPLOAD_FOLDER, folder_path)
    os.makedirs(folder_full_path, exist_ok=True)

    # Upload files via drag & drop
    if request.method=='POST':
        for file in request.files.getlist('file'):
            if file:
                file.save(os.path.join(folder_full_path, file.filename))
        return redirect(url_for('view_folder', folder_path=folder_path))

    # Lista file e cartelle
    items = []
    for f in os.listdir(folder_full_path):
        path = os.path.join(folder_full_path, f)
        items.append({
            'name': f,
            'type': 'folder' if os.path.isdir(path) else 'file'
        })

    return render_template('folder.html', items=items, current_path=folder_path)

# --- CREATE / RENAME / DELETE ---
@app.route('/create_folder', defaults={'folder_path':''}, methods=['POST'])
@app.route('/create_folder/<path:folder_path>', methods=['POST'])
@login_required
def create_folder(folder_path):
    name = request.form['folder_name'].strip()
    if name:
        path = os.path.join(UPLOAD_FOLDER, folder_path, name)
        os.makedirs(path, exist_ok=True)
    return ('',204)

@app.route('/rename_folder/<path:folder_path>', methods=['POST'])
@login_required
def rename_folder(folder_path):
    old = request.form['old_name'].strip()
    new = request.form['new_name'].strip()
    old_path = os.path.join(UPLOAD_FOLDER, folder_path, old)
    new_path = os.path.join(UPLOAD_FOLDER, folder_path, new)
    if os.path.exists(old_path) and new:
        os.rename(old_path, new_path)
    return ('',204)

@app.route('/delete_folder/<path:folder_path>', methods=['POST'])
@login_required
def delete_folder(folder_path):
    folder_name = request.form['folder_name'].strip()
    path = os.path.join(UPLOAD_FOLDER, folder_path, folder_name)
    if os.path.exists(path):
        shutil.rmtree(path)
    return ('',204)

@app.route('/rename_file/<path:folder_path>', methods=['POST'])
@login_required
def rename_file(folder_path):
    old = request.form.get('old_name', '').strip()
    new = request.form.get('new_name', '').strip()
    folder_full_path = os.path.join(UPLOAD_FOLDER, folder_path)
    old_path = os.path.join(folder_full_path, old)
    new_path = os.path.join(folder_full_path, new)
    if os.path.exists(old_path) and new:
        os.rename(old_path, new_path)
        return ('',204)
    return ('File non valido', 400)

@app.route('/delete_file/<path:folder_path>', methods=['POST'])
@login_required
def delete_file(folder_path):
    file_name = request.form['file_name'].strip()
    file_path = os.path.join(UPLOAD_FOLDER, folder_path, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
    return ('',204)

@app.route('/uploads/<path:file_path>')
@login_required
def uploaded_file(file_path):
    folder_path, filename = os.path.split(file_path)
    return send_from_directory(os.path.join(UPLOAD_FOLDER, folder_path), filename, as_attachment=True)

# --- ADMIN USER MANAGEMENT ---
@app.route('/manage_users')
@login_required
def manage_users():
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT username, is_admin FROM users")
    users = [{"username": row[0], "is_admin": row[1]} for row in c.fetchall()]
    conn.close()
    return render_template('manage_users.html', users=users)


@app.route('/create_user', methods=['POST'])
@login_required
def create_user():
    if not session.get('is_admin'):
        return ('',403)
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    if username and password:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        password_hash = generate_password_hash(password)
        c.execute('INSERT INTO users (username,password_hash,is_admin) VALUES (?,?,0)', (username,password_hash))
        conn.commit()
        conn.close()
    return redirect(url_for('manage_users'))


if __name__=='__main__':
    app.run(debug=True)
