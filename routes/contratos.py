from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from conexao import conectar

contratos_bp = Blueprint('contratos', __name__)

@contratos_bp.route('/contratos', methods=['GET', 'POST'])
def cadastrar_contrato():
    if 'usuario_id' not in session or session['tipo'] != 'escritorio':
        return redirect(url_for('auth.login'))
    
    conn = conectar()
    with conn.cursor() as cursor:
        if request.method == 'POST':
            cliente_id = request.form['cliente_id']
            numero_contrato = request.form['numero_contrato']
            data_inicio = request.form['data_inicio']
            data_fim = request.form['data_fim']
            valor = request.form['valor']

            cursor.execute('''
                INSERT INTO contratos (cliente_id, numero_contrato, data_inicio, data_fim, valor)      
                VALUES (%s, %s, %s, %s, %s)              
            ''', (cliente_id, numero_contrato, data_inicio, data_fim, valor))

            contrato_id = cursor.lastrowid
            # Adicionando os modelos relacionados ao contrato
            modelos_ids = request.form.getlist('modelo_ids')
    
            for modelo_id in modelos_ids:
                quantidade = request.form.get(f'quantidade_{modelo_id}')
                if quantidade and int(quantidade) > 0:
                        cursor.execute('''
                            INSERT INTO contratos_modelos(contrato_id, modelo_id, quantidade)
                            VALUES (%s, %s, %s)
                            ''', (contrato_id, modelo_id, quantidade))
                        

            conn.commit()


            flash('Contrato cadastrado com sucesso!')

            return redirect(url_for('contratos.cadastrar_contrato'))
        # pegando os clientes e modelos  para mostrar no <select>
        cursor.execute("SELECT id, nome FROM clientes")
        clientes = cursor.fetchall()
        
        cursor.execute("SELECT id, nome_marca, fabricante, capacidade_btu FROM modelos_ar_condicionado")
        modelos = cursor.fetchall()

        return render_template('cadastrar_contrato.html', clientes=clientes, modelos=modelos)
    
