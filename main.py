from flask import Flask, request, render_template, jsonify
import requests
import re
from urllib.parse import unquote
from datetime import datetime

app = Flask(__name__)

def extract_instagram_token(cookies):
    """Extract EAAB token using 2025 Instagram-Facebook integration"""
    try:
        # Create session
        session = requests.Session()
        
        # Set cookies (with URL decoding)
        cookie_dict = {}
        for cookie in cookies.split(';'):
            cookie = cookie.strip()
            if '=' in cookie:
                key, value = cookie.split('=', 1)
                cookie_dict[key] = unquote(value)  # Decode URL encoded values
        
        # Verify required cookies
        required_cookies = ['c_user', 'xs', 'fr']
        for rc in required_cookies:
            if rc not in cookie_dict:
                return None, f"Missing required cookie: {rc}"

        # Set cookies in session
        for name, value in cookie_dict.items():
            session.cookies.set(name, value)

        # Make request to Facebook OAuth with Instagram permissions
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1',
            'Accept-Language': 'en-US,en;q=0.9'
        }

        oauth_url = "https://www.facebook.com/v17.0/dialog/oauth"
        params = {
            'client_id': '124024574287414',  # Instagram's official app ID
            'redirect_uri': 'https://www.instagram.com/',
            'scope': 'instagram_basic,instagram_manage_messages,pages_read_engagement,email',
            'response_type': 'token',
            'auth_type': 'rerequest',
            'state': datetime.now().strftime('%Y%m%d%H%M%S')
        }

        response = session.get(
            oauth_url,
            params=params,
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
        
        # Validate token format
        if token and token.startswith('EAAB') and len(token) > 100:
            return token, None
        else:
            return None, "Token extraction failed - may need fresh cookies"

    except Exception as e:
        return None, f"Error: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        cookies = request.form.get('cookies', '')
        token, error = extract_instagram_token(cookies)
        
        if token:
            return render_template('index.html', token=token)
        else:
            return render_template('index.html', error=error or "Token extraction failed")
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
