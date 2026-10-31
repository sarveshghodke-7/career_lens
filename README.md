# CareerLens - Resume Analyzer and Career Guidance

CareerLens is a minimalist, strictly-constrained academic prototype that calculates an ATS (Applicant Tracking System) score by comparing a resume against a job description.

## Strict Project Constraints Met:
* **Backend:** Python & Flask
* **Image Processing & OCR:** OpenCV2 & PyTesseract
* **Frontend:** 100% Pure HTML and CSS
* **Database:** MySQL
* **Zero JavaScript:** Dynamic frontend updates were intentionally omitted.
* **Zero Jinja2:** The results page is compiled dynamically within the Python backend and served directly as an HTML string to ensure strict HTML compliance.

## Setup Instructions

### 1. Database Setup
1. Open MySQL.
2. Run the provided `database.sql` script to create `careerlens_db` and the `ats_history` table.
3. Open `app.py` and update the `DB_CONFIG` dictionary with your local MySQL password.

### 2. Tesseract OCR Installation
Because this project utilizes OpenCV for image preprocessing, Tesseract OCR is required to extract the text.
* **Windows:** Download the Tesseract installer from UB Mannheim. Uncomment line 14 in `app.py` and ensure the path matches your installation (`r'C:\Program Files\Tesseract-OCR\tesseract.exe'`).
* **Linux:** Run `sudo apt-get install tesseract-ocr`.
* **Mac:** Run `brew install tesseract`.

### 3. Python Environment Setup
1. Open your terminal in the project directory.
2. Install the required Python libraries:
   ```bash
   pip install -r requirements.txt