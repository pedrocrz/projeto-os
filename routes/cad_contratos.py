from flask import Blueprint, render_template, request, redirect, url_for, session
from conexao import conectar

cad_contratos_bp = Blueprint('cad_contratos', __name__)

@cad_contratos_bp.route('/contratos/<int:contrato_id>/cad_contratos', methods=['GET', 'POST'])
def cad_contratos(contrato_id):
    # Verificando se o usuário está logado e permissao
    if 'usuario_id' not in session or session['tipo'] != 'escritorio':
        return redirect(url_for('auth.login'))
    # conexão com o banco de dados
    conn = conectar()

    with conn.cursor() as cursor:
        if request.method == 'POST':
            total_enderecos = int(request.form['total_enderecos'])

            for i in range(total_enderecos):
                cidade = request.form.get(f'endereco_{i}_cidade')
                endereco = request.form.get(f'endereco_{i}_logradouro')

                # Inserindo o local de instalação
                cursor.execute('''
                        INSERT INTO locais_instalacao (contrato_id, cidade, endereco)
                        VALUES (%s, %s, %s)
                        ''', (contrato_id, cidade, endereco))
                local_id = cursor.lastrowid

                # modelos e quantidades
                for key in request.form:
                    if key.startswith(f'endereco_{i}_quantidade'):
                        modelo_id = key.split('_')[-1]
                        quantidade = request.form.get(key)
                        
                        if quantidade:
                            cursor.execute('''
                                INSERT INTO locais_modelos_instalados (local_id, modelo_id, quantidade)
                                VALUES (%s, %s, %s)
                                ''', (local_id, modelo_id, quantidade))
                # instaladores
                instaladores = request.form.getlist(f'endereco_{i}_instaladores')
                for instalados in instaladores:
                    cursor.execute('''
                        INSERT INSTO instaladores_locais (local_id, instalador_id)
                        VALUE (%s, %s)
                        ''', (local_id, instalador_id)) # type: ignore
            conn.commit()
            
            return redirect(url_for('contratos.cadastrar_contrato'))
        # GET para buscar modelos e instaladores
        cursor.execute("SELECT id, nome_marca, fabricante, capacidade_btu FROM modelos_ar_condicionado")
        modelos = cursor.fetchall()

        cursor.execute("SELECT id, nome FROM usuarios WHERE tipo = 'instalador'")
        instaladores = cursor.fetchall()

        return render_template('cad_contratos.html', contrato_id=contrato_id, modelos=modelos, instaladores=instaladores)
    
                    


