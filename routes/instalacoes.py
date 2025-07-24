from flask import Blueprint, render_template, request, redirect, session, flash, url_for
from conexao import conectar
import datetime
import os
from werkzeug.utils import secure_filename
from flask import current_app
import pathlib




instalacoes_bp = Blueprint('instalacoes', __name__)


@instalacoes_bp.route('/obras_instalador')
def obras_instalador():
    if 'usuario_id' not in session or session['tipo'] != 'instalador':
        return redirect(url_for('auth.login'))
    
    usuario_id = session['usuario_id']

    conn = conectar()
    with conn.cursor() as cursor:
        cursor.execute('''
            SELECT o.id, o.nome, o.cidade, o.estado, o.numero_empenho
            FROM obras o
            JOIN instaladores_obra io ON io.obra_id = o.id
            WHERE io.usuario_id = %s
            ORDER BY o.id DESC
            ''', (usuario_id,))
        obras = cursor.fetchall()
    conn.close()
    return render_template('instalador_obra.html', obras=obras)

@instalacoes_bp.route('/obra/<int:obra_id>/modelos')
def modelos_da_obra(obra_id):
    if 'usuario_id' not in session or session['tipo'] != 'instalador':
        return redirect(url_for('auth.login'))

    conn = conectar()
    with conn.cursor() as cursor:
        #Pegando a obra
        cursor.execute('''
            SELECT o.nome, o.cidade, o.estado, o.numero_empenho
            FROM obras o 
            WHERE o.id = %s
            ''', (obra_id,))
        obra = cursor.fetchone()
        # Pegando os modelos + quantidade instalada
        cursor.execute('''
            SELECT 
                lmi.id AS local_modelo_id,
                m.id,
                m.nome_marca,
                m.fabricante,
                m.capacidade_btu,
                lmi.quantidade AS quantidade_total,
                (
                    SELECT COUNT(*) FROM instalacoes i
                    WHERE i.local_modelo_id = lmi.id                 
                ) AS quantidade_instalada
            FROM locais_modelos_instalados lmi
            JOIN modelos_ar_condicionado m ON m.id = lmi.modelo_id
            WHERE lmi.local_id = %s
        ''', (obra_id))
        modelos = cursor.fetchall()
        # Para cada modelo, buscar as instalações feitas
        for modelo in modelos:
            cursor.execute('''
                SELECT id, data, observacoes
                FROM instalacoes
                WHERE local_modelo_id = %s
                ORDER BY data DESC
                ''', (modelo['local_modelo_id'],))
            modelo['instalacoes'] = cursor.fetchall()

            
    conn.close()
    return render_template('modelos_obra_instalador.html', obra=obra, modelos=modelos, obra_id=obra_id)

