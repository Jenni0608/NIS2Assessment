import urllib

from flask import Flask, render_template, request, session, redirect, url_for, send_file, jsonify
import sqlite3
import json
import os
import binascii
import logging
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime
from io import BytesIO
from collections import Counter
from matplotlib.ticker import MaxNLocator

matplotlib.use('Agg')

from SPARQLWrapper import SPARQLWrapper, JSON
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.units import mm


# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Generate a secret key for the Flask session
secret_key = binascii.hexlify(os.urandom(24)).decode()
print(secret_key)

# Initialize Flask app
app = Flask(__name__, static_url_path='/static')
app.secret_key = secret_key


# Database initialisation (**Matches init_db.py)
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

init_db()


# Class to handle regulatory assessment tool logic
class RegulatoryAssessmentTool:
    def __init__(self):

        endpoint_url = "http://localhost:8080/repositories/NIS2Ontology"
        username = "admin"
        password = "hBxGF3PtJMUgNePB"

        # Initialize SPARQLWrapper with the endpoint URL
        self.sparql = SPARQLWrapper(endpoint_url)
        # Mapping of question labels to scores
        self.question_label_scores = {
            '(i)': 0,
            '(ii)': 1,
            '(iii)': 2
        }

    def run_sparql_query(self, query):
        """Runs a SPARQL query and returns the results in JSON format."""
        logging.debug(f"Running SPARQL query: {query}")
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        try:
            results = self.sparql.query().convert()
            logging.debug(f"SPARQL query results: {results}")
            return results
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            logging.error(f"Error running SPARQL query: {e}")
            return None

    def get_answer_definition(self, question_number, answer_label):
        print("In... get_answer_definition")
        logging.debug(f"answer_label: {answer_label}")
        """Fetches the definition of an answer given a question number and answer label."""
        query = f'''
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX assess: <http://JP_ontology.org/assessment/>
        
        SELECT ?answerDef
        WHERE {{
          ?answer rdf:type assess:MCQ.{question_number} ;
                  skos:altLabel ?answerLabel ;
                  skos:definition ?answerDef .
          FILTER (str(?answerLabel) = '{answer_label}')
        }}
        '''
        logging.debug(f"Generated SPARQL query for get_answer_definition: {query}")
        results = self.run_sparql_query(query)
        print("Leaving... get_answer_definition")
        if results['results']['bindings']:
            return results['results']['bindings'][0]['answerDef']['value']
        else:
            return None

    def get_article_info(self, article_label):
        print("In... get_article_info")
        """Fetches information about an article given its label."""
        query = f'''
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX dct: <http://purl.org/dc/terms/>
        SELECT ?prefLabel ?definition ?source
        WHERE {{
            <http://JP_ontology.org/nis2v/{article_label}> skos:prefLabel ?prefLabel ;
                                                           skos:definition ?definition ;
                                                           dct:source ?source .
            FILTER (LANG(?prefLabel) = "en")
            FILTER (LANG(?definition) = "en")
        }}
        '''
        logging.debug(f"Generated SPARQL query for get_article_info: {query}")
        results = self.run_sparql_query(query)
        return results

    def get_article_label(self, mcq_number):
        """Fetches the article label for a given MCQ number."""
        article_info = self.get_article_label_for_question(mcq_number)
        if article_info:
            return article_info['articleLabel']
        else:
            return 'Unknown Article'

    def get_question_score(self, question_label):
        """Returns the score for a given question label."""
        return self.question_label_scores.get(question_label, 0)

    def get_question_data(self, mcq_number):
        """Fetches data for a specific question, including the question text, answers, and related article."""
        print("In... get_question_data")
        question_data = self.run_sparql_query(f'''
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        SELECT ?questionLabel ?questionDefinition
        WHERE {{
          ?concept skos:altLabel "MCQ.{mcq_number}"@en ;
                   skos:prefLabel ?questionLabel ;
                   skos:definition ?questionDefinition .
        }}
        ''')

        answers_data = self.run_sparql_query(f'''
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX nis2v: <http://JP_ontology.org/nis2v/>
        PREFIX assess: <http://JP_ontology.org/assessment/>
        SELECT ?answerLabel ?answerDef ?answerPrefLabel
        WHERE {{
          ?answer a <http://JP_ontology.org/assessment/MCQ.{mcq_number}> ;
                  skos:altLabel ?answerLabel ;
                  skos:definition ?answerDef ;
                  skos:prefLabel ?answerPrefLabel .
        }}
        ORDER BY ?answerLabel
        ''')

        article_label = self.get_article_label(mcq_number)
        article_info = self.get_article_info(article_label)

        question = {
            'label': 'No question available',
            'definition': '',
            'score': 0
        }
        if question_data['results']['bindings']:
            question_label = question_data['results']['bindings'][0]['questionLabel']['value']
            question_score = self.get_question_score(question_label)
            question = {
                'label': question_label,
                'definition': question_data['results']['bindings'][0]['questionDefinition']['value'],
                'score': question_score
            }

        answers = []
        if answers_data['results']['bindings']:
            answers = [{'answerLabel': item['answerLabel']['value'],
                        'answerDef': item['answerDef']['value'],
                        'answerPrefLabel': item['answerPrefLabel']['value'],
                        'score': self.get_question_score(item['answerLabel']['value'])}
                       for item in answers_data['results']['bindings']]

        article_details = {'prefLabel': '', 'definition': '', 'source': ''}
        if article_info['results']['bindings']:
            article_details = {
                'prefLabel': article_info['results']['bindings'][0]['prefLabel']['value'],
                'definition': article_info['results']['bindings'][0]['definition']['value'],
                'source': article_info['results']['bindings'][0]['source']['value']
            }

        return {
            'question': question,
            'answers': answers,
            'article_label': article_label,
            'article_details': article_details,
            'question_number': mcq_number
        }

    def get_recommendation(self, mcq_number):
        """Fetches the recommendation for a given MCQ number."""
        print("In... get_recommendation")
        query = f'''
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX dct: <http://purl.org/dc/terms/>
        PREFIX nis2v: <http://JP_ontology.org/nis2v#>
        
        SELECT ?control ?recommendation
        WHERE {{
          ?question skos:altLabel "MCQ.{mcq_number}"@en ;
                    nis2v:relatedToControl ?control .
          ?control skos:definition ?recommendation .
        }}
        '''
        logging.debug(f"Generated SPARQL query for get_recommendation: {query}")
        results = self.run_sparql_query(query)
        print("Leaving... get_recommendation")
        if results['results']['bindings']:
            return results['results']['bindings'][0]['recommendation']['value']
        else:
            return "No recommendation available."

    def get_article_label_for_question(self, mcq_number):
        """Fetches the article label related to a specific MCQ number."""
        print("In... get_article_label_for_question")
        query = f'''
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX dct: <http://purl.org/dc/terms/>
        
        SELECT ?articleLabel ?definition
        WHERE {{
          ?question skos:altLabel "MCQ.{mcq_number}"@en ;
                 dct:subject ?article .
          ?article skos:prefLabel ?articleLabel ;
                   skos:definition ?definition .
        }}
        '''
        logging.debug(f"Generated SPARQL query for get_article_label_for_question: {query}")
        results = self.run_sparql_query(query)
        logging.debug(f"SPARQL query results for get_article_label_for_question: {results}")

        if results['results']['bindings']:
            binding = results['results']['bindings'][0]
            if 'articleLabel' in binding and 'definition' in binding:
                return {
                    'articleLabel': binding['articleLabel']['value'],
                    'definition': binding['definition']['value']
             }
            else:
                return None
        else:
            return None

