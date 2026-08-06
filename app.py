from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import date

app = Flask(__name__)
app.secret_key = 'chave_secreta_laboratorio'

def init_db():
    conn = sqlite3.connect('database.db')
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alunos (
            matricula TEXT PRIMARY KEY,
            nome TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipamentos (
            numero_serie TEXT PRIMARY KEY,
            nome TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emprestimos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula_aluno TEXT NOT NULL,
            numero_serie_equipamento TEXT NOT NULL,
            data_emprestimo DATE NOT NULL,
            data_devolucao_prevista DATE NOT NULL,
            status TEXT DEFAULT 'Ativo',
            FOREIGN KEY (matricula_aluno) REFERENCES alunos(matricula),
            FOREIGN KEY (numero_serie_equipamento) REFERENCES equipamentos(numero_serie)
        )
    ''')
    conn.commit()
    conn.close()

def aluno_tem_atraso(matricula):
    hoje = date.today().isoformat()
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM emprestimos
        WHERE matricula_aluno = ? AND status = 'Ativo' AND data_devolucao_prevista < ?
    ''', (matricula, hoje))
    atrasos = cursor.fetchone()[0]
    conn.close()
    return atrasos > 0

# Rota Principal: Carrega a página e as listas para os menus suspensos
@app.route('/')
def index():
    hoje = date.today().isoformat()
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Buscar lista de alunos cadastrados
    cursor.execute("SELECT matricula, nome FROM alunos")
    lista_alunos = cursor.fetchall()
    
    # Buscar lista de equipamentos cadastrados
    cursor.execute("SELECT numero_serie, nome FROM equipamentos")
    lista_equipamentos = cursor.fetchall()
    
    # Buscar empréstimos ativos
    cursor.execute('''
        SELECT e.id, e.matricula_aluno, e.numero_serie_equipamento, e.data_emprestimo, e.data_devolucao_prevista
        FROM emprestimos e WHERE e.status = 'Ativo'
    ''')
    emprestimos = cursor.fetchall()
    
    # Buscar atrasos
    cursor.execute('''
        SELECT e.matricula_aluno, e.numero_serie_equipamento, e.data_devolucao_prevista
        FROM emprestimos e WHERE e.status = 'Ativo' AND e.data_devolucao_prevista < ?
    ''', (hoje,))
    atrasos = cursor.fetchall()
    
    conn.close()
    return render_template('index.html', 
                           lista_alunos=lista_alunos, 
                           lista_equipamentos=lista_equipamentos, 
                           emprestimos=emprestimos, 
                           atrasos=atrasos, 
                           data_hoje=hoje)

# Rota para cadastrar Aluno separadamente
@app.route('/adicionar_aluno', methods=['POST'])
def adicionar_aluno():
    matricula = request.form['matricula']
    nome = request.form['nome']
    
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO alunos (matricula, nome) VALUES (?, ?)', (matricula, nome))
        conn.commit()
        conn.close()
        flash('Aluno cadastrado com sucesso!', 'sucesso')
    except sqlite3.IntegrityError:
        flash('Erro: Já existe um aluno cadastrado com esta matrícula.', 'erro')
        
    return redirect(url_for('index'))

# Rota para cadastrar Equipamento separadamente
@app.route('/adicionar_equipamento', methods=['POST'])
def adicionar_equipamento():
    numero_serie = request.form['numero_serie']
    nome_eq = request.form['nome_eq']
    
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO equipamentos (numero_serie, nome) VALUES (?, ?)', (numero_serie, nome_eq))
        conn.commit()
        conn.close()
        flash('Equipamento cadastrado com sucesso!', 'sucesso')
    except sqlite3.IntegrityError:
        flash('Erro: Já existe um equipamento com este número de série.', 'erro')
        
    return redirect(url_for('index'))

# Rota para registrar o Empréstimo usando os itens já cadastrados
@app.route('/adicionar_emprestimo', methods=['POST'])
def adicionar_emprestimo():
    matricula = request.form['matricula']
    num_serie = request.form['numero_serie']
    data_devolucao = request.form['data_devolucao']
    data_hoje = date.today().isoformat()

    # Validação 1: Aluno com atraso
    if aluno_tem_atraso(matricula):
        flash('BLOQUEADO: O aluno possui empréstimos em atraso!', 'erro')
        return redirect(url_for('index'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Validação 2: Equipamento já emprestado
    cursor.execute('''
        SELECT COUNT(*) FROM emprestimos 
        WHERE numero_serie_equipamento = ? AND status = 'Ativo'
    ''', (num_serie,))
    
    if cursor.fetchone()[0] > 0:
        conn.close()
        flash('ERRO: Este equipamento já se encontra emprestado!', 'erro')
        return redirect(url_for('index'))

    # Realiza o empréstimo
    cursor.execute('''
        INSERT INTO emprestimos (matricula_aluno, numero_serie_equipamento, data_emprestimo, data_devolucao_prevista, status)
        VALUES (?, ?, ?, ?, 'Ativo')
    ''', (matricula, num_serie, data_hoje, data_devolucao))
    
    conn.commit()
    conn.close()
    
    flash('Empréstimo realizado com sucesso!', 'sucesso')
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)