import os
import pathlib
import requests
from flask import Flask, session, abort, redirect, request
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests

app = Flask("Google Local App")
app.secret_key = "Code"

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

def create_diamond(num_lines):
    if num_lines % 2 == 0:
        num_lines += 1

    diamond = ""
    for i in range(1, num_lines, 2):
        diamond += " " * ((num_lines - i) // 2)
        diamond += "atharv" * (i // 6 + 1)
        diamond += "\n"

    for i in range(num_lines, 0, -2):
        diamond += " " * ((num_lines - i) // 2)
        diamond += "atharv" * (i // 6 + 1)
        diamond += "\n"

    return diamond

GOOGLE_CLIENT_ID = "769259634860-5uif81n6opduoajqkgndmh24pk0rv5u4.apps.googleusercontent.com"

client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")
flow = Flow.from_client_secrets_file(
  client_secrets_file = client_secrets_file,
  scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
  redirect_uri="http://127.0.0.1:5000/callback"
                                     )



def login_is_requried(function):
  def wrapper(*args, **kwargs):
    if "google_id" not in session:
      return abort(401)
    else:
      return function()

  return wrapper  
    

@app.route("/login")
def login():
  autorization_url, state = flow.authorization_url()
  session["state"] = state
  return redirect(autorization_url)


@app.route("/callback")
def callback():
  flow.fetch_token(authorization_response = request.url)

  if not session["state"] == request.args["state"]:
    abort(500)

  credentials = flow.credentials
  request_session = requests.session()
  cached_session = cachecontrol.CacheControl(request_session)
  token_request = google.auth.transport.requests.Request(session=cached_session)

  id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )
  
  session["google_id"] = id_info.get("sub")
  session["name"] = id_info.get("name")
  session["email"] = id_info.get("email")
  session["profile_picture"] = id_info.get("picture")
  return redirect("/protected_area")


@app.route("/logout")
def logout():
  session.clear()
  return redirect("/")

@app.route("/")
def index():
  return """
        <div class="index-content" style="text-align: center;">
        <p style="font-family: Arial, sans-serif;">Enter the no of lines</p>
        <form action="/display_diamond" method="post">
            <label for="num_lines">Number of Lines (Max: 100):</label>
            <input type="number" id="num_lines" name="num_lines" min="1" max="100" required>
            <button type="submit" style="margin-top: 10px; padding: 10px 20px; border: none; background-color: #007bff; color: white; border-radius: 5px; cursor: pointer;">Display</button>
        </form>
        </div>
        <div class="index-content" style="text-align: center;">
            <h1 style="font-family: Arial, sans-serif;" >Welcome to the Application</h1>
            <p style="font-family: Arial, sans-serif;">click login into your google account</p>
            <a href='/login'>
                <button style="margin-top: 10px; padding: 10px 20px; border: none; background-color: #007bff; color: white; border-radius: 5px; cursor: pointer;">Login</button>
            </a>
        </div>
    """

@app.route("/display_diamond", methods=['POST'])
def display_diamond():
    num_lines = int(request.form['num_lines'])
    diamond = create_diamond(num_lines)
    return f"""
    <h2>Diamond Pattern:</h2>
    <pre>{diamond}</pre>
    <a href='/'><button style="margin-top: 10px; padding: 10px 20px; border: none; background-color: #007bff; color: white; border-radius: 5px; cursor: pointer;">Back to Home</button></a>
    """



@app.route("/protected_area")
@login_is_requried
def protected_area():
   if 'google_id' in session and 'name' in session and 'email' in session and "profile_picture" in session:
        user_name = session['name']
        user_email = session['email']
        profile_picture = session.get('profile_picture')
        return f"""
            <div style="text-align: center;">
                <img src='{profile_picture}' alt='Profile Picture' style='border-radius: 10%; width: 150px; height: 150px;'>
                <h1 style="font-family: Arial, sans-serif;">Welcome, {user_name}! <a href='/logout'><button style="margin-top: 20px; padding: 10px 20px; border: none; background-color: #007bff; color: white; border-radius: 5px; cursor: pointer;">Logout</button></a></h1>
                <p style="font-family: Arial, sans-serif;">You are signed with email: {user_email}</p>
                <p></p>
            </div>
        """
   else:
        return "User information not found. <a href='/logout'><button>Logout</button></a>"


if __name__ == "__main__":
  app.run(debug=True)