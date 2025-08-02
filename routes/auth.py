from flask import Blueprint, render_template, request, redirect, session, flash, url_for
from conexao import conectar

auth_bp = Blueprint('auth', __name__)



# def home():
#     # Se o usuário estiver logado, redireciona para o dashboard
#     if 'usuario_id' in session:
#         return redirect(url_for('dashboard'))
#     return redirect(url_for('login'))

@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        conn = conectar()
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM usuarios WHERE email = %s AND senha = %s', (email, senha))
            usuario = cursor.fetchone()

        if usuario:
            session['usuario_id'] = usuario['id']
            session['nome'] = usuario['nome']
            session['tipo'] = usuario['tipo']
            return redirect(url_for('dashboard.dashboard'))
        else:
            return 'Usuário ou senha incorretos'
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear() # limpa tudo da sessão
    return redirect(url_for('auth.login'))
