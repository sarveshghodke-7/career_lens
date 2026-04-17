import os
import cv2
import numpy as np
import pymysql
import pytesseract
from flask import Flask, request, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='static')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  

# Windows Users: Uncomment and update the path below if Tesseract is not in your system PATH
pytesseract.pytesseract.tesseract_cmd = r'D:\Tr-OCR\tesseract.exe'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '175935', # Update this
    'database': 'careerlens_db'
}

def get_db_connection():
    return pymysql.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        cursorclass=pymysql.cursors.DictCursor
    )

def process_image_with_opencv(filepath):
    img = cv2.imread(filepath)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    return thresh

def extract_text_from_image(filepath):
    processed_img = process_image_with_opencv(filepath)
    text = pytesseract.image_to_string(processed_img)
    return text.lower()

def calculate_ats_score(resume_text, job_description):
    jd_words = set(word.strip('.,!?;:()[]{}').lower() for word in job_description.split() if len(word) > 3)
    resume_words = set(resume_text.split())
    
    matched_keywords = list(jd_words.intersection(resume_words))
    missing_keywords = list(jd_words.difference(resume_words))
    
    if not jd_words:
        return 0, [], []
        
    score = int((len(matched_keywords) / len(jd_words)) * 100)
    return score, matched_keywords, missing_keywords

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'resume_file' not in request.files:
        return "Error: No file uploaded. <a href='/'>Go back</a>", 400
        
    file = request.files['resume_file']
    job_description = request.form.get('job_description', '')
    
    if file.filename == '':
        return "Error: No selected file. <a href='/'>Go back</a>", 400
        
    if file and job_description:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            resume_text = extract_text_from_image(filepath)
            score, matched, missing = calculate_ats_score(resume_text, job_description)
            
            # Save to MySQL
            try:
                connection = get_db_connection()
                with connection.cursor() as cursor:
                    sql = "INSERT INTO ats_history (filename, score) VALUES (%s, %s)"
                    cursor.execute(sql, (filename, score))
                connection.commit()
            except Exception as db_err:
                print(f"Database error: {db_err}")
            finally:
                if 'connection' in locals() and connection.open:
                    connection.close()

            os.remove(filepath)
            
            # Format lists into HTML list items
            matched_html = "".join([f"<li>{word}</li>" for word in matched[:10]])
            missing_html = "".join([f"<li>{word}</li>" for word in missing[:10]])
            
            if not matched_html: matched_html = "<li>None</li>"
            if not missing_html: missing_html = "<li>None</li>"

            # --- THE NEW STRING REPLACEMENT LOGIC ---
            # Open the pure HTML result file
            with open('templates/result.html', 'r', encoding='utf-8') as f:
                html_template = f.read()

            # Replace the placeholders with our actual data
            final_html = html_template.replace('__SCORE__', str(score))
            final_html = final_html.replace('__MATCHED_LIST__', matched_html)
            final_html = final_html.replace('__MISSING_LIST__', missing_html)

            # Return the modified HTML string
            return final_html
            
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return f"An error occurred: {str(e)} <br><a href='/'>Go back</a>", 500
            
    return "Invalid request. <a href='/'>Go back</a>", 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)