from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from conexao import conectar

usuarios_bp = Blueprint('usuarios', __name__)

@usuarios_bp.route('/cadastrar_usuario', methods=['GET', 'POST'])
def cadastrar_usuario():
    if 'usuario_id' not in session or session['tipo'] != 'escritorio':
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        tipo = request.form['tipo']

        conn = conectar()
        with conn.cursor() as cursor:
            cursor.execute('''
                INSERT INTO usuarios (nome, email, senha, tipo)
                VALUES (%s, %s, %s, %s)
                ''', (nome, email, senha, tipo))
            conn.commit()

        flash('Usuário cadastrado com sucesso!')

    return render_template('cadastrar_usuario.html')

