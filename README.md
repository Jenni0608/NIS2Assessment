# Overview of the NIS2 Regulatory Assessment Tool

The Regulatory Assessment Tool, developed in Python, leverages a unified knowledge model (ontology stored in GraphDB) to evaluate compliance with the NIS2 Cybersecurity risk-management measures outlined in Article 21. The tool dynamically retrieves multiple-choice questions (MCQs) from the ontology stored in GraphDB, facilitating a comprehensive evaluation of compliance with the NIS2 directive.

# Purpose and Scope

The primary objective of this tool is to enable organisations to conduct an in-depth NIS2 gap analysis using the ISO 27001:2022 framework as a benchmark. The tool systematically maps specific ISO 27001:2022 controls and the essential security controls recommended by the European Union Agency for Cybersecurity (ENISA) against the ten NIS2 Cybersecurity risk-management measures detailed in Article 21. This mapping ensures a thorough and standardised approach to assessing and enhancing cybersecurity compliance.

# Installation

System Requirements
• Python 3.7 or higher
• Flask
• SPARQLWrapper
• ReportLab
• Matplotlib
• SQLite3
• Flask-Session
• A running instance of GraphDB

Installation Steps:

1. Clone the repository:

- git clone https://github.com/Jenni0608/NIS2Assessment.git
- cd NIS2Addessment

2. Create a virtual environment:

- python -m venv venv
- source venv/bin/activate

- On Windows: venv\Scripts\activate

3. Install the required packages:

- pip install -r requirements.txt

4. Run the application in the dev mode:

- flask --app main run

Configuration:
Setting up the SPARQL Endpoint
Ensure that the GraphDB instance is running and accessible. Update the SPARQL endpoint URL in the `RegulatoryAssessmentTool` class within `main.py`:
self.sparql = SPARQLWrapper("http://localhost:8080/repositories/NIS2Ontology")

Configuring the Flask Application
Ensure Flask is set up correctly by configuring the secret key:
secret_key = binascii.hexlify(os.urandom(24)).decode()
app = Flask(**name**, static_url_path='/static')
app.secret_key = secret_key

Usage:
Starting the Application
Run the Flask application:
flask run
Access the application in the web browser at `http://127.0.0.1:5000`.

Navigating the Welcome Page:
The welcome page introduces the tool and provides an overview of NIS2 requirements. Click "Begin Assessment" to start the compliance assessment.

Conducting an Assessment:
Answer the multiple-choice questions presented. Each question is dynamically fetched from the ontology.

Viewing Results:
After completing the assessment, view detailed results categorized by implementation status and article. Recommendations are provided for partial or non-implemented measures.

Generating Reports:
Click "Download Report" on the results page to generate a PDF report of the assessment, including scores, compliance percentage, and recommendations.

User Feedback:
Users can provide feedback through a feedback form available after the assessment. The feedback form includes questions on usability, content relevance, and overall satisfaction.

Code Overview:
main.py: Explanation of the Main Application File
Class: RegulatoryAssessmentTool
`__init__`: Initializes the SPARQL endpoint and question label scores.
`run_sparql_query`: Executes a SPARQL query and returns the results.
`get_answer_definition`: Retrieves the definition for a given answer.
`get_article_info`: Fetches information for a specific article.
`get_article_label`: Gets the article label for a given MCQ number.
`get_question_score`: Returns the score for a question label.
`get_question_data`: Retrieves question and answer data for a given MCQ number.
`get_recommendation`: Gets recommendations for a given MCQ number.
`get_article_label_for_question`: Fetches the article label and definition for a given MCQ number.

Flask Routes
`/welcome`: Renders the welcome page.
`/`: Renders the index page, starting the quiz if not already started.
`/begin_assessment`: Starts the assessment.
`/submit_answer`: Submits an answer and fetches the next question.
`/get_next_question`: Fetches the next question's data.
`/complete`: Renders the completion page with scores and charts.
`/results`: Renders detailed results and recommendations.
`/download_report`: Generates and downloads the PDF report.
‘/consent’: Renders the consent form page and handles user consent.
‘/feedback’: Renders the user feedback form.
‘/submit_feedback’: Submits user feedback to the database.
‘/view_feedback’: Displays all submitted feedback.
‘/goodbye’: Renders the goodbye page if the user does not consent.

Utility Functions
`fetch_mcq_numbers`: Fetches and sorts MCQ numbers from the ontology.
`add_page_number`: Adds page numbers to the PDF report.
`create_pie_chart`: Creates and saves a pie chart of the question breakdown.

Customization
How to Modify the Assessment Questions
Update the ontology in GraphDB with new questions and answers. Ensure the labels and definitions follow the same structure.

Adding New SPARQL Queries
Add new methods in the `RegulatoryAssessmentTool` class to handle additional SPARQL queries as needed.

Customizing the Report Layout
Modify the `download_report` route in `main.py` to change the layout, styles, and content of the PDF report.

# Application Deployment

- The app can be deployed using `gunicorn`. The defautl configuration file can be found [here](/gunicorn_config.py).
- Generate a secret key for Session. Make sure you are in env and run: `python -c 'import secrets; print(secrets.token_hex())'`
- Update the secret_key variable in the main.py.
- Rn the app in production mode: `gunicorn --config gunicorn_config.py main:app`

# Troubleshooting

Common Issues and Solutions
SPARQL Query Errors: Ensure the SPARQL queries are correctly formatted and the endpoint is accessible.
Flask Application Errors: Check for missing or misconfigured routes and templates.

Logging and Debugging:
Enable logging in `main.py`:
logging.basicConfig(level=logging.DEBUG)
Check the console output for detailed logs.

# Contact

For support or to contribute to this project, contact Jenni Parry at jenni.parry@ucdconnect.ie.
