create TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    firstname TEXT,
    name TEXT,
    birthdate DATE,
    email TEXT,
    salt TEXT,
    hash TEXT,
    confirmed BOOLEAN DEFAULT FALSE,
    admin BOOLEAN DEFAULT FALSE
);

create TABLE sessions (
    session_id TEXT PRIMARY KEY,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

create TABLE commentaires (
    commentaire_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE,
    est_satisfait INTEGER,
    commentaire TEXT,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

create TABLE trajets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE,
    lat TEXT,
    lng TEXT,
    nav TEXT,
    dataTrajets TEXT,
    rayon TEXT,
    poly TEXT,
    travelAd TEXT,
    liste TEXT,
    weather TEXT,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
