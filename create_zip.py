import os
import zipfile

def create_project_zip(zip_name='messenger_project.zip'):
    # List of essential files to include
    essential_files = [
        'app.py',
        'models.py',
        'routes.py',
        'init_db.py',
        'templates/index.html',
        'static/css/style.css',
        'static/js/script.js',
        'replit.nix',
        'requirements.txt'
    ]
    
    # Create a new zip file
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add each file to the zip
        for file_path in essential_files:
            if os.path.exists(file_path):
                # Preserve the directory structure in the zip
                zipf.write(file_path)
                print(f"Added {file_path} to {zip_name}")
            else:
                print(f"Warning: {file_path} not found")

if __name__ == '__main__':
    create_project_zip()
    print("\nZip file creation completed!")
