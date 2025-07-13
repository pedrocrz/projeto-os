from flask import Blueprint, render_template, request, redirect, session, flash, url_for
from conexao import conectar

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/', methods=['GET', 'POST'])
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    if session['tipo'] == 'escritorio':
        return redirect(url_for('dashboard.dashboard_escritorio'))
    elif session['tipo'] == 'instalador':
        return redirect(url_for('dashboard.dashboard_instalador'))
    
@dashboard_bp.route('/escritorio')
def dashboard_escritorio():
    if 'usuario_id' not in session or session['tipo'] != 'escritorio':
        return redirect(url_for('login'))
    
    conn = conectar()
    with conn.cursor() as cursor:
        # Pegando os contratos em aberto
        cursor.execute('''
            SELECT c.id, c.numero_contrato, clientes.nome AS cliente, c.data_inicio, c.data_fim, c.valor
            FROM contratos c
            JOIN clientes ON c.cliente_id = clientes.id
            WHERE c.data_fim >= CURDATE()
                       ''')
        contratos_abertos = cursor.fetchall()
        
        # Pegando obras em aberto
        cursor.execute('''
            SELECT o.id, o.nome, o.cidade, o.estado
            FROM obras o 
            LEFT JOIN instalacoes i ON o.id = i.obra_id
            WHERE i.id IS NULL
                    ''')
        obras_abertas = cursor.fetchall()
        
        # Resumo de produtividade por instalador
        cursor.execute('''
            SELECT u.nome,
                SUM(CASE WHEN DATE(i.data) = CURDATE() THEN 1 ELSE 0 END) AS hoje,
                SUM(CASE WHEN WEEK(i.data) = WEEK(CURDATE()) THEN 1 ELSE 0 END) AS semana,
                SUM(CASE WHEN MONTH(i.data) = MONTH(CURDATE()) THEN 1 ELSE 0 END) AS mes
            FROM usuarios u
            JOIN instalacoes i ON u.id = i.usuario_id
            WHERE u.tipo = 'instalador'
            GROUP BY u.id
            ORDER BY nome DESC
                       ''')
        resumo_instaladores = cursor.fetchall()
    conn.close()


    return render_template('dashboard.html', contratos_abertos=contratos_abertos, obras_abertas=obras_abertas, resumo_instaladores=resumo_instaladores)

@dashboard_bp.route('/instalador')
def dashboard_instalador():
    if 'usuario_id' not in session or session['tipo'] != 'instalador':
        return redirect(url_for('auth.login'))
    usuario_id = session.get('usuario_id')

    conn = conectar()
    with conn.cursor() as cursor:
        cursor.execute('''
                SELECT i.id, i.data, o.nome AS obra_nome
                FROM instalacoes i
                JOIN obras o ON i.obra_id = o.id
                WHERE i.usuario_id = %s
            ''', (usuario_id))
        instalacoes = cursor.fetchall()
    conn.close()

    return render_template('dashboard_instalador.html', instalacoes=instalacoes)

@dashboard_bp.route('/painel')
def painel_escritorio():
    if 'usuario_id' not in session or session['tipo'] != 'escritorio':
        return redirect(url_for('auth.login'))
    
    conn = conectar()
    with conn.cursor() as cursor:
        # indicariores rápidos
        cursor.execute('SELECT COUNT(*) AS contratos FROM contratos')
        total_contratos = cursor.fetchone()['contratos']

        cursor.execute('SELECT COUNT(*) AS obras FROM obras')
        total_obras = cursor.fetchone()['obras']

        cursor.execute('SELECT COUNT(*) AS instalacoes FROM instalacoes')
        total_inst = cursor.fetchone()['instalacoes']

        # resumo por contrato
        cursor.execute('''
            SELECT c.id, c.numero_contrato,
                       COUNT(DISTINCT o.id) AS obras,
                       COUNT(i.id) AS instalacoes
            FROM contratos c
            LEFT JOIN obras o ON o.contrato_id = c.id
            LEFT JOIN instalacoes i ON i.obra_id = o.id
            GROUP BY c.id
            ORDER BY c.id DESC
                       ''')
        resumo = cursor.fetchall()
    conn.close()
    
    return render_template('painel_escritorio.html',
                            total_contratos=total_contratos,
                            total_obras=total_obras,
                            total_inst=total_inst,
                            resumo=resumo)