from flask import Blueprint, render_template, request, redirect, session, flash, url_for
from conexao import conectar

obras_bp = Blueprint('obras', __name__)


@obras_bp.route('/', methods=['GET', 'POST'])
def obras():
    if 'usuario_id' not in session or session['tipo'] != 'escritorio':
        return redirect(url_for('login'))

    conn = conectar()
    with conn.cursor() as cursor:
        
        # Carregar os instaladores e contratos
        cursor.execute("SELECT id, nome FROM usuarios WHERE tipo = 'instalador'")
        instaladores = cursor.fetchall()

        cursor.execute('''
            SELECT c.id, c.numero_contrato, c.valor, cl.nome AS cliente_nome
            FROM contratos c
            JOIN clientes cl ON c.cliente_id = cl.id
            ''')
        contratos = cursor.fetchall()
        
        modelos_contrato = []
        contrato_selecionado = request.args.get('contrato_id')

        if contrato_selecionado:
            cursor.execute('''
                SELECT cm.modelo_id, m.fabricante, m.nome_marca, m.capacidade_btu, cm.quantidade
                FROM contratos_modelos cm
                JOIN modelos_ar_condicionado m ON cm.modelo_id = m.id
                WHERE cm.contrato_id = %s
                ''', (contrato_selecionado,))
            modelos_contrato = cursor.fetchall()
        
        # POST: salvando nova obra:
        if request.method == 'POST':
            nome = request.form['nome']
            endereco = request.form['endereco']
            cidade = request.form['cidade']
            estado = request.form['estado']
            contrato_id = request.form['contrato_id']
            criado_por = session['usuario_id']
            numero_empenho = request.form['numero_empenho']
            observacoes = request.form.get('observacoes', '')

            
            # Carregar modelos relacionados ao contrato
            cursor.execute('''
                SELECT cm.modelo_id, m.fabricante, m.nome_marca, m.capacidade_btu, cm.quantidade
                FROM contratos_modelos cm
                JOIN modelos_ar_condicionado m ON cm.modelo_id = m.id
                WHERE cm.contrato_id = %s
            ''', (contrato_id,))
            modelos_contrato = cursor.fetchall()
            # Cadastra obra
            cursor.execute('''
                INSERT INTO obras (nome, endereco, cidade, estado, contrato_id, criado_por, numero_empenho, observacoes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (nome, endereco, cidade, estado, contrato_id, criado_por, numero_empenho, observacoes))

            conn.commit()

            cursor.execute('SELECT LAST_INSERT_ID()')
            obra_id = cursor.fetchone()['LAST_INSERT_ID()']

            # Instaladores
            instaladores_selecionados = request.form.getlist('instaladores')
            for usuario_id in instaladores_selecionados:
                cursor.execute('''
                    INSERT INTO instaladores_obra (obra_id, usuario_id)
                    VALUES (%s, %s)
                    ''', (obra_id, usuario_id))
                
            # Modelos
            modelo_ids = request.form.getlist('modelo_ids[]')
            for modelo_id in modelo_ids:
                campo_quantidade = f'quantidade_{modelo_id}'
                quantidade = int(request.form.get(campo_quantidade, 0))
                if quantidade > 0:

                    # Consultando valor unitário
                    cursor.execute('''
                        SELECT valor_unitario FROM contratos_modelos
                        WHERE contrato_id = %s AND modelo_id = %s
                        ''', (contrato_id, modelo_id))
                    resultado = cursor.fetchone()
                    valor_unitario = resultado['valor_unitario'] if resultado else 0
                    valor_total = quantidade * valor_unitario

                      # Inserindo modelos da obra                  
                    cursor.execute('''
                        INSERT INTO locais_modelos_instalados(local_id, modelo_id, quantidade, valor_total)
                        VALUES (%s, %s, %s, %s)
                    ''', (obra_id, modelo_id, quantidade, valor_total))

            conn.commit()

                        

            flash('Obra Cadastrada com Sucesso!')
            return redirect(url_for('obras.obras'))
        
        # Listar Obras
        cursor.execute('''
            SELECT o.id, o.nome, o.cidade, o.estado, GROUP_CONCAT(u.nome SEPARATOR ', ') AS instaladores
            FROM obras o 
            LEFT JOIN instaladores_obra io ON o.id = io.obra_id
            LEFT JOIN usuarios u ON io.usuario_id = u.id
            GROUP BY o.id
            ORDER BY o.id DESC
            ''')
        obras_lista = cursor.fetchall()
    conn.close()
    return render_template(
        'obras.html',
        instaladores=instaladores,
        contratos=contratos,
        obra=obras_lista,
        modelos_contrato=modelos_contrato,
        contrato_selecionado=int(contrato_selecionado) if contrato_selecionado else None
    )

@obras_bp.route('/editar/<int:obra_id>', methods=['GET', 'POST'])
def editar_obra(obra_id):
    if 'usuario_id' not in session or session['tipo'] != 'escritorio':
        return redirect(url_for('auth.login'))

    conn = conectar()
    with conn.cursor() as cursor:
        if request.method == 'GET':
            # Buscar dados da obra para edição
            cursor.execute('''
                SELECT o.id, o.nome, o.endereco, o.cidade, o.estado, o.numero_empenho, o.observacoes, o.contrato_id
                FROM obras o 
                WHERE o.id = %s
                ''', (obra_id,))
            obra = cursor.fetchone()
            
            if not obra:
                flash('Obra não encontrada!')
                return redirect(url_for('obras.obras'))

            # Buscar instaladores da obra
            cursor.execute('''
                SELECT u.id
                FROM instaladores_obra io
                JOIN usuarios u ON io.usuario_id = u.id
                WHERE io.obra_id = %s
                ''', (obra_id,))
            instaladores_obra = [inst['id'] for inst in cursor.fetchall()]

            # Buscar todos os instaladores disponíveis
            cursor.execute("SELECT id, nome FROM usuarios WHERE tipo = 'instalador'")
            instaladores = cursor.fetchall()

            conn.close()
            return render_template('editar_obra.html', obra=obra, instaladores=instaladores, instaladores_obra=instaladores_obra)

        # POST: Processar edição
        if request.method == 'POST':
            nome = request.form['nome']
            endereco = request.form['endereco']
            cidade = request.form['cidade']
            estado = request.form['estado']
            numero_empenho = request.form['numero_empenho']
            observacoes = request.form.get('observacoes', '')

            # Atualizar obra
            cursor.execute('''
                UPDATE obras 
                SET nome = %s, endereco = %s, cidade = %s, estado = %s, 
                    numero_empenho = %s, observacoes = %s
                WHERE id = %s
                ''', (nome, endereco, cidade, estado, numero_empenho, observacoes, obra_id))

            # Atualizar instaladores
            # Primeiro remove todos os instaladores da obra
            cursor.execute('DELETE FROM instaladores_obra WHERE obra_id = %s', (obra_id,))
            
            # Depois adiciona os selecionados
            instaladores_selecionados = request.form.getlist('instaladores')
            for usuario_id in instaladores_selecionados:
                cursor.execute('''
                    INSERT INTO instaladores_obra (obra_id, usuario_id)
                    VALUES (%s, %s)
                    ''', (obra_id, usuario_id))

            conn.commit()
            conn.close()

            flash('Obra atualizada com sucesso!')
            return redirect(url_for('obras.detalhes_obra', obra_id=obra_id))

@obras_bp.route('/obras/<int:obra_id>/modelo/<int:modelo_id>/instalacoes')
def visualizar_instalacoes_modelo(obra_id, modelo_id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    
    conn = conectar()
    with conn.cursor() as cursor:
        # Buscar modelo
        cursor.execute('''
            SELECT fabricante, nome_marca, capacidade_btu
            FROM modelos_ar_condicionado
            WHERE id= %s
            ''', (modelo_id,))
        modelo = cursor.fetchone()

        # Detalhes da obra
        cursor.execute('''
            SELECT nome, endereco, cidade, estado
            FROM obras
            WHERE id = %s
            ''', (obra_id,))
        obra = cursor.fetchone()

        
        # Buscar todas as instalações da obra
        cursor.execute('''
            SELECT
                i.id AS instalacao_id,
                i.data,
                i.observacoes,
                u.nome AS instalador
            FROM instalacoes i 
            JOIN usuarios u ON i.usuario_id = u.id
            JOIN instaladores_instalacao ii ON ii.instalacao_id = i.id
            JOIN instaladores_equipamentos ie ON ie.instalador_id = u.id
            JOIN equipamentos e ON e.id = ie.equipamento_id
            WHERE i.obra_id = %s AND e.modelo = (
                       SELECT CONCAT(nome_marca, ' - ', fabricante, ' - ', capacidade_btu)
                       FROM modelos_ar_condicionado WHERE id = %s)
            GROUP BY i.id
            ORDER BY i.data DESC
            ''',(obra_id, modelo_id))
        
        instalacoes = cursor.fetchall()
    return render_template('visualizar_instal_modelos.html',
                           modelo=modelo,
                           instalacoes=instalacoes,
                           obra_id=obra_id)

@obras_bp.route('/obras/<int:obra_id>')
def detalhes_obra(obra_id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    
    conn = conectar()
    with conn.cursor() as cursor:
        # Detalhes da obra:
        cursor.execute('''
            SELECT o.id, o.nome, o.endereco, o.cidade, o.estado, o.numero_empenho, o.observacoes,
                    c.numero_contrato, cl.nome AS cliente
            FROM obras o 
            JOIN contratos c ON o.contrato_id = c.id
            JOIN clientes cl ON cliente_id = cl.id
            WHERE o.id = %s
            ''', (obra_id))
        obra = cursor.fetchone()

        # Instaladores da obra
        cursor.execute('''
            SELECT u.nome
            FROM instaladores_obra io
            JOIN usuarios u ON io.usuario_id = u.id
            WHERE io.obra_id = %s
            ''', (obra_id))
        instaladores = cursor.fetchall()

        # Modelos instalados + total previsto
        cursor.execute('''
            SELECT m.id AS modelo_id, m.fabricante, m.nome_marca, m.capacidade_btu,
                lmi.quantidade AS qtd_total
            FROM locais_modelos_instalados lmi
            JOIN modelos_ar_condicionado m ON lmi.modelo_id = m.id
            WHERE lmi.local_id = %s
            ''', (obra_id))
        modelos = cursor.fetchall()

        # Para cada modelo, puxas as instalações
        for modelo in modelos:
            modelo_id = modelo['modelo_id']
            
            # instalações feitas nesse modelo

            cursor.execute('''
                SELECT i.id, i.data, u.nome AS instalador, i.metragem_linha, i.metragem_dreno, i.metragem_eletrica
                FROM instalacoes i
                JOIN usuarios u ON i.usuario_id = u.id
                JOIN instaladores_instalacao ii ON ii.instalacao_id = i.id
                JOIN instaladores_equipamentos ie ON ie.instalador_id = u.id
                JOIN equipamentos e ON e.id = ie.equipamento_id
                WHERE i.obra_id = %s AND e.modelo = (
                            SELECT CONCAT(nome_marca, ' - ', fabricante, ' - ', capacidade_btu)
                            FROM modelos_ar_condicionado WHERE ID = %s
                           )             
                ''', (obra_id, modelo_id))
            instalacoes = cursor.fetchall()
            modelo['instalacoes'] = instalacoes
            modelo['qtd_instalada'] = len(instalacoes)

            # Resumo das metragens
            if instalacoes:
                linhas = [i['metragem_linha'] for i in instalacoes if i['metragem_linha']]
                drenos = [i['metragem_dreno'] for i in instalacoes if i['metragem_dreno']]
                eletricas = [i['metragem_eletrica'] for i in instalacoes if i['metragem_eletrica']]

                modelo['linha_min'] = min(linhas) if linhas else 0
                modelo['linha_max'] = max(linhas) if linhas else 0
                modelo['linha_media'] = round(sum(linhas) / len(linhas), 2) if linhas else 0

                modelo['dreno_min'] = min(drenos) if drenos else 0
                modelo['dreno_max'] = max(drenos) if drenos else 0
                modelo['dreno_media'] = round(sum(drenos) / len(drenos), 2) if drenos else 0
                 
                modelo['eletrica_min'] = min(eletricas) if eletricas else 0
                modelo['eletrica_max'] = max(eletricas) if eletricas else 0
                modelo['eletrica_media'] = round(sum(eletricas) / len(eletricas), 2) if eletricas else 0
            else:
                modelo['linha_min'] = modelo['linha_max'] = modelo['linha_media'] = 0
                modelo['dreno_min'] = modelo['dreno_max'] = modelo['dreno_media'] = 0
                modelo['eletrica_min'] = modelo['eletrica_max'] = modelo['eletrica_media'] = 0

    conn.close()
                

    return render_template('detalhes_obra.html',
                           obra=obra,
                           instaladores=instaladores,
                           modelos=modelos)

        