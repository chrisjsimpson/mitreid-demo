# Demo oauth2 client 

### What does this do?
1. Connects to mitreid ( `Authorization endpoint: /authorize`)
2. Requests access token ( `Token endpoint: /token`) 
  - https://tools.ietf.org/html/rfc6749#section-4.1.3
3. Shows you the access token (ta-da)

That's it.

[Video demo](https://www.youtube.com/watch?v=Vn80iB9LFUw&feature=youtu.be)

## Assumptions:

- You have Mitreid running on: http://localhost:8080/openid-connect-server-webapp
  - If not, see https://github.com/chrisjsimpson/mitreid-demo quickstart
- You've already created a user and registerd an app (aka client/consumer) 

You need to know your:

- Client id
- Client secret
- Client redirect url
If you don't know these, follow: https://github.com/chrisjsimpson/mitreid-demo you basically need to create an app, and upon registering your app gets given a client id and client secret. You choose the redirect url back to your own app (this repo serves as an example client app).

# Setup 

Edit `client/__init__.py` with your client id and client secret (TODO make this config).

Then:
```
git clone git@github.com:chrisjsimpson/mitreid-demo.git
cd mitreid-demo/mitreid-client-example
virtualenv -p python3 venv
. venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=client
export FLASK_DEBUG=True
flask run
```

# Usage

Construct an authoristion request url to your Mitreid instance:
e.g. 

http://localhost:8080/openid-connect-server-webapp/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri=http://127.0.0.1:5000&scope=openid&state=1234zyx

Then you will see the auth token (if successful)

view `__init__.py` to see what's happening (it's only 20 lines long)