@instalacoes_bp.route('/obra/<int:obra_id>/modelo/<int:local_modelo_id>/instalar', methods=['GET', 'POST'])
def nova_instalacao_modelo(obra_id, local_modelo_id):
    if 'usuario_id' not in session or session['tipo'] != 'instalador':
        return redirect(url_for('auth.login'))
    
    conn = conectar()
    with conn.cursor() as cursor:
        cursor.execute('''
            SELECT mac.nome_marca, mac.fabricante, mac.capacidade_btu
            FROM locais_modelos_instalados lmi
            JOIN modelos_ar_condicionado mac ON mac.id = lmi.modelo_id
            WHERE lmi.id = %s
            ''', (local_modelo_id,))
        modelo = cursor.fetchone()

    if request.method == 'POST':
        data = datetime.datetime.now()
        usuario_id = session['usuario_id']
        observacoes = request.form.get('observacoes')
        checklist = request.form.getlist('checklist[]')
        foto = request.files.get('foto')
        tipo_foto = request.form.get('tipo_foto')
        metragem_linha = request.form.get('metragem_linha')
        metragem_dreno = request.form.get('metragem_dreno')
        metragem_eletrica = request.form.get('metragem_eletrica')



        with conn.cursor() as cursor:
            # inserir na tabela das instalações
            cursor.execute('''
                INSERT INTO instalacoes(obra_id, usuario_id, data, observacoes, local_modelo_id)
                VALUES (%s, %s, %s, %s, %s)
                ''', (obra_id, usuario_id, data, observacoes, local_modelo_id))
            conn.commit()

            cursor.execute('SELECT LAST_INSERT_ID()')
            instalacao_id = list(cursor.fetchone().values())[0]
            
            # Checklist
            for item in checklist:
                cursor.execute('''
                    INSERT INTO checklist (instalacao_id, item, marcado)
                    VALUES (%s, %s, %s)
                    ''', (instalacao_id, item, True))

            # Foto com descrição                
            for i in range(1, 6): # 5 fotos possíveis
                foto = request.files.get(f'fotos_{i}')
                tipo_foto = request.form.get(f'foto_tipo_{i}')

                if foto and foto.filename != '':
                    pasta_instalacao = os.path.join(current_app.config['UPLOAD_FOLDER'], f'instalacao_{instalacao_id}')
                    pathlib.Path(pasta_instalacao).mkdir(parents=True, exist_ok=True)
                    filename = secure_filename(f'{tipo_foto.replace(" ", "_")}_{foto.filename}')
                    caminho = os.path.join(pasta_instalacao, filename)
                    foto.save(caminho)
                    

                    cursor.execute('''
                        INSERT INTO fotos_instalacoes (instalacao_id, caminho, tipo)
                        VALUES (%s, %s, %s)
                        ''', (instalacao_id, f'instalacao_{instalacao_id}/{filename}', tipo_foto))
                    
                    

            # Atualizar metragem
            cursor.execute('''
                UPDATE instalacoes 
                        SET metragem_linha = %s,
                           metragem_dreno = %s,
                           metragem_eletrica = %s
                WHERE id = %s
                ''', (metragem_linha, metragem_dreno, metragem_eletrica, instalacao_id)) 
                
            conn.commit()

            
        flash('Instalação registrada com sucesso!')
        return redirect(url_for('instalacoes.obras_instalador'))
    return render_template('instalacao_modelo_form.html', modelo=modelo, obra_id=obra_id)
#Rota para visualizar/editar a instalação
@instalacoes_bp.route('/instalacao/<int:instalacao_id>/editar', methods=['GET', 'POST'])
def editar_instalacao(instalacao_id):
    if 'usuario_id' not in session or session['tipo'] != 'instalador':
        return redirect(url_for('auth.login'))
    
    conn = conectar()
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM instalacoes WHERE id = %s', (instalacao_id,))
        instalacao = cursor.fetchone()

        cursor.execute('SELECT * FROM checklist WHERE instalacao_id = %s', (instalacao_id))
        checklist = cursor.fetchall()

        cursor.execute('SELECT * FROM fotos_instalacoes WHERE instalacao_id = %s', (instalacao_id))
        fotos = cursor.fetchall()

        if request.method == 'POST':
            observacoes = request.form.get('observacoes')
            metragem = request.form.get('metragem')
            itens_marcados = request.form.getlist('itens')
            metragem_linha = request.form.get('metragem_linha')
            metragem_dreno = request.form.get('metragem_dreno')
            metragem_eletrica = request.form.get('metragem_eletrica')

            # Atualizar a instalação
            cursor.execute('''
                UPDATE instalacoes
                SET observacoes = %s, 
                           metragem_linha = %s,
                           metragem_dreno = %s,
                           metragem_eletrica = %s
                WHERE id = %s
                ''', (observacoes, metragem_linha, metragem_dreno, metragem_eletrica, instalacao_id))
            
            # Atualizar Checklist (apaga tudo e regrava)
            cursor.execute('DELETE FROM checklist WHERE instalacao_id = %s', (instalacao_id,))
            for item in itens_marcados:
                cursor.execute('''
                    INSERT INTO checklist (instalacao_id, item, marcado)
                    VALUES (%s, %s, %s)
                    ''', (instalacao_id, item, True))
                
            # Fotos (opcionais)
            for i in range(1, 6):
                foto = request.files.get(f'fotos_{i}')
                tipo_foto = request.form.get(f'foto_tipo_{i}')
                if foto and foto.filename != '':
                    pasta_instalacao = os.path.join(current_app.config['UPLOAD_FOLDER'], f'instalacao_{instalacao_id}')
                    pathlib.Path(pasta_instalacao).mkdir(parents=True, exist_ok=True)
                    filename = secure_filename(f'{tipo_foto.replace(" ", "_")}_{foto.filename}')
                    caminho = os.path.join(pasta_instalacao, filename)
                    foto.save(caminho)
                    

                    cursor.execute('''
                        INSERT INTO fotos_instalacoes (instalacao_id, caminho, tipo)
                        VALUES (%s, %s, %s)
                        ''', (instalacao_id, f'instalacao_{instalacao_id}/{filename}', tipo_foto))
            conn.commit()


            cursor.execute('SELECT * FROM instalacoes WHERE id = %s', (instalacao_id,))
            instalacao = cursor.fetchone()

            cursor.execute('SELECT * FROM checklist WHERE instalacao_id = %s', (instalacao_id))
            checklist = cursor.fetchall()

            cursor.execute('SELECT * FROM fotos_instalacoes WHERE instalacao_id = %s', (instalacao_id))
            fotos = cursor.fetchall()

    conn.close()          
        

    return render_template('editar_instalacao.html', instalacao=instalacao, checklist=checklist, fotos=fotos)