# Fetch MCQ numbers
import re

def fetch_mcq_numbers():
    """Fetches all MCQ numbers from the ontology."""
    tool = RegulatoryAssessmentTool()
    query = '''
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    SELECT ?class
    WHERE {
        ?class rdf:type rdfs:Class .
        ?class skos:altLabel ?label .
        FILTER(STRSTARTS(?label, "MCQ"))
    }
    '''
    logging.debug(f"Generated SPARQL query for fetch_mcq_numbers: {query}")
    results = tool.run_sparql_query(query)

    # Extract the MCQ numbers correctly using regex
    mcq_numbers = []
    for result in results['results']['bindings']:
        uri = result['class']['value']
        mcq_number_match = re.search(r'MCQ\.(\d+(\.\d+)?)$', uri)
        if mcq_number_match:
            mcq_number = mcq_number_match.group(1)
            mcq_numbers.append(mcq_number)
            logging.debug(f"Added MCQ number: {mcq_number}")
            logging.debug(f"Current MCQ numbers: {mcq_numbers}")

    # Sort the MCQ numbers correctly
    def sort_key(mcq):
        parts = mcq.split('.')
        return tuple(int(part) for part in parts)

    mcq_numbers.sort(key=sort_key)

    logging.debug(f"Sorted MCQ numbers: {mcq_numbers}")
    return mcq_numbers

