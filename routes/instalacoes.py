from flask import Blueprint, render_template, request, redirect, session, flash, url_for
from conexao import conectar
import datetime
import os
from werkzeug.utils import secure_filename
from flask import current_app



instalacoes_bp = Blueprint('instalacoes', __name__)


@instalacoes_bp.route('/nova_instalacao', methods=['GET', 'POST'])
def nova_instalacao():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    
    conn = conectar()
    with conn.cursor() as cursor:
        # Listar obras para o SELECT
        cursor.execute('SELECT * FROM obras')
        obras = cursor.fetchall()

        if request.method == 'POST':
            obra_id = request.form['obra_id']
            observacoes = request.form['observacoes']
            metragem = request.form.get('metragem')
            usuario_id = session['usuario_id']
            data = datetime.datetime.now()
            itens_checklist = request.form.getlist('checklist[]')
            foto = request.files.get('foto')


            with conn.cursor() as cursor:

                # 1º inserir a instalação
                cursor.execute('''
                        INSERT INTO instalacoes (obra_id, usuario_id, data, observacoes)
                            VALUES (%s, %s, %s, %s)
                        ''', (obra_id, usuario_id, data, observacoes))
                conn.commit()

                #2º Pegar o ID da instalação recem inserida
                cursor.execute('SELECT LAST_INSERT_ID()')
                nova_instalacao_id = list(cursor.fetchone().values())[0]

                #3º Inserir os itens do checklist
                for item in itens_checklist:
                    cursor.execute('''
                            INSERT INTO checklist (instalacao_id, item, marcado)
                                   VALUES (%s, %s, %s)
                                ''', (nova_instalacao_id, item, True))
                
                #4º Salvar foto, se houver
                if foto and foto.filename != '':
                   filename = secure_filename(foto.filename)
                   caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                   foto.save(caminho)

                   cursor.execute('''
                            INSERT INTO fotos_instalacoes (instalacao_id, caminho)
                                  VALUES (%s, %s)
                                  ''', (nova_instalacao_id, filename))

                conn.commit() 


            flash('Instalação cadastrada com sucesso!')
            return redirect(url_for('instalacoes.detalhes_instalacao', id=nova_instalacao_id))
    return render_template('cadastro_instalacao.html', obras=obras)

@instalacoes_bp.route('/instalacao/<int:id>')
def detalhes_instalacao(id):
    if 'usuario_id' not in session:
        return  redirect(url_for('auth.login'))
    
    conn = conectar()

    with conn.cursor() as cursor:
       # Pegand o checklist 
        cursor.execute('SELECT * FROM checklist WHERE instalacao_id = %s', (id,))
        checklist = cursor.fetchall()
        # Pegando o as fotos
        cursor.execute('SELECT * FROM fotos_instalacoes WHERE instalacao_id = %s', (id,))
        fotos = cursor.fetchall()
        # Pega as observacoes
        cursor.execute('SELECT observacoes FROM instalacoes WHERE id = %s', (id,))
        resultado = cursor.fetchone()
        observacoes = resultado['observacoes'] if resultado else ''
        # Pega os detalhes da instalação e da obra com JOIN
        cursor.execute('''
                SELECT
                       i.id AS instalacao_id,
                       i.observacoes,
                       o.nome AS nome_obra,
                       i.data AS data_obra,
                       i.metragem,
                       o.endereco,
                       o.cidade,
                       o.estado
                    FROM instalacoes i
                    JOIN obras o ON i.obra_id = o.id
                    WHERE i.id = %s
                       ''',(id,))
        dados_obra = cursor.fetchone()
    return render_template('detalhes_instalacao.html', 
                        instalacao_id=id, 
                        checklist=checklist,
                        fotos=fotos, 
                        observacoes=observacoes,
                        dados_obra=dados_obra
                        )


@instalacoes_bp.route('/upload_foto', methods=['POST'])
def upload_foto():
    foto = request.files['foto']
    instalacao_id = request.form['instalacao_id']

    if foto:
        filename = secure_filename(foto.filename)
        caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        foto.save(caminho)

        conn = conectar()
        with conn.cursor() as cursor:
            cursor.execute('INSERT INTO fotos_instalacoes (instalacao_id, caminho) VALUES (%s, %s)', (instalacao_id, filename))
            conn.commit()
        return redirect(url_for('instalacoes.detalhes_instalacao', id=instalacao_id))

@instalacoes_bp.route('/salvar_checklist', methods=['POST'])
def salvar_cheklist():
    instalacao_id = request.form['instalacao_id']
    itens_marcados = request.form.getlist('itens')
    observacoes = request.form.get('observacoes', '')
    metragem = request.form.get('metragem')

    conn = conectar()
    with conn.cursor() as cursor:
        cursor.execute('DELETE FROM checklist WHERE instalacao_id = %s', (instalacao_id,))
        for item in itens_marcados:
            cursor.execute('INSERT INTO checklist (instalacao_id, item, marcado) VALUES (%s, %s, %s)', (instalacao_id, item, True))

        cursor.execute('UPDATE instalacoes SET observacoes = %s, metragem = %s WHERE id = %s', (observacoes, metragem, instalacao_id))
        conn.commit()
    
    return redirect(url_for('instalacoes.detalhes_instalacao', id=instalacao_id))
