from flask import Blueprint, request, render_template, redirect, url_for
from conexao import conectar

catalogo_bp = Blueprint('catalogo', __name__)

@catalogo_bp.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar_modelo_ar():
    conn = conectar()
    with conn.cursor() as cursor:
        if request.method == 'POST':
            nome_marca = request.form['nome_marca']
            fabricante = request.form['fabricante']
            capacidade_btu = request.form['capacidade_btu']

            cursor.execute('''
                    INSERT INTO modelos_ar_condicionado (nome_marca, fabricante, capacidade_btu)
                    VALUES (%s, %s, %s)
                    ''', (nome_marca, fabricante, capacidade_btu))
            conn.commit()
            return redirect(url_for('catalogo.listar_modelos'))
    return render_template('cadastrar_modelo.html')
@catalogo_bp.route('/listar')
def listar_modelos():
    conn = conectar()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM modelos_ar_condicionado")
        modelos = cursor.fetchall()
    return render_template('listar_modelos.html', modelos=modelos)