# Initialize the list of MCQ numbers
mcq_numbers = fetch_mcq_numbers()

# Create an instance of RegulatoryAssessmentTool
tool = RegulatoryAssessmentTool()

@app.route('/welcome')
def welcome():
    """Route for the welcome page."""
    return render_template('welcome.html')

@app.route('/')
def index():
    """Route for the main index page, displaying the current question."""
    if 'quiz_started' not in session:
        return redirect(url_for('welcome'))
    if not session.get('consent'):
        return redirect(url_for('consent'))

    try:
        mcq_index = session.get('mcq_index', 0)  # Get mcq_index from session
        print(f"In def index - mcq_index: {mcq_index}")

        data = tool.get_question_data(mcq_numbers[mcq_index])
        return render_template('index.html', **data)
    except Exception as e:
        logging.error(f"Error in index route: {e}")
        return f"An error occurred: {str(e)}", 500


@app.route('/consent', methods=['GET', 'POST'])
def consent():
    if request.method == 'POST':
        consent = request.form.get('consent')
        user_id = session.get('user_id', os.urandom(16).hex())  # Generate or get user ID
        print(f"User Id: {user_id}")
        session['user_id'] = user_id

        conn = sqlite3.connect('assessment_results.db')
        c = conn.cursor()

        if consent == 'yes':
            # User agreed to participate, record consent and proceed to the assessment
            session['consent'] = True
            session['quiz_started'] = True  # Set quiz_started to True
            c.execute('INSERT INTO results (user_id, consent) VALUES (?, ?)', (user_id, 'yes'))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
        else:
            # User did not agree to participate, record consent and show goodbye message
            session['consent'] = False
            c.execute('INSERT INTO results (user_id, consent) VALUES (?, ?)', (user_id, 'no'))
            conn.commit()
            conn.close()
            return redirect(url_for('goodbye'))

    return render_template('consent.html')


@app.route('/goodbye')
def goodbye():
    """Route to display a goodbye message when user does not consent."""
    return render_template('goodbye.html')


@app.route('/begin_assessment')
def begin_assessment():
    """Route to show the consent form before starting the assessment."""
    session['quiz_started'] = True  # Ensure quiz_started is set
    session['mcq_index'] = 0  # Initialize mcq_index
    return redirect(url_for('consent'))


@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    """Route to submit an answer for the current question."""
    data = request.json
    choice = data.get('choice')
    score = data.get('score', 0)

    if 'user_choices' not in session:
        session['user_choices'] = []
    if 'total_score' not in session:
        session['total_score'] = 0

    mcq_index = session.get('mcq_index', 0)
    print(f"In submit answer (top) - mcq_index: {mcq_index}")

    session['user_choices'].append((mcq_numbers[mcq_index], choice))
    session['total_score'] += int(score)

    if mcq_index >= len(mcq_numbers) - 1:
        return jsonify({
            'total_score': session['total_score'],
            'user_choices': session['user_choices'],
            'completed': True
        })

    mcq_index += 1
    session['mcq_index'] = mcq_index
    session.modified = True  # Ensure session is marked as modified
    print(f"In submit answer (just after increment) - mcq_index: {mcq_index}")

    return jsonify({
        'total_score': session['total_score'],
        'user_choices': session['user_choices'],
        'completed': False
    })

