from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from conexao import conectar
from datetime import datetime, date
from urllib.parse import quote_plus


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

            # Cadastra o contrato sem valor ainda
            cursor.execute('''
                INSERT INTO contratos (cliente_id, numero_contrato, data_inicio, data_fim)      
                VALUES (%s, %s, %s, %s)              
            ''', (cliente_id, numero_contrato, data_inicio, data_fim))

            contrato_id = cursor.lastrowid

            # Adicionando os modelos relacionados ao contrato
            modelos_ids = request.form.getlist('modelo_ids[]')
    
            for modelo_id in modelos_ids:
                quantidade = int(request.form.get(f'quantidade_{modelo_id}'))
                valor_unitario = float(request.form.get(f'valor_modelo_{modelo_id}'))

                if quantidade and valor_unitario:
                    quantidade = int(quantidade)
                    valor_unitario = float(valor_unitario)
                    if quantidade > 0:                       
                        cursor.execute('''
                            INSERT INTO contratos_modelos(contrato_id, modelo_id, quantidade, valor_unitario)
                            VALUES (%s, %s, %s, %s)
                            ''', (contrato_id, modelo_id, quantidade, valor_unitario))
                        
           
            # Calculando o valor total do contrato após adicionar os modelos
            cursor.execute('''
                SELECT SUM(quantidade * valor_unitario) AS total
                FROM contratos_modelos
                WHERE contrato_id = %s
                           ''', (contrato_id,))
            resultado = cursor.fetchone()
            valor_total = resultado['total'] if resultado['total'] is not None else 0

            # Atualizar o campo valor de 'contratos'
            cursor.execute('''
                UPDATE contratos SET valor = %s WHERE id = %s
                           ''', (valor_total, contrato_id))
            conn.commit()
            
            flash('Contrato cadastrado com sucesso!')

            return redirect(url_for('contratos.cadastrar_contrato'))
        
        # pegando os clientes e modelos  para mostrar no <select>
        cursor.execute("SELECT id, nome FROM clientes")
        clientes = cursor.fetchall()
        
        cursor.execute("SELECT id, nome_marca, fabricante, capacidade_btu FROM modelos_ar_condicionado")
        modelos = cursor.fetchall()


    return render_template('cadastrar_contrato.html', clientes=clientes, modelos=modelos)
    
@contratos_bp.route('/contratos/listar')
def listar_contratos():
    if 'usuario_id' not in session or session['tipo'] != 'escritorio':
        return redirect(url_for('auth.login'))
    
    conn = conectar()
    with conn.cursor() as cursor:
        cursor.execute('''
            SELECT c.id, c.numero_contrato, c.valor, c.data_inicio, c.data_fim, cl.nome AS cliente_nome
            FROM contratos c
            JOIN clientes cl ON c.cliente_id = cl.id
            ORDER BY c.data_fim DESC
        ''')
        contratos_raw = cursor.fetchall()
    hoje = date.today()
    contratos_ativos = []
    contratos_vencidos = []
    
    for c in contratos_raw:
        data_fim = c['data_fim']
        dias_restantes = (data_fim - hoje).days
        c['dias_restantes'] = dias_restantes

        if dias_restantes >= 0:
            contratos_ativos.append(c)
        else:
            contratos_vencidos.append(c)


    return render_template('listar_contratos.html', 
                           contratos_ativos=contratos_ativos,
                           contratos_vencidos=contratos_vencidos)


@contratos_bp.route('/contratos/<int:contrato_id>')
def detalhes_contrato(contrato_id):
    if 'usuario_id' not in session or session['tipo'] != 'escritorio':
        return redirect(url_for('auth.login'))
    
    conn = conectar()
    with conn.cursor() as cursor:
        # dados do contrato
        cursor.execute('''
                SELECT c.*, cl.nome AS cliente_nome
                FROM contratos c
                JOIN clientes cl on c.cliente_id = cl.id
                WHERE c.id = %s
            ''', (contrato_id))
        contrato = cursor.fetchone()

        # Modelos do contrato
        cursor.execute('''
            SELECT m.nome_marca, m.fabricante, m.capacidade_btu, cm.quantidade, cm.valor_unitario
            FROM contratos_modelos cm
            JOIN modelos_ar_condicionado m ON cm.modelo_id = m.id
            WHERE cm.contrato_id = %s
            ''', (contrato_id,))
        modelos = cursor.fetchall()

        # Obras relacionadas
        cursor.execute('''
            SELECT o.id, o.nome, o.numero_empenho, o.endereco, o.cidade, o.estado, o.observacoes
            FROM obras o 
            WHERE o.contrato_id = %s
            ''', (contrato_id,))
        obras = cursor.fetchall()

        # Instaladores por obra
        instaladores_por_obra = {}

        for obra in obras:
            cursor.execute('''
                SELECT u.nome
                FROM instaladores_obra io
                JOIN usuarios u ON io.usuario_id = u.id
                WHERE io.obra_id = %s
                ''', (obra['id'],))
            instaladores_por_obra[obra['id']] = [i['nome'] for i in cursor.fetchall()]

        # Localização da obra (cidade + estado)
        localizacoes = []
        for obra in obras:
            endereco_completo = f"{obra['endereco']}, {obra['cidade']}, {obra['estado']}"
            localizacoes.append(quote_plus(endereco_completo))

    return render_template(
        'detalhes_contrato.html',
        contrato=contrato,
        modelos=modelos,
        obras=obras,
        instaladores_por_obra=instaladores_por_obra,
        localizacoes=localizacoes
        )
