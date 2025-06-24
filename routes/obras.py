from flask import Blueprint, render_template, request, redirect, session, flash, url_for
from conexao import conectar

obras_bp = Blueprint('obras', __name__)


@obras_bp.route('/', methods=['GET', 'POST'])
def obras():
    if 'usuario_id' not in session or session['tipo'] != 'escritorio':
        return redirect(url_for('login'))

    conn = conectar()
    with conn.cursor() as cursor:
        #Dados da obra
        if request.method == 'POST':
            nome = request.form['nome']
            endereco = request.form['endereco']
            cidade = request.form['cidade']
            estado = request.form['estado']
            criado_por = session['usuario_id']
            contrato_id = request.form['contrato_id']

            
            # Cadastrando a obra
            cursor.execute('''
                    INSERT INTO obras (nome, endereco, cidade, estado, criado_por, contrato_id)
                           VALUES (%s, %s, %s, %s,%s, %s)
                    ''', (nome, endereco, cidade, estado, criado_por, contrato_id))
            conn.commit()

        # Pegando o Id da obra recem criada
        cursor.execute('SELECT LAST_INSERT_ID()')
        obra_id = cursor.fetchone()['LAST_INSERT_ID()']

        # Pegando os instaladores selecionados e salvando relacionamento
        instaladores_selecionados = request.form.getlist('instaladores')
        for usuario_id in instaladores_selecionados:
            cursor.execute('''
                    INSERT INTO instaladores_obra (obra_id, usuario_id)
                    VALUES (%s, %s)
                           ''', (obra_id, usuario_id))
        conn.commit()

        flash('Obra Cadastrada com Sucesso!')

        # Carregar os instaladores para o formulário
        cursor.execute("SELECT id, nome FROM usuarios WHERE tipo = 'instalador'")
        instaladores = cursor.fetchall()
        
        # Buscando contratos para exibir no select
        cursor.execute("SELECT id, numero_contrato FROM contratos")
        contratos = cursor.fetchall()

        # Carregando as obras em aberto
        cursor.execute('''
                SELECT o.id, o.nome, o.cidade, o.estado, GROUP_CONCAT(u.nome SEPARATOR ', ') AS instaladores
                FROM obras o 
                LEFT JOIN instaladores_obra io ON o.id =io.obra_id
                LEFT JOIN usuarios u ON io.usuario_id = u.id
                GROUP BY o.id
                ORDER BY o.id DESC
                ''')
        obras_lista = cursor.fetchall()
        conn.close()

        


    return render_template('obras.html', instaladores=instaladores, obras=obras_lista, contratos=contratos)

















