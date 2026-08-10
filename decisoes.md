# DECISOES.md — Sistema de Empréstimo de Equipamentos do Laboratório

## 1. Decisões assumidas

1. O pedido não especifica se um mesmo equipamento pode existir em mais de uma
   unidade (estoque) ou se cada cadastro representa um item físico único.
   Assumimos que cada equipamento cadastrado é um item físico único (uma
   linha = um objeto real). Se o cliente esperasse controle de estoque
   (várias unidades do mesmo modelo), o impacto seria: adicionar um campo de
   quantidade à tabela `equipamentos`, trocar a checagem "equipamento já
   emprestado" (hoje uma checagem binária por número de série) por uma
   contagem de unidades disponíveis, e mudar a interface de seleção de
   equipamento para seleção de unidade.

2. O pedido não especifica o alcance do bloqueio por atraso ("aluno com
   pendência não pode pegar mais nada"). Assumimos que o bloqueio é geral:
   qualquer atraso do aluno, em qualquer equipamento, impede qualquer novo
   empréstimo. Se o cliente esperasse um bloqueio restrito ao equipamento em
   atraso, o impacto seria: alterar a função `aluno_tem_atraso` para receber
   também o número de série pretendido e filtrar a consulta por esse campo.

3. O pedido não define quem registra a devolução. Assumimos que é o técnico
   (ou qualquer pessoa com acesso à tela), manualmente, pelo botão
   "Devolver" — não há autoidentificação do aluno nem devolução automática
   por vencimento de prazo. Se o cliente esperasse que o próprio aluno desse
   baixa remotamente, o impacto seria: adicionar autenticação por aluno e um
   registro de auditoria de quem executou cada devolução.

4. O pedido não define uma data de devolução prevista fixa. Assumimos que
   essa data é escolhida livremente no momento do empréstimo (campo
   obrigatório no formulário). Se o cliente esperasse um prazo padrão fixo
   (ex.: 7 dias corridos), o impacto seria: remover o campo de data do
   formulário e calculá-la automaticamente a partir da data do empréstimo,
   com uma constante de configuração para o prazo.

5. O pedido não define tolerância para atraso. Assumimos atraso = qualquer
   dia após a data prevista, sem carência. Se o cliente esperasse uma
   tolerância (ex.: 1 dia de carência), o impacto seria: alterar as
   consultas de atraso (em `aluno_tem_atraso` e na rota `/`) para comparar
   contra `data_devolucao_prevista + N dias` em vez da data prevista pura.

6. O pedido não define o que ocorre no cadastro duplicado (mesma matrícula
   ou mesmo número de série enviados de novo). Assumimos que cadastro é
   somente inserção: uma segunda tentativa com a mesma chave é rejeitada
   (erro de integridade do banco) e nada é alterado no registro existente.
   Se o cliente esperasse que reenviar atualizasse o nome cadastrado, o
   impacto seria: trocar o `INSERT` por um `INSERT ... ON CONFLICT DO
   UPDATE` (upsert) nas rotas de cadastro.

7. O pedido não define se alunos e equipamentos podem ser editados ou
   excluídos após o cadastro. Assumimos que não — não há rota de edição nem
   de exclusão, apenas de inserção. Se o cliente esperasse corrigir um erro
   de digitação (ex.: nome errado) sem recriar o registro, o impacto seria:
   criar rotas `/editar_aluno` e `/editar_equipamento` e as telas
   correspondentes.

8. O pedido não define o identificador interno das entidades. Usamos a
   matrícula e o número de série como chave primária (chave natural) das
   tabelas `alunos` e `equipamentos`, em vez de um ID numérico próprio do
   banco. Se o cliente esperasse alterar matrícula ou número de série depois
   de cadastrado (ex.: correção de digitação), o impacto seria alto: como
   esses campos são referenciados por chave estrangeira em `emprestimos`,
   trocar de chave natural para um ID substituto exigiria migrar o esquema
   inteiro e todos os empréstimos já registrados.

9. O pedido não define quantos empréstimos simultâneos um mesmo aluno pode
   ter. Assumimos que não há limite (um aluno sem atraso pode pegar quantos
   equipamentos diferentes quiser, um de cada vez). Se o cliente esperasse
   um limite (ex.: no máximo 2 equipamentos por aluno), o impacto seria:
   adicionar uma contagem de empréstimos ativos do aluno na validação da
   rota `/adicionar_emprestimo`.

10. O pedido não define comportamento para concorrência (dois técnicos
    tentando emprestar o último equipamento disponível ao mesmo tempo).
    Assumimos volume de uso baixo (laboratório pequeno, poucos acessos
    simultâneos) e não implementamos travamento explícito além do que o
    SQLite oferece por padrão. Se o cliente esperasse uso concorrente
    intenso, o impacto seria: mover para um banco com controle de
    concorrência mais robusto (ex.: PostgreSQL) e/ou usar transações
    explícitas com `SELECT ... FOR UPDATE` equivalente.

11. O pedido não define validação de formato para matrícula e número de
    série. Assumimos qualquer texto não vazio como válido (a única
    restrição aplicada é o atributo HTML `required`, sem validação no
    servidor). Se o cliente esperasse rejeitar formatos inválidos (ex.:
    matrícula com letras, ou com espaços à frente que criem duplicatas
    "diferentes" para o mesmo aluno), o impacto seria: adicionar validação
    server-side (regex/normalização com `strip()`) antes do `INSERT`.

12. O pedido não define o que aparece na tela para equipamentos disponíveis
    versus emprestados. Assumimos que basta a lista de "Equipamentos
    Emprestados Atualmente" (quem tem o quê); a lista de "Equipamentos
    Cadastrados" não indica status de disponibilidade. Se o cliente
    esperasse ver rapidamente, na própria lista de cadastro, quais
    equipamentos estão disponíveis, o impacto seria: fazer um `LEFT JOIN`
    entre `equipamentos` e `emprestimos` ativos e exibir uma coluna de
    status na tabela de cadastro.

13. Adicionamos, nesta versão, a coluna `data_devolucao_real` e a rota de
    devolução, que não existiam no código original recebido (ver §4). O
    pedido não especifica se a data de devolução real deve poder ser
    retroativa (ex.: técnico esqueceu de registrar e faz isso dois dias
    depois). Assumimos que a data de devolução real é sempre a data do
    servidor no momento do clique em "Devolver", sem opção de backdating.
    Se o cliente esperasse poder informar uma data passada, o impacto
    seria: adicionar um campo de data editável no formulário de devolução
    em vez de usar `date.today()` automaticamente.

## 2. Perguntas ao cliente

1. **Um mesmo equipamento cadastrado representa sempre uma unidade física
   única, ou pode haver várias unidades iguais (estoque) sob o mesmo
   cadastro?**
   - Resposta A — unidade única: o sistema atual já atende, nenhuma
     mudança necessária.
   - Resposta B — múltiplas unidades: seria necessário adicionar controle
     de quantidade/estoque por equipamento e reformular a lógica de
     "equipamento disponível", hoje binária (emprestado ou não).

2. **O bloqueio por pendência deve valer para qualquer atraso do aluno, ou
   apenas quando o atraso é do mesmo equipamento que ele está tentando
   pegar de novo?**
   - Resposta A — bloqueio geral (o que foi implementado): nenhuma mudança.
   - Resposta B — bloqueio específico por equipamento: a consulta de
     verificação de atraso precisaria ser filtrada também pelo número de
     série do equipamento pretendido, permitindo que o aluno pegue outros
     itens mesmo estando em atraso com um item específico.

3. **A devolução deve ser registrada apenas pelo técnico do laboratório
   (presencialmente, no computador do laboratório), ou o próprio aluno deve
   poder dar baixa remotamente?**
   - Resposta A — apenas o técnico (o que foi assumido): o sistema atual,
     sem login, já atende.
   - Resposta B — o aluno também pode devolver remotamente: seria
     necessário implementar autenticação de usuários e um registro de
     auditoria (quem registrou cada devolução), hoje inexistente.

## 3. Critérios de aceite

1. Um aluno cadastrado com um empréstimo ativo cuja `data_devolucao_prevista`
   é anterior à data atual, ao submeter o formulário de novo empréstimo para
   qualquer equipamento, recebe a mensagem "BLOQUEADO: O aluno possui
   empréstimos em atraso!" e nenhuma nova linha é criada na tabela
   `emprestimos`.

2. Um equipamento com um registro em `emprestimos` cujo `status` é `'Ativo'`,
   ao ser selecionado no formulário de novo empréstimo por qualquer aluno
   (inclusive um aluno diferente do atual tomador), gera a mensagem "ERRO:
   Este equipamento já se encontra emprestado!" e nenhuma nova linha é
   criada na tabela `emprestimos`.

3. Ao submeter o formulário do botão "Devolver" de um empréstimo com
   `status = 'Ativo'`, o registro correspondente passa a ter `status =
   'Devolvido'` e `data_devolucao_real` preenchida com a data atual; esse
   empréstimo deixa de aparecer na tabela "Equipamentos Emprestados
   Atualmente"; e, se esse era o único empréstimo em atraso do aluno, um
   novo empréstimo para esse mesmo aluno deixa de ser bloqueado.

## 4. Decisões da ferramenta de IA

1. **Chave secreta fixa no código (`app.secret_key = 'chave_secreta_laboratorio'`).**
   Essa linha já vinha no código-base recebido, sem que tivesse sido pedida
   explicitamente uma estratégia de configuração de segredo. É uma decisão
   plausível para um protótipo local de laboratório, mas é inadequada para
   qualquer cenário de implantação real: qualquer pessoa com acesso ao
   repositório vê a chave, o que compromete a assinatura das mensagens
   `flash` e de eventuais sessões futuras. O correto seria ler o segredo de
   uma variável de ambiente, com um valor gerado aleatoriamente como
   fallback local.

2. **Uso de matrícula e número de série como chave primária (chave natural)
   das tabelas `alunos` e `equipamentos`, em vez de um `id` autoincrementado
   próprio do banco.** Essa é uma decisão razoável para simplificar as
   consultas e evitar um JOIN a mais, mas é frágil: se a matrícula de um
   aluno for digitada errada no cadastro, não há como corrigi-la sem apagar
   e recriar o aluno (e, com ele, perder a referência de qualquer
   empréstimo já feito por causa da chave estrangeira). Um `id` substituto,
   com a matrícula como campo único porém editável, seria mais seguro para
   esse cenário de uso.

3. **Forma de bloquear a data de devolução prevista retroativa.** Foi
   solicitado à IA que corrigisse a ausência de validação server-side da
   data de devolução prevista (até então só existia a restrição
   client-side `min=""` no HTML, contornável por um POST direto). O pedido
   foi genérico ("aplique as correções necessárias"); a IA decidiu, sem
   isso ter sido especificado, **rejeitar totalmente** a submissão quando
   `data_devolucao < data_hoje`, devolvendo o usuário ao formulário com uma
   mensagem de erro — em vez de, por exemplo, aceitar a data mas exibir um
   aviso, ou truncar automaticamente para a data mínima válida. Essa é uma
   decisão plausível (é o comportamento mais seguro contra dado inválido),
   mas pode ser inadequada se o cliente preferisse tolerância maior no
   formulário (ex.: permitir o técnico corrigir manualmente depois) em vez
   de recusa dura. Da mesma forma, a checagem de integridade referencial
   (`PRAGMA foreign_keys = ON` reativada em toda conexão, via função
   `get_conn()`) passou a **rejeitar com erro não tratado** qualquer
   tentativa de inserir um empréstimo com matrícula ou número de série
   inexistentes — hoje isso resultaria em erro 500 sem mensagem amigável ao
   usuário, pois não havia (nem foi pedido) tratamento de exceção para essa
   condição. Isso é adequado para blindar a integridade dos dados, mas
   precisaria de um `try/except sqlite3.IntegrityError` com uma mensagem
   `flash` amigável para não quebrar a experiência do usuário em produção.

## Registro de tempo

Horas escrevendo ou gerando código: ___  Tiago: 1 hora
Horas decidindo o que o sistema deveria fazer: ___ Tiago: 1 hora

*(preencher com a estimativa honesta da dupla — não compõe a nota)*

## 5. Declaração de uso de IA

Foram utilizados os assistentes **Claude (Anthropic)** e **Gemini (Google)**, via chat, para: analisar o
código-base fornecido frente ao pedido original e identificar lacunas;
implementar a rota de devolução de empréstimos (`/devolver_emprestimo`, com a
respectiva migração de coluna `data_devolucao_real` e o botão correspondente
no template); reorganizar os arquivos na estrutura de pastas exigida pelo
Flask (`templates/`, `static/`); e redigir a primeira versão deste
`DECISOES.md` a partir da leitura do enunciado e do código.
A utilização de ambos os chats foi escolhida a fim de validar a eficiência 
de um dos modelos com o outro. Assim garantindo que um dos assistentes não
tenha deixado algum ponto central faltando ou errado.

O que foi verificado manualmente: *(a dupla deve completar este item de
acordo com o que de fato testou antes da entrega — por exemplo: execução do
`app.py` em máquina limpa, teste manual de cada um dos três critérios de
aceite pela interface, revisão linha a linha do `app.py` e do `index.html`.)*
A responsabilidade técnica pelo que está sendo entregue é da dupla.

O que foi verificado manualmente: execução do `app.py` em mais de uma máquina,
visando validar a funcionalidade da aplicação e o cumprimento dos critérios
estabelicidos pela atividade.