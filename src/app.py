from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session, jsonify
import logging
from pathlib import Path
from werkzeug.utils import secure_filename
from .generate_salary_slips import generate_salary_slips
from .google_sheets_handler import read_google_sheet

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get the parent directory and set up paths
PARENT_DIR = Path(__file__).parent.parent
TEMPLATE_DIR = PARENT_DIR / 'templates'
UPLOAD_DIR = PARENT_DIR / 'uploads'

app = Flask(__name__, template_folder=str(TEMPLATE_DIR))
app.secret_key = 'your-secret-key-here'  # Required for flash messages and sessions

# Configure upload folder
ALLOWED_EXTENSIONS = {'csv'}
UPLOAD_DIR.mkdir(exist_ok=True)
app.config['UPLOAD_FOLDER'] = str(UPLOAD_DIR)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    logger.debug("Home route accessed")
    return render_template('upload.html')

@app.route('/get-sheets', methods=['POST'])
def get_sheets():
    sheet_url = request.form.get('sheet_url')
    if not sheet_url:
        return jsonify({'error': 'Please provide a Google Sheets URL'}), 400
    
    try:
        # This will return list of available sheets
        sheets = read_google_sheet(sheet_url)
        return jsonify({'sheets': sheets})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = UPLOAD_DIR / filename
        file.save(str(filepath))
        
        try:
            # Generate salary slips
            html_content = generate_salary_slips(str(filepath))
            
            # Save the generated HTML
            output_path = UPLOAD_DIR / 'salary_slips.html'
            output_path.write_text(html_content, encoding='utf-8')
            
            # Redirect to the salary slips page
            return redirect(url_for('show_salary_slips'))
        except Exception as e:
            flash(f'Error processing file: {str(e)}')
            return redirect(url_for('home'))
    else:
        flash('Invalid file type. Please upload a CSV file.')
        return redirect(request.url)

@app.route('/process-sheet', methods=['POST'])
def process_sheet_url():
    sheet_url = request.form.get('sheet_url')
    sheet_name = request.form.get('sheet_name')
    
    if not sheet_url or not sheet_name:
        flash('Please provide both Google Sheets URL and select a sheet')
        return redirect(url_for('home'))
    
    try:
        # Read data from selected sheet
        df = read_google_sheet(sheet_url, sheet_name)
        
        # Save data as CSV temporarily
        temp_csv = UPLOAD_DIR / 'temp_sheet.csv'
        df.to_csv(str(temp_csv), index=False)
        
        # Generate salary slips
        html_content = generate_salary_slips(str(temp_csv))
        
        # Save the generated HTML
        output_path = UPLOAD_DIR / 'salary_slips.html'
        output_path.write_text(html_content, encoding='utf-8')
        
        # Clean up temporary CSV
        temp_csv.unlink()
        
        # Redirect to the salary slips page
        return redirect(url_for('show_salary_slips'))
    except Exception as e:
        flash(f'Error processing Google Sheet: {str(e)}')
        return redirect(url_for('home'))

@app.route('/salary-slips')
def show_salary_slips():
    output_path = UPLOAD_DIR / 'salary_slips.html'
    if output_path.exists():
        content = output_path.read_text(encoding='utf-8')
        return content
    else:
        flash('No salary slips found. Please upload a CSV file or provide a Google Sheet URL.')
        return redirect(url_for('home'))

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(host='0.0.0.0', port=5000, debug=True) 