@instalacoes_bp.route('/relatorio_instalador', methods=['GET', 'POST'])
def relatorio_instalador():
    if 'usuario_id' not in session or session['tipo'] != 'escritorio':
        return redirect(url_for('auth.login'))
    
    conn = conectar()
    with conn.cursor() as cursor:
        # Buscar todos os instaladores
        cursor.execute("SELECT id, nome FROM usuarios WHERE tipo = 'instalador' ORDER BY nome")
        instaladores = cursor.fetchall()
        
        instalacoes_instalador = []
        instalador_selecionado = None
        
        if request.method == 'POST':
            instalador_id = request.form.get('instalador_id')
            if instalador_id:
                # Buscar dados do instalador selecionado
                cursor.execute("SELECT nome FROM usuarios WHERE id = %s", (instalador_id,))
                instalador_selecionado = cursor.fetchone()
                
                # Buscar todas as instalações do instalador com detalhes
                cursor.execute('''
                    SELECT 
                        i.id AS instalacao_id,
                        i.data,
                        i.observacoes,
                        i.metragem_linha,
                        i.metragem_dreno,
                        i.metragem_eletrica,
                        o.nome AS obra_nome,
                        o.cidade AS obra_cidade,
                        o.estado AS obra_estado,
                        mac.fabricante,
                        mac.nome_marca,
                        mac.capacidade_btu
                    FROM instalacoes i
                    JOIN obras o ON i.obra_id = o.id
                    JOIN locais_modelos_instalados lmi ON i.local_modelo_id = lmi.id
                    JOIN modelos_ar_condicionado mac ON lmi.modelo_id = mac.id
                    WHERE i.usuario_id = %s
                    ORDER BY i.data DESC
                    ''', (instalador_id,))
                instalacoes_instalador = cursor.fetchall()
                
                # Para cada instalação, buscar as fotos
                for instalacao in instalacoes_instalador:
                    cursor.execute('''
                        SELECT caminho, tipo
                        FROM fotos_instalacoes
                        WHERE instalacao_id = %s
                        ''', (instalacao['instalacao_id'],))
                    instalacao['fotos'] = cursor.fetchall()
    
    conn.close()
    return render_template('relatorio_instalador.html',
                         instaladores=instaladores,
                         instalacoes=instalacoes_instalador,
                         instalador_selecionado=instalador_selecionado)






