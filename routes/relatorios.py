from flask import Blueprint, render_template, request, redirect, session, flash, url_for
from conexao import conectar

relatorios_bp = Blueprint('relatorios', __name__)

@relatorios_bp.route('/instalador', methods=['GET', 'POST'])
def relatorio_instalador():
    # Verificar se o usuário está logado e é admin/supervisor
    if 'usuario_id' not in session or session['tipo'] != 'escritorio':
        return redirect(url_for('auth.login'))
    
    conn = conectar()
    
    # Buscar todos os instaladores para o dropdown
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT id, nome 
            FROM usuarios 
            WHERE tipo = 'instalador' 
            ORDER BY nome
        """)
        instaladores = cursor.fetchall()
    
    # Inicializar variáveis para os dados do relatório
    instalador_selecionado = None
    resumo_equipamentos = []
    resumo_obras = []
    detalhes_instalacoes = []
    
    # Se um instalador foi selecionado, buscar os dados do relatório
    if request.method == 'POST':
        instalador_id = request.form.get('instalador_id')
        
        if instalador_id:
            with conn.cursor() as cursor:
                # Buscar dados do instalador selecionado
                cursor.execute("""
                    SELECT nome FROM usuarios WHERE id = %s
                """, (instalador_id,))
                instalador_selecionado = cursor.fetchone()
                
                # Resumo de equipamentos por capacidade/modelo
                cursor.execute("""
                    SELECT 
                        m.fabricante,
                        m.nome_marca,
                        m.capacidade_btu,
                        COUNT(*) as quantidade_instalada
                    FROM instalacoes i
                    JOIN locais_modelos_instalados lmi ON i.local_modelo_id = lmi.id
                    JOIN modelos_ar_condicionado m ON lmi.modelo_id = m.id
                    WHERE i.usuario_id = %s
                    GROUP BY m.id, m.fabricante, m.nome_marca, m.capacidade_btu
                    ORDER BY m.capacidade_btu, m.fabricante, m.nome_marca
                """, (instalador_id,))
                resumo_equipamentos = cursor.fetchall()
                
                # Resumo de metragem por obra
                cursor.execute("""
                    SELECT 
                        o.nome as obra_nome,
                        o.cidade,
                        o.estado,
                        SUM(COALESCE(i.metragem_linha, 0)) as total_metragem_linha,
                        SUM(COALESCE(i.metragem_dreno, 0)) as total_metragem_dreno,
                        SUM(COALESCE(i.metragem_eletrica, 0)) as total_metragem_eletrica,
                        COUNT(i.id) as total_instalacoes
                    FROM obras o
                    JOIN instalacoes i ON o.id = i.obra_id
                    WHERE i.usuario_id = %s
                    GROUP BY o.id, o.nome, o.cidade, o.estado
                    ORDER BY o.nome
                """, (instalador_id,))
                resumo_obras = cursor.fetchall()
                
                # Detalhes das instalações (resumo detalhado)
                cursor.execute("""
                    SELECT 
                        i.id,
                        i.data,
                        o.nome as obra_nome,
                        m.fabricante,
                        m.nome_marca,
                        m.capacidade_btu,
                        i.metragem_linha,
                        i.metragem_dreno,
                        i.metragem_eletrica,
                        i.observacoes
                    FROM instalacoes i
                    JOIN obras o ON i.obra_id = o.id
                    JOIN locais_modelos_instalados lmi ON i.local_modelo_id = lmi.id
                    JOIN modelos_ar_condicionado m ON lmi.modelo_id = m.id
                    WHERE i.usuario_id = %s
                    ORDER BY i.data DESC
                """, (instalador_id,))
                detalhes_instalacoes = cursor.fetchall()
    
    conn.close()
    
    return render_template('relatorio_instalador.html', 
                         instaladores=instaladores,
                         instalador_selecionado=instalador_selecionado,
                         resumo_equipamentos=resumo_equipamentos,
                         resumo_obras=resumo_obras,
                         detalhes_instalacoes=detalhes_instalacoes)