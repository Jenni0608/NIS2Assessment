import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('assessment_results.db')

# Create a cursor object
cursor = conn.cursor()

# Use PRAGMA table_info() to get information about the table
cursor.execute("PRAGMA table_info(feedback)")

# Fetch all rows from the cursor to get information about each column
columns_info = cursor.fetchall()

# Print the schema of the table
print("Table Schema:")
for column in columns_info:
    column_id, column_name, data_type, not_null, default_value, primary_key = column
    print(f"Column ID: {column_id}, Name: {column_name}, Type: {data_type}, Not Null: {not_null}, Default Value: {default_value}, Primary Key: {primary_key}")

# sample_data = {'familiarity': 'intermediate_knowledge', 'role': 'data_protection_officer', 'experience': '15_20', 'location': 'Ireland', 'use_frequently': 'Neutral', 'complexity': 'Neutral', 'ease_of_use': 'Neutral', 'need_support': 'Neutral', 'integration': 'Neutral', 'inconsistency': 'Neutral', 'learn_quickly': 'Neutral', 'cumbersome': 'Neutral', 'confidence': 'Neutral', 'learning_curve': 'Neutral', 'navigation': 'Neutral', 'relevance': 'Neutral', 'comprehensive': 'Neutral', 'useful_recommendations': 'Neutral', 'overall_satisfaction': 'Not specified', 'recommend': '5', 'best_feature': 'dadaw', 'biggest_difficulty': 'dawdawd', 'missing_feature': 'dadwadwa', 'additional_comments': 'wadwadaw'}

# columns = ', '.join(sample_data.keys())
# placeholders = ', '.join(['?'] * len(sample_data))

# # Prepare the INSERT statement
# sql = f"INSERT INTO feedback ({columns}) VALUES ({placeholders})"
# print(sql)
# cursor.execute(sql, tuple(sample_data.values()))
# conn.commit()

# Close the connection
conn.close()