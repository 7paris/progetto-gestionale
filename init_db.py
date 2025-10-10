# init_db.py
import sqlite3
from werkzeug.security import generate_password_hash

# Connessione al database
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Creazione tabella utenti
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
)
''')

# Inserimento utente (sostituisci con i tuoi dati)
username = 'mio_username'
password = 'mia_password'  # password in chiaro
password_hash = generate_password_hash(password)

try:
    c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
    conn.commit()
    print("Utente creato con successo!")
except sqlite3.IntegrityError:
    print("Utente già presente nel database.")

conn.close()
