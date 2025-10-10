import sqlite3
from werkzeug.security import generate_password_hash

# Connessione al database (crea il file se non esiste)
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Creazione tabella utenti (solo se non esiste)
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
)
''')

# Inserisci il tuo utente
username = input("Inserisci il tuo username: ")
password = input("Inserisci la tua password: ")
password_hash = generate_password_hash(password)

try:
    c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
    conn.commit()
    print(f"Utente '{username}' creato con successo!")
except sqlite3.IntegrityError:
    print("Errore: utente già presente nel database.")

conn.close()