@app.route('/get_next_question')
def get_next_question():
    """Route to get the next question in the assessment."""
    try:
        mcq_index = session.get('mcq_index', 0)
        print(f"In get_next_question (top) - mcq_index: {mcq_index}")

        data = tool.get_question_data(mcq_numbers[mcq_index])
        question_data = {
            'question': {
                'number': mcq_numbers[mcq_index],
                'label': data['question']['label'],
                'definition': data['question']['definition'],
                'score': data['question']['score']
            },
            'answers': data['answers'],
            'article_details': data['article_details']
        }
        print(f"In get_next_question (bottom) - mcq_index: {mcq_index}")
        return jsonify(question_data)
    except Exception as e:
        logging.error(f"Error in get_next_question route: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/complete')
def complete():
    """Route to complete the assessment and display the results summary."""
    total_score = session.get('total_score', 0)
    user_choices = session.get('user_choices', [])

    grouped_choices = {}
    tool = RegulatoryAssessmentTool()
    label_map = {
        '(i)': 'Not Implemented',
        '(ii)': 'Partially Implemented',
        '(iii)': 'Fully Implemented'
    }

    for question_number, choice in user_choices:
        article_info = tool.get_article_label_for_question(question_number)
        article_label = article_info['articleLabel'] if article_info else 'Unknown Article'

        if article_label not in grouped_choices:
            grouped_choices[article_label] = []

        grouped_choices[article_label].append({
            'question_number': question_number,
            'choice': choice,
            'prefLabel': label_map[choice],  # Map the choice to the corresponding label
            'score': tool.get_question_score(choice)
        })

    grouped_choices = dict(sorted(grouped_choices.items()))
    for article in grouped_choices:
        grouped_choices[article] = sorted(grouped_choices[article], key=lambda x: x['question_number'])

    # Generate bar charts and calculate scores
    chart_paths = {}
    article_scores = {}
    total_max_score = 0
    overall_counts = {'Not Implemented': 0, 'Partially Implemented': 0, 'Fully Implemented': 0}

    for article, choices in grouped_choices.items():
        # Count occurrences of each response
        response_labels = [choice['prefLabel'] for choice in choices]
        response_counts = Counter(response_labels)

        # Update overall counts
        for label in overall_counts:
            overall_counts[label] += response_counts.get(label, 0)

        # Define the order of labels
        labels_order = ['Not Implemented', 'Partially Implemented', 'Fully Implemented']
        counts = [response_counts.get(label, 0) for label in labels_order]

        # Calculate scores
        total_questions = len(choices)
        article_score = sum(choice['score'] for choice in choices)
        max_score = total_questions * 2  # Each question has a maximum score of 2
        total_max_score += max_score

        article_scores[article] = {'score': article_score, 'max_score': max_score}

        plt.figure(figsize=(10, 5))
        bars = plt.bar(labels_order, counts, color='#CD3278')  # Use VioletRed3 color in hex
        plt.ylabel('Count of Responses', fontsize=16)  # Increase font size
        plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))  # Ensure y-axis has integer ticks
        plt.xticks(fontsize=14)  # Increase font size of x-axis ticks
        plt.yticks(fontsize=14)  # Increase font size of y-axis ticks
        plt.tight_layout()

        # Add labels on top of the bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2.0, height, f'{int(height)}', ha='center', va='bottom', fontsize=12)

        chart_path = f'static/{article}_chart.png'
        plt.savefig(chart_path)
        plt.close()

        chart_paths[article] = chart_path

    # Calculate percentage of NIS2 compliance
    if total_max_score > 0:
        compliance_percentage = (total_score / total_max_score) * 100
    else:
        compliance_percentage = 0

    # Split chart_paths into two lists
    articles = list(chart_paths.items())
    mid_index = len(articles) // 2
    left_column_articles = articles[:mid_index]
    right_column_articles = articles[mid_index:]

     # Generate overall score graph
    overall_labels = ['Not Implemented', 'Partially Implemented', 'Fully Implemented']
    overall_counts_list = [overall_counts[label] for label in overall_labels]

    logging.debug(f"overall_counts: {overall_counts_list}")

    plt.figure(figsize=(10, 5))
    bars = plt.bar(overall_labels, overall_counts_list, color='#cf73ff')
    plt.ylabel('Total Scores', fontsize=16)
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    plt.tight_layout()

    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2.0, height, f'{int(height)}', ha='center', va='bottom', fontsize=12)

    overall_chart_path = 'static/overall_chart.png'
    plt.savefig(overall_chart_path)
    plt.close()

# Save results to the database
    user_id = session.get('user_id', 'anonymous')
    details = json.dumps(grouped_choices)
    conn = sqlite3.connect('assessment_results.db')
    c = conn.cursor()
    c.execute('''UPDATE results SET total_score=?, compliance_percentage=?, details=? 
                 WHERE user_id=?''', (total_score, compliance_percentage, details, user_id))
    conn.commit()
    conn.close()

    return render_template('complete.html', total_score=total_score, left_column_articles=left_column_articles, right_column_articles=right_column_articles, article_scores=article_scores, compliance_percentage=compliance_percentage, overall_chart_path=overall_chart_path)


