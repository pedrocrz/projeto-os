from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from conexao import conectar

clientes_bp = Blueprint('clientes', __name__)

@clientes_bp.route('/clientes', methods=['GET', 'POST'])
def cadastrar_cliente():
    if 'usuario_id' not in session or session['tipo'] != 'escritorio':
        return redirect(url_for('auth.login'))
    
    conn = conectar()
    with conn.cursor() as cursor:
        if request.method == 'POST':
            nome = request.form['nome']
            cnpj = request.form['cnpj']
            endereco = request.form['endereco']

            cursor.execute('''
                    INSERT INTO clientes (nome, CNPJ, endereco)
                    VALUES (%s, %s, %s)
                        ''', (nome, cnpj, endereco))
            conn.commit()
            flash('Cliente cadastrado com sucesso!')
            return redirect(url_for('clientes.cadastrar_cliente'))
    return render_template('clientes.html')

