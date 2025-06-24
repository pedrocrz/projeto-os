from flask import Blueprint, request, render_template, redirect, session, url_for
from conexao import conectar

aparelhos_bp = Blueprint('aparelhos', __name__)

@aparelhos_bp.route('/aparelhos', methods=['GET', 'POST'])
def cadastrar_aparelho():
    if 'usuario_id' not in session or session['tipo'] != 'escritorio':
        return redirect(url_for('auth.login'))
    
    conn = conectar()
    with conn.cursor() as cursor:
        if request.method == 'POST':
            nome = request.form['nome']
            preco = float(request.form['preco'])

            cursor.execute('''
                    INSERT INTO aparelhos (nome, preco)
                           ''')
            