@app.route('/view_results')
def view_results():
    conn = sqlite3.connect('assessment_results.db')
    c = conn.cursor()
    c.execute('SELECT * FROM results')
    results = c.fetchall()

    # Fetch the column names
    column_names = [description[0] for description in c.description]

    conn.close()
    return render_template('view_results.html', results=results, column_names=column_names)


@app.route('/results')
def results():
    """Route to display the results of the assessment."""
    print("In... def results")
    if 'user_choices' not in session:
        return redirect(url_for('welcome'))

    user_choices = session['user_choices']
    tool = RegulatoryAssessmentTool()

    results = []
    article_details = {}  # Dictionary to hold article details

    # Map choices to implementation statuses
    label_map = {
        '(i)': 'Not Implemented',
        '(ii)': 'Partially Implemented',
        '(iii)': 'Fully Implemented'
    }

    for question_number, choice in user_choices:
        answer_def = tool.get_answer_definition(question_number, choice)
        article_info = tool.get_article_label_for_question(question_number)
        recommendation = None
        if choice in ['(i)', '(ii)']:  # Get recommendation only for 'Not Implemented' and 'Partially Implemented'
            recommendation = tool.get_recommendation(question_number)

        result = {
            'question_number': question_number,
            'answerLabel': label_map.get(f"({choice.strip('()')})", 'Unknown Status'),  # Use label_map for the label
            'answerDef': answer_def,
            'recommendation': recommendation  # Include the recommendation
        }

        if article_info:
            article_label = article_info['articleLabel']
            result['articleLabel'] = article_label
            result['articleDefinition'] = article_info['definition']
            # Add article details to the dictionary
            if article_label not in article_details:
                article_details[article_label] = article_info['definition']

        results.append(result)

    # Sort and group results by implementation status and then by article label
    results.sort(key=lambda x: (x['answerLabel'], x.get('articleLabel', '')))
    grouped_results = {'Not Implemented': {}, 'Partially Implemented': {}, 'Fully Implemented': {}}
    for result in results:
        article_label = result.get('articleLabel', 'Unknown Article')
        status = result['answerLabel']  # Use the full description

        if status not in grouped_results:
            grouped_results[status] = {}

        if article_label not in grouped_results[status]:
            grouped_results[status][article_label] = []

        grouped_results[status][article_label].append(result)

    print("Leaving... def results")
    return render_template('results.html', grouped_results=grouped_results, article_details=article_details)

# Define a custom darker pink color
darker_pink = colors.HexColor('#C2185B')

