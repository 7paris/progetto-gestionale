from flask import Flask, request, redirect, url_for, render_template, send_from_directory, session
import os, shutil, sqlite3
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'una_chiave_segretissima'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# -----------------------
# Decoratore login
# -----------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# -----------------------
# Utility per percorsi
# -----------------------
def get_abs_path(subpath=None):
    """Restituisce percorso assoluto della cartella root o sottocartella."""
    if not subpath or subpath.strip() == "":
        return os.path.abspath(UPLOAD_FOLDER)
    return os.path.abspath(os.path.join(UPLOAD_FOLDER, subpath))

# -----------------------
# LOGIN
# -----------------------
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT password_hash FROM users WHERE username=?', (username,))
        res = c.fetchone()
        conn.close()
        if res and check_password_hash(res[0], password):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = "Username o password sbagliati"
    return render_template('login.html', error=error)

@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))

# -----------------------
# Pagina principale (root)
# -----------------------
@app.route('/files')
@login_required
def index():
    base_path = get_abs_path()
    items = []
    for item in os.listdir(base_path):
        full_path = os.path.join(base_path, item)
        item_type = 'folder' if os.path.isdir(full_path) else 'file'
        items.append({'name': item, 'type': item_type})
    return render_template('folder.html', items=items, current_path='')

# -----------------------
# Sottocartelle e files
# -----------------------
@app.route('/folder/<path:subpath>', methods=['GET','POST'])
@login_required
def view_folder(subpath):
    abs_path = get_abs_path(subpath)
    os.makedirs(abs_path, exist_ok=True)

    if request.method == 'POST':
        for file in request.files.getlist('file'):
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(abs_path, filename))
        return redirect(url_for('view_folder', subpath=subpath))

    items = []
    for item in os.listdir(abs_path):
        full_path = os.path.join(abs_path, item)
        item_type = 'folder' if os.path.isdir(full_path) else 'file'
        items.append({'name': item, 'type': item_type})

    return render_template('folder.html', items=items, current_path=subpath)

# -----------------------
# Creazione cartella
# -----------------------
@app.route('/create_folder', methods=['POST'])
@login_required
def create_root_folder():
    folder_name = request.form.get('folder_name', '').strip()
    abs_path = get_abs_path()
    if folder_name:
        os.makedirs(os.path.join(abs_path, secure_filename(folder_name)), exist_ok=True)
    return ('', 204)

@app.route('/create_folder/<path:subpath>', methods=['POST'])
@login_required
def create_folder(subpath):
    folder_name = request.form.get('folder_name', '').strip()
    abs_path = get_abs_path(subpath)
    if folder_name:
        os.makedirs(os.path.join(abs_path, secure_filename(folder_name)), exist_ok=True)
    return ('', 204)

# -----------------------
# Rinomina cartella
# -----------------------
@app.route('/rename_folder', methods=['POST'])
@login_required
def rename_root_folder():
    old = request.form.get('old_name', '').strip()
    new = request.form.get('new_name', '').strip()
    abs_path = get_abs_path()
    old_path = os.path.join(abs_path, old)
    new_path = os.path.join(abs_path, secure_filename(new))
    if os.path.exists(old_path) and new:
        os.rename(old_path, new_path)
    return ('', 204)

@app.route('/rename_folder/<path:subpath>', methods=['POST'])
@login_required
def rename_folder(subpath):
    old = request.form.get('old_name', '').strip()
    new = request.form.get('new_name', '').strip()
    abs_path = get_abs_path(subpath)
    old_path = os.path.join(abs_path, old)
    new_path = os.path.join(abs_path, secure_filename(new))
    if os.path.exists(old_path) and new:
        os.rename(old_path, new_path)
    return ('', 204)

# -----------------------
# Elimina cartella
# -----------------------
@app.route('/delete_folder', methods=['POST'])
@login_required
def delete_root_folder():
    folder_name = request.form.get('folder_name', '').strip()
    abs_path = get_abs_path()
    folder_path = os.path.join(abs_path, folder_name)
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    return ('', 204)

@app.route('/delete_folder/<path:subpath>', methods=['POST'])
@login_required
def delete_folder(subpath):
    folder_name = request.form.get('folder_name', '').strip()
    abs_path = get_abs_path(subpath)
    folder_path = os.path.join(abs_path, folder_name)
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    return ('', 204)

# -----------------------
# Rinomina file
# -----------------------
@app.route('/rename_file', methods=['POST'])
@login_required
def rename_root_file():
    old = request.form.get('old_name', '').strip()
    new = request.form.get('new_name', '').strip()
    abs_path = get_abs_path()
    old_path = os.path.join(abs_path, old)
    new_path = os.path.join(abs_path, secure_filename(new))
    if os.path.exists(old_path) and new:
        os.rename(old_path, new_path)
    return ('', 204)

@app.route('/rename_file/<path:subpath>', methods=['POST'])
@login_required
def rename_file(subpath):
    old = request.form.get('old_name', '').strip()
    new = request.form.get('new_name', '').strip()
    abs_path = get_abs_path(subpath)
    old_path = os.path.join(abs_path, old)
    new_path = os.path.join(abs_path, secure_filename(new))
    if os.path.exists(old_path) and new:
        os.rename(old_path, new_path)
    return ('', 204)

# -----------------------
# Elimina file
# -----------------------
@app.route('/delete_file', methods=['POST'])
@login_required
def delete_root_file():
    file_name = request.form.get('file_name', '').strip()
    abs_path = get_abs_path()
    file_path = os.path.join(abs_path, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
    return ('', 204)

@app.route('/delete_file/<path:subpath>', methods=['POST'])
@login_required
def delete_file(subpath):
    file_name = request.form.get('file_name', '').strip()
    abs_path = get_abs_path(subpath)
    file_path = os.path.join(abs_path, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
    return ('', 204)

# -----------------------
# Download / Anteprima file
# -----------------------
@app.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    abs_path = get_abs_path(os.path.dirname(filename))
    file_name = os.path.basename(filename)
    return send_from_directory(abs_path, file_name, as_attachment=False)

# -----------------------
# Avvio app
# -----------------------
if __name__=='__main__':
    app.run(debug=True)
