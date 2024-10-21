# Flask Data Processing App

This is a Flask-based web application for processing and storing various types of data files using PostgreSQL on Replit.

## Setup Instructions

1. Clone the repository to your Replit account.
2. Make sure you have a PostgreSQL database set up on Replit.
3. Set up the following environment variables in your Replit secrets:
   - PGDATABASE
   - PGUSER
   - PGPORT
   - DATABASE_URL
   - PGPASSWORD
   - PGHOST
4. Install the required packages by running:
   ```
   pip install -r requirements.txt
   ```
5. Run the application:
   ```
   python app.py
   ```

## Features

- File upload and processing for various data types (SMS, calls, contacts, applications, keylogs, chats)
- Data visualization
- Unique data insights
- Chat view for message data

## File Structure

- `app.py`: Main Flask application
- `utils.py`: Utility functions for data processing and database operations
- `templates/`: HTML templates for the web interface
- `uploads/`: Directory for uploaded files (created automatically)

## Usage

1. Access the application through the provided Replit URL.
2. Use the upload page to submit data files.
3. View visualizations and insights on the respective pages.
4. Explore the chat view for message data.

## Note

This application is designed to run on Replit and uses Replit's built-in PostgreSQL database. Make sure all necessary environment variables are set before running the application.
