import os
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from utils import process_and_insert_data, create_tables, test_db_connection, get_data_for_visualization

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    db_connected = test_db_connection()
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            try:
                process_and_insert_data(file_path)
                flash('File successfully uploaded and processed')
            except Exception as e:
                flash(f'Error processing file: {str(e)}')
            
            return redirect(url_for('upload_file'))
    return render_template('upload.html', db_connected=db_connected)

@app.route('/visualize')
def visualize():
    return render_template('visualize.html')

@app.route('/api/data/<category>')
def get_data(category):
    data = get_data_for_visualization(category)
    return jsonify(data)

if __name__ == '__main__':
    create_tables()
    connection_status = test_db_connection()
    print(f"Database connection status: {connection_status}")
    app.run(host='0.0.0.0', port=5000)
