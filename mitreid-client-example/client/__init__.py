from flask import Flask, jsonify, url_for, request
import requests

TOKEN_ENDPOINT="http://localhost:8080/openid-connect-server-webapp/token"
REDIRECT_URI="http://127.0.0.1:5000"
CLIENT_ID="22dih2szepebygw0pvcnhqineyx12tkbwnjm2plb"
CLIENT_SECRET="1e3vrbeardxdpztyuwiyi1ikwsblgs4zlumchvrx"

app = Flask(__name__)

@app.route('/')
def test():
  auth_code = request.args.get('code')
  # Should compare state value to ensure it matches the one we started with
  state = request.args.get('state')

  # use auth code to request an access token:
  # this is: https://tools.ietf.org/html/rfc6749#section-4.1.3
  payload = {
    'grant_type': 'authorization_code',
    'code': auth_code,
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'redirect_uri': REDIRECT_URI
  }
  token_req = requests.post(TOKEN_ENDPOINT, data=payload)
  return token_req.text

