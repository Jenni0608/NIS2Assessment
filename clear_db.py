import sqlite3

def clear_db():
    conn = sqlite3.connect('assessment_results.db')
    c = conn.cursor()

    # Drop the feedback table if it exists
    c.execute('DROP TABLE IF EXISTS feedback')

    # Recreate the feedback table with the correct schema
    c.execute('''
        CREATE TABLE feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            familiarity TEXT,
            role TEXT,
            experience TEXT,
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

    # Drop the results table if it exists
    c.execute('DROP TABLE IF EXISTS results')

    # Recreate the results table with the correct schema
    c.execute('''
        CREATE TABLE results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            total_score INTEGER,
            compliance_percentage REAL,
            details TEXT,
            consent TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print("Database cleared and tables recreated.")

if __name__ == '__main__':
    clear_db()