@app.route('/download_report')
def download_report():
    """Route to generate and download the assessment report as a PDF."""
    if 'user_choices' not in session:
        return redirect(url_for('welcome'))

    user_choices = session['user_choices']
    tool = RegulatoryAssessmentTool()

    results = []
    article_details = {}  # Dictionary to hold article details

    # Map choices to implementation statuses
    label_map = {
        '(i)': 'Not Implemented',
        '(ii)': 'Partially Implemented',
        '(iii)': 'Fully Implemented'
    }

    # Define a sorting order for implementation statuses
    status_order = {'Not Implemented': 0, 'Partially Implemented': 1, 'Fully Implemented': 2}

    for question_number, choice in user_choices:
        answer_def = tool.get_answer_definition(question_number, choice)
        article_info = tool.get_article_label_for_question(question_number)
        recommendation = None
        if choice in ['(i)', '(ii)']:  # Get recommendation only for 'Not Implemented' and 'Partially Implemented'
            recommendation = tool.get_recommendation(question_number)

        result = {
            'question_number': question_number,
            'answerLabel': label_map.get(f"({choice.strip('()')})", 'Unknown Status'),  # Use label_map for the label
            'answerDef': answer_def or '',
            'recommendation': recommendation or '',  # Include the recommendation
            'articleLabel': article_info['articleLabel'] if article_info else 'Unknown Article'
        }

        if article_info:
            article_label = article_info['articleLabel']
            result['articleLabel'] = article_label
            result['articleDefinition'] = article_info['definition']
            # Add article details to the dictionary
            if article_label not in article_details:
                article_details[article_label] = article_info['definition']

        results.append(result)

    # Sort results by article first and then by implementation status
    results.sort(key=lambda x: (x.get('articleLabel', ''), status_order.get(x['answerLabel'], 3)))

    # Group results by article and then by implementation status
    grouped_results = {}
    article_scores = {}
    for result in results:
        article_label = result['articleLabel']
        status = result['answerLabel']  # Use the full description

        if article_label not in grouped_results:
            grouped_results[article_label] = {'Not Implemented': [], 'Partially Implemented': [], 'Fully Implemented': []}

        grouped_results[article_label][status].append(result)

        if article_label not in article_scores:
            article_scores[article_label] = {'score': 0, 'max_score': 0}
        article_scores[article_label]['score'] += tool.get_question_score(f"({result['answerLabel']})")
        article_scores[article_label]['max_score'] += 2  # Assuming each question has a maximum score of 2

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    # Define styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    article_style = ParagraphStyle('ArticleStyle', parent=styles['Heading2'], textColor=darker_pink)
    question_style = ParagraphStyle('QuestionStyle', parent=styles['BodyText'], spaceBefore=10, spaceAfter=5, leftIndent=10)
    answer_style = ParagraphStyle('AnswerStyle', parent=styles['BodyText'], spaceBefore=5, spaceAfter=10, leftIndent=20)
    recommendation_style = ParagraphStyle('RecommendationStyle', parent=styles['BodyText'], spaceBefore=5, spaceAfter=10, leftIndent=20, textColor=darker_pink, fontName='Helvetica-Bold')
    score_style = ParagraphStyle('ScoreStyle', parent=styles['Heading3'])
    date_style = ParagraphStyle('DateStyle', parent=styles['Normal'], alignment=2)  # Right alignment

    # Add title
    elements.append(Paragraph("NIS2 Regulatory Assessment Report", title_style))
    elements.append(Spacer(1, 12))

    # Add date
    today = datetime.today().strftime('%Y-%m-%d')
    elements.append(Paragraph(f"Date: {today}", date_style))
    elements.append(Spacer(1, 12))

    # Add total score and compliance percentage
    total_score = session.get('total_score', 0)
    user_choices = session.get('user_choices', [])
    total_max_score = len(user_choices) * 2  # Each question has a maximum score of 2
    if total_max_score > 0:
        compliance_percentage = (total_score / total_max_score) * 100
    else:
        compliance_percentage = 0

    elements.append(Paragraph(f"Total Score: {total_score}", styles['Normal']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Percentage of NIS2 Compliance: {int(compliance_percentage)}%", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Add results and recommendations
    for article_label, statuses in grouped_results.items():
        if article_label in article_details:
            article_def = article_details[article_label]
            article_text = f"{article_label} - {article_def}"
        else:
            article_text = article_label

        elements.append(Paragraph(article_text, article_style))
        elements.append(Spacer(1, 12))

        total_questions = article_scores[article_label]['max_score'] // 2
        score_info = f"<h4>Total Questions: {total_questions}</h4>"
        elements.append(Paragraph(score_info, score_style))
        elements.append(Spacer(1, 12))

        # Add bar chart
        chart_path = f'static/{article_label}_chart.png'
        if os.path.exists(chart_path):
            elements.append(Image(chart_path, width=400, height=200))  # Resize the chart to fit better
            elements.append(Spacer(1, 12))

        for status, results in statuses.items():
            if results:
                elements.append(Paragraph(status, article_style))
                for result in results:
                    question = f"<b>Response Q.{result['question_number']}:</b> {result['answerDef']}"
                    elements.append(Paragraph(question, question_style))
                    if status != 'Fully Implemented':
                        recommendation = f"<b>Recommendation:</b> {result['recommendation']}"
                        elements.append(Paragraph(recommendation, recommendation_style))
                    elements.append(Spacer(1, 12))

        elements.append(PageBreak())  # Add a page break after each article

    # Build PDF
    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='NIS2_Assessment_Report.pdf', mimetype='application/pdf')

def add_page_number(canvas, doc):
    """Function to add page numbers to the PDF."""
    page_num = canvas.getPageNumber()
    text = f"Page {page_num}"
    canvas.drawRightString(200 * mm, 20 * mm, text)

def create_pie_chart():
    """Function to create and save a pie chart showing the question breakdown across NIS2 articles."""
    import matplotlib.pyplot as plt

    # Data with reversed order
    articles = [
        "Article 21.2 j", "Article 21.2 i", "Article 21.2 h", "Article 21.2 g",
        "Article 21.2 f", "Article 21.2 e", "Article 21.2 d", "Article 21.2 c",
        "Article 21.2 b", "Article 21.2 a"
    ]
    percentage = [3, 19, 1, 18, 10, 5, 6, 4, 7, 28]

    # Create a pie chart
    plt.figure(figsize=(6, 6))  # Resize the pie chart to fit better
    wedges, texts, autotexts = plt.pie(percentage, labels=articles, autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)

    # Adjust text properties
    for text in texts:
        text.set_fontsize(10)
        text.set_horizontalalignment('center')
        text.set_verticalalignment('center')

    for autotext in autotexts:
        autotext.set_fontsize(10)
        autotext.set_color('black')

    plt.title('Question breakdown across NIS2 Articles', pad=20)  # Move the title up
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    # Adjust layout to ensure no labels are cut off
    plt.tight_layout()

    # Save the chart as an image file
    plt.savefig('static/nis2_completion_chart.png')
    plt.close()

# Create the initial pie chart
create_pie_chart()

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    user_id = request.form.get('user_id')
    feedback_data = {
        'familiarity': request.form.get('familiarity'),
        'role': request.form.get('role'),
        'experience': request.form.get('experience'),
        'use_frequently': request.form.get('use_frequently'),
        'complexity': request.form.get('complexity'),
        'ease_of_use': request.form.get('ease_of_use'),
        'need_support': request.form.get('need_support'),
        'integration': request.form.get('integration'),
        'inconsistency': request.form.get('inconsistency'),
        'learn_quickly': request.form.get('learn_quickly'),
        'cumbersome': request.form.get('cumbersome'),
        'confidence': request.form.get('confidence'),
        'learning_curve': request.form.get('learning_curve'),
        'navigation': request.form.get('navigation'),
        'relevance': request.form.get('relevance'),
        'comprehensive': request.form.get('comprehensive'),
        'useful_recommendations': request.form.get('useful_recommendations'),
        'overall_satisfaction': request.form.get('overall_satisfaction'),
        'recommend': request.form.get('recommend'),
        'best_feature': request.form.get('best_feature'),
        'biggest_difficulty': request.form.get('biggest_difficulty'),
        'missing_feature': request.form.get('missing_feature'),
        'additional_comments': request.form.get('additional_comments')
    }

    conn = sqlite3.connect('assessment_results.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO feedback (
            user_id, familiarity, role, experience, use_frequently, complexity,
            ease_of_use, need_support, integration, inconsistency, learn_quickly,
            cumbersome, confidence, learning_curve, navigation, relevance,
            comprehensive, useful_recommendations, overall_satisfaction,
            recommend, best_feature, biggest_difficulty, missing_feature,
            additional_comments
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, feedback_data['familiarity'], feedback_data['role'], feedback_data['experience'],
        feedback_data['use_frequently'], feedback_data['complexity'], feedback_data['ease_of_use'],
        feedback_data['need_support'], feedback_data['integration'], feedback_data['inconsistency'],
        feedback_data['learn_quickly'], feedback_data['cumbersome'], feedback_data['confidence'],
        feedback_data['learning_curve'], feedback_data['navigation'], feedback_data['relevance'],
        feedback_data['comprehensive'], feedback_data['useful_recommendations'], feedback_data['overall_satisfaction'],
        feedback_data['recommend'], feedback_data['best_feature'], feedback_data['biggest_difficulty'],
        feedback_data['missing_feature'], feedback_data['additional_comments']
    ))



    # Commit the transaction and close the connection
    conn.commit()
    conn.close()

    # Redirect to a thank you page or another appropriate page
    return redirect(url_for('thank_you'))

    # Render the feedback form
    return render_template('feedback.html')

@app.route('/view_feedback')
def view_feedback():
    conn = sqlite3.connect('assessment_results.db')
    c = conn.cursor()
    c.execute('SELECT * FROM feedback')
    feedback_records = c.fetchall()
    conn.close()

    # Fetch the column names
    column_names = [description[0] for description in c.description]

    return render_template('view_feedback.html', feedback_records=feedback_records, column_names=column_names)

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

if __name__ == '__main__':
    app.run(debug=True)
