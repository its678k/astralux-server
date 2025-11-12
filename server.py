from flask import Flask, send_file, abort, jsonify
import json
import os
import time
from pathlib import Path

app = Flask(__name__)

TOKENS_FILE = 'tokens.json'
DOWNLOADS_DIR = 'downloads'

def load_tokens():
    """Load tokens from JSON file"""
    if not os.path.exists(TOKENS_FILE):
        return {}
    try:
        with open(TOKENS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_tokens(tokens):
    """Save tokens to JSON file"""
    with open(TOKENS_FILE, 'w') as f:
        json.dump(tokens, f, indent=2)

def delete_token(token):
    """Remove a token from storage"""
    tokens = load_tokens()
    if token in tokens:
        del tokens[token]
        save_tokens(tokens)

@app.route('/download/<token>')
def download_file(token):
    """Serve file for one-time download"""
    tokens = load_tokens()
    
    # Check if token exists
    if token not in tokens:
        return jsonify({'error': 'Invalid or expired download link'}), 404
    
    token_data = tokens[token]
    file_path = token_data['path']
    expiry = token_data['expiry']
    
    # Check if token expired (24 hour validity)
    if time.time() > expiry:
        delete_token(token)
        return jsonify({'error': 'Download link has expired'}), 410
    
    # Check if file exists
    if not os.path.exists(file_path):
        delete_token(token)
        return jsonify({'error': 'File not found'}), 404
    
    # Delete token immediately (one-time use)
    delete_token(token)
    
    # Serve file
    try:
        return send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path)
        )
    except Exception as e:
        return jsonify({'error': 'Failed to serve file'}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Server is running'})

if __name__ == '__main__':
    # Create downloads directory if it doesn't exist
    Path(DOWNLOADS_DIR).mkdir(exist_ok=True)
    
    # Run Flask server
    app.run(host='0.0.0.0', port=5000, debug=False)