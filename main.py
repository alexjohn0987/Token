from flask import Flask, request, render_template, redirect, url_for
import requests
import re
from datetime import datetime

app = Flask(__name__)

# Configuration
FB_APP_ID = "124024574287414"  # Instagram's official app ID
REDIRECT_URI = "https://www.instagram.com/"
MIN_TOKEN_LENGTH = 150  # EAAB... tokens are typically >150 chars

def extract_fb_token(cookie_header):
    """Extract EAAB token using 2025 Facebook OAuth flow"""
    try:
        session = requests.Session()
        
        # Set cookies from header
        cookies = {}
        for c in cookie_header.split(';'):
            c = c.strip()
            if '=' in c:
                key, val = c.split('=', 1)
                cookies[key] = val
                session.cookies.set(key, val)

        # Verify required cookies
        required_cookies = ['c_user', 'xs', 'fr']
        for rc in required_cookies:
            if rc not in cookies:
                return None, f"Missing required cookie: {rc}"

        # Make OAuth request with 2025 parameters
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1',
            'Accept-Language': 'en-US,en;q=0.9'
        }

        oauth_params = {
            'client_id': FB_APP_ID,
            'redirect_uri': REDIRECT_URI,
            'scope': 'instagram_basic,instagram_manage_messages,email',
            'response_type': 'token,granted_scopes',
            'auth_type': 'rerequest',
            'display': 'popup',
            'state': datetime.now().strftime('%Y%m%d%H%M%S')
        }

        response = session.get(
            'https://www.facebook.com/v19.0/dialog/oauth',
            params=oauth_params,
            headers=headers,
            allow_redirects=True,
            timeout=30
        )

        # Extract token from response
        token = None
        
        # Method 1: Check redirect URL
        if 'access_token=' in response.url:
            token_match = re.search(r'access_token=([^&]+)', response.url)
            if token_match:
                token = token_match.group(1)

        # Method 2: Check JavaScript response
        if not token:
            js_match = re.search(r'"accessToken":"([^"]+)"', response.text)
            if js_match:
                token = js_match.group(1)

        # Validate token
        if token and len(token) >= MIN_TOKEN_LENGTH and token.startswith('EAAB'):
            return token, None
        else:
            return None, "Valid token not found in response"

    except Exception as e:
        return None, f"Extraction error: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def index():
    token = None
    error = None
    cookie_input = ""
    
    if request.method == 'POST':
        cookie_input = request.form.get('cookies', '')
        token, error = extract_fb_token(cookie_input)
    
    return render_template(
        'index.html',
        token=token,
        error=error,
        cookie_input=cookie_input
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
