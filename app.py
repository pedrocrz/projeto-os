from flask import Flask, render_template, request, redirect, session, url_for, flash 
from conexao import conectar
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from routes.auth import auth_bp
from routes import init_routes


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'peixe123')
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
init_routes(app)

#app.register_blueprint(auth_bp)
#@app.route('/')
#def home():
#   return 'Hello World'



if __name__ == '__main__':
    app.run(debug=False, host='192.168.5.104', port= 5000)
