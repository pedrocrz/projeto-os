from flask import Flask, render_template, request, redirect, session, url_for, flash 
from conexao import conectar
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from routes.auth import auth_bp
from routes import init_routes


app = Flask(__name__)
app.secret_key = 'peixe123'
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
init_routes(app)

#app.register_blueprint(auth_bp)
#@app.route('/')
#def home():
#   return 'Hello World'



if __name__ == '__main__':
    app.run(debug=True, host='192.168.5.104', port= 5000)