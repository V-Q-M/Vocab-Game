import duckdb

conn = duckdb.connect("vocabulary.db")

def initiate_table():
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vocabulary (
            language TEXT,
            word TEXT,
            translation TEXT,
            PRIMARY KEY (language, word)
        );
    """)

# Call the table creation at startup
initiate_table()

def add_vocabulary(language, words, translations):
    data = [(language, w, t) for w, t in zip(words, translations)]
    conn.executemany("""
        INSERT OR IGNORE INTO vocabulary (language, word, translation)
        VALUES (?, ?, ?)
    """, data)


def fetch_vocabulary(language):
    vocab = conn.execute("""
        SELECT word, translation FROM vocabulary WHERE language = (?)
    """, (language,))
    return vocab.fetchall()



