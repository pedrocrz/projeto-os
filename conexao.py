from flask import Flask, render_template
import pymysql

app = Flask(__name__)

#configuração da conexão

def conectar():
    return pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='#Peixe153',
        database='sistema_instalacoes',
        cursorclass=pymysql.cursors.DictCursor
        )

#@app.route('/')
#def index():
    with conexao.cursor() as cursor:
        cursor.execute('SELECT NOW() AS hora')
        resultado = cursor.fetchone()
    return f'Hora atual no banco: {resultado['hora']}'

#if __name__ == '__main__':
    app.run(debug=True)