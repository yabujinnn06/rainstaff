"""
WSGI Entry Point for Render Deployment
Redirects gunicorn to server/app.py (Flask web dashboard)
"""

# Import the Flask app from server directory
from server.app import app

# This allows: gunicorn wsgi:app
if __name__ == "__main__":
    app.run()
