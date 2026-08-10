# Sistema de Empréstimo de Equipamentos do Laboratório

Sistema web simples para controlar o empréstimo de equipamentos do
laboratório: registra quem pegou o quê, quando deve devolver, permite dar
baixa na devolução e gera um relatório dos empréstimos em atraso. Alunos
com pendência ficam bloqueados para novos empréstimos.

Feito em Python (Flask) com banco de dados SQLite.

## Requisitos

- Python 3.9 ou superior
- pip

Não há outras dependências de sistema — o SQLite já vem embutido no Python
(`sqlite3` é módulo padrão da linguagem).

## Estrutura de pastas esperada

O Flask exige essa organização para encontrar o template e os arquivos
estáticos:

```
projeto/
├── app.py
├── database.db          (criado automaticamente se não existir)
├── templates/
│   └── index.html
└── static/
    └── style.css
```

Se você recebeu os arquivos soltos (fora dessa estrutura), mova
`index.html` para dentro de uma pasta `templates/` e `style.css` para
dentro de uma pasta `static/`, ambas no mesmo nível de `app.py`.

## Instalação

Em um terminal, na pasta do projeto:

```bash
# (opcional, mas recomendado) crie um ambiente virtual
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# instale a única dependência externa
pip install flask
```

## Execução

```bash
python3 app.py
```

Na primeira execução, o `app.py` cria automaticamente o arquivo
`database.db` e as tabelas necessárias (`alunos`, `equipamentos`,
`emprestimos`), caso ainda não existam. Se um `database.db` já vier junto
do projeto, ele é reaproveitado — nenhum dado é apagado.

O servidor sobe em modo de desenvolvimento, por padrão em:

```
http://127.0.0.1:5000
```

Abra esse endereço no navegador. Não é necessário nenhum login.

## Uso

A tela é dividida em duas abas:

- **Gestão de Cadastros** — cadastrar alunos (matrícula + nome) e
  equipamentos (número de série + nome), e ver a lista de cada um.
- **Empréstimos e Devoluções** — registrar um novo empréstimo (escolhendo
  aluno, equipamento já cadastrado e data prevista de devolução), ver os
  empréstimos ativos com botão de "Devolver", e consultar o relatório de
  atrasos.

Regras principais aplicadas pelo sistema:

- Um aluno com qualquer empréstimo em atraso é bloqueado para pegar novos
  equipamentos, até devolver o que está pendente.
- Um equipamento já emprestado (status `Ativo`) não pode ser emprestado de
  novo até ser devolvido.
- A data de devolução prevista não pode ser anterior à data atual.

## Observações técnicas

- O banco impõe integridade referencial (`FOREIGN KEY`) entre empréstimos,
  alunos e equipamentos — não é possível registrar um empréstimo para uma
  matrícula ou número de série que não estejam cadastrados.
- `app.secret_key` está fixo no código como valor de desenvolvimento; para
  qualquer uso além de teste local, substitua por um valor lido de
  variável de ambiente.
- Detalhes de decisões de projeto, premissas assumidas e critérios de
  aceite estão documentados em `DECISOES.md`.