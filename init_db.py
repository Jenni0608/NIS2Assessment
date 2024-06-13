import sqlite3
import os

def delete_db():
    if os.path.exists('assessment_results.db'):
        os.remove('assessment_results.db')
        print("Database file deleted.")
    else:
        print("Database file does not exist.")


# Initialise the Database and table to store the users inputs.
def init_db():
    print(sqlite3.version)
    conn = sqlite3.connect('assessment_results.db')  # This will create the database file
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE,
            total_score INTEGER,
            compliance_percentage REAL,
            details TEXT,
            consent TEXT,  
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            familiarity TEXT,
            role TEXT,
            experience TEXT,
            location TEXT,
            use_frequently TEXT,
            complexity TEXT,
            ease_of_use TEXT,
            need_support TEXT,
            integration TEXT,
            inconsistency TEXT,
            learn_quickly TEXT,
            cumbersome TEXT,
            confidence TEXT,
            learning_curve TEXT,
            navigation TEXT,
            relevance TEXT,
            comprehensive TEXT,
            useful_recommendations TEXT,
            overall_satisfaction TEXT,
            recommend TEXT,
            best_feature TEXT,
            biggest_difficulty TEXT,
            missing_feature TEXT,
            additional_comments TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database and table initialised.")
