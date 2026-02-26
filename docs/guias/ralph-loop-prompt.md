# Ralph Loop — brokerAI

## Contexto
Você está desenvolvendo o brokerAI, um sistema de agentes de IA para uma corretora de seguros brasileira.
Toda a arquitetura, regras de negócio e modelo de dados estão documentados em:
- `architecture.md` — arquitetura técnica completa e ADRs
- `project_spec.md` — especificação de produto e regras de negócio
- `CLAUDE.md` — convenções do projeto
- `project_status.md` — o que já foi feito e o que falta

## Fluxo de trabalho por iteração

1. Leia `project_status.md` para identificar a próxima tarefa não concluída
2. Implemente a tarefa seguindo as convenções do `CLAUDE.md`
3. Escreva testes para o que foi implementado
4. Rode os testes: `docker compose exec api pytest tests/ -v`
5. Corrija erros até os testes passarem
6. Rode o lint: `docker compose exec api ruff check . && mypy .`
7. Atualize `project_status.md` marcando a tarefa como concluída `[x]`
8. Crie a documentação em `docs/<area>/<feature>.md`
9. Faça commit: `git add . && git commit -m "feat(<scope>): <descrição em pt-BR>"`
10. Repita para a próxima tarefa

## Critério de conclusão
Quando todas as tarefas do M1 em `project_status.md` estiverem marcadas como `[x]`, escreva:
<promise>M1_CONCLUIDO</promise>

## Restrições importantes
- Todo texto para o usuário final em português (pt-BR)
- `emit_policy` deve estar desabilitado (retornar NotImplementedError)
- Nenhuma ação irreversível sem aprovação humana
- Dados sensíveis (CPF, financeiros) nunca entram no histórico do LLM — usar tokens
