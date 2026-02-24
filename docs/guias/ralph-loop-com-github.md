# Usando o Ralph Loop com Versionamento no GitHub

> **Área:** guias
> **Última atualização:** Fevereiro de 2026

## Objetivo

Este guia descreve como usar o plugin Ralph Loop de forma segura e rastreável, integrando commits, branches e pull requests no GitHub a cada ciclo de desenvolvimento autônomo. O objetivo é garantir que o código gerado autonomamente seja revisável, reversível e auditável — sem abrir mão da velocidade que o Ralph proporciona.

---

## Como funciona

O Ralph Loop executa o Claude Code em ciclos contínuos até que um critério de conclusão seja atingido. Sem disciplina de versionamento, isso pode resultar em centenas de linhas de código sem histórico rastreável, difíceis de revisar ou reverter.

A estratégia correta é:

```
branch isolada → Ralph executa → commits incrementais → PR para revisão → merge em main
```

Cada milestone do projeto recebe sua própria branch. O Ralph commita ao final de cada tarefa concluída. Você revisa o PR antes de qualquer merge.

---

## Fluxo completo por milestone

### 1. Antes de iniciar o loop

Certifique-se de que `main` está limpo e atualizado:

```bash
git checkout main
git pull origin main
git status  # deve retornar "nothing to commit"
```

Crie uma branch dedicada ao milestone:

```bash
git checkout -b feat/m1-fundacao
# ou
git checkout -b feat/m2-agente-renovacao
git checkout -b feat/m3-agente-sinistros
```

### 2. Configure o ralph_prompt.md para commitar

O `ralph_prompt.md` já instrui o Claude a fazer commit ao final de cada tarefa. Confirme que a instrução de commit está presente e segue a convenção:

```
git add . && git commit -m "feat(<scope>): <descrição em pt-BR>"
```

Nunca instrua o Ralph a fazer `git push` automaticamente — o push deve ser sempre manual e consciente.

### 3. Inicie o loop na branch correta

```bash
# Confirme que está na branch certa antes de rodar
git branch  # deve mostrar * feat/m1-fundacao

/ralph-loop "Leia ralph_prompt.md e implemente o M1 completo" --max-iterations 25 --completion-promise "M1_CONCLUIDO"
```

### 4. Durante a execução

Você pode acompanhar o progresso sem interromper:

```bash
# Em outro terminal, acompanhe os commits sendo criados
git log --oneline

# Veja o que está sendo modificado em tempo real
git status
```

Se precisar cancelar:
```
/cancel-ralph
```

O estado ficará no último commit feito — nada é perdido.

### 5. Após o loop concluir

Revise tudo que foi gerado antes de qualquer push:

```bash
# Veja todos os commits criados pelo Ralph
git log --oneline main..HEAD

# Revise as mudanças completas em relação a main
git diff main...HEAD

# Rode os testes uma última vez para confirmar que está tudo verde
docker compose exec api pytest tests/ -v
docker compose exec api ruff check .
docker compose exec api mypy .
```

### 6. Abra o Pull Request

Só faça push após a revisão:

```bash
git push -u origin feat/m1-fundacao
```

Crie o PR via GitHub CLI:

```bash
gh pr create \
  --title "feat(m1): fundação — FastAPI, banco, webhooks e Z-API" \
  --body "$(cat <<'EOF'
## Contexto
Implementação do M1 conforme arquitetura definida em architecture.md.
Gerado via Ralph Loop com revisão manual antes do merge.

## O que mudou
- Docker Compose com API, PostgreSQL e Redis
- Migrations iniciais (clients, policies, claims, conversations)
- Rotas /webhook/whatsapp e /scheduler/renewal-check
- Integração básica Z-API

## Como testar
- [ ] `docker compose up` sobe sem erros
- [ ] `pytest tests/` passa com 0 falhas
- [ ] Webhook recebe mensagem de teste do Z-API

Closes #<número-da-issue>
EOF
)"
```

### 7. Revisão e merge

Revise o PR como qualquer outro — o fato de ter sido gerado autonomamente não muda o critério:

- Os testes passam?
- O código segue as convenções do `CLAUDE.md`?
- Alguma regra de negócio de `project_spec.md` foi violada?
- Dados sensíveis estão sendo tokenizados corretamente?
- `emit_policy` está desabilitado?

Aprovado, faça squash merge para manter o histórico de `main` limpo:

```bash
gh pr merge --squash
```

---

## Estratégia de branches por milestone

```
main
 └── feat/m1-fundacao          ← Ralph roda aqui
      └── (PR aprovado → squash merge → main)
 └── feat/m2-agente-renovacao  ← Ralph roda aqui (após M1 merged)
      └── (PR aprovado → squash merge → main)
 └── feat/m3-agente-sinistros  ← Ralph roda aqui (após M2 merged)
      └── (PR aprovado → squash merge → main)
```

**Nunca rode o Ralph diretamente em `main`.** Se algo der errado, você perde a possibilidade de reverter sem afetar o histórico principal.

---

## Recuperação em caso de problema

### O loop gerou código ruim e preciso voltar atrás

```bash
# Veja os commits disponíveis
git log --oneline

# Volte para um commit específico (mantém as mudanças como unstaged)
git reset <hash-do-commit-bom>

# Ou descarte tudo desde o último commit bom (irreversível)
git reset --hard <hash-do-commit-bom>
```

### O loop travou no meio e quero continuar

A branch mantém todos os commits feitos até o travamento. Basta rodar o Ralph novamente na mesma branch — ele vai ler o `project_status.md` e continuar do ponto onde parou:

```bash
/ralph-loop "Leia ralph_prompt.md e continue a implementação do M1, verificando o project_status.md para identificar o que falta" --max-iterations 15 --completion-promise "M1_CONCLUIDO"
```

### O loop fez commit de algo que não deveria (ex: credenciais)

```bash
# Remova o arquivo do histórico de commits
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push na branch (nunca em main)
git push origin feat/m1-fundacao --force
```

---

## Configuração do GitHub para proteção

Garanta que as seguintes proteções estejam ativas no repositório antes de começar:

```
Repositório → Settings → Branches → Branch protection rules → main
```

- [x] Require a pull request before merging
- [x] Require approvals (mínimo 1)
- [x] Require status checks to pass (CI com pytest + ruff)
- [x] Do not allow bypassing the above settings

Isso impede que qualquer push direto em `main` aconteça — mesmo que o Ralph tente.

---

## Limitações conhecidas

- O Ralph não abre PRs automaticamente — o push e a criação do PR são sempre manuais e intencionais.
- `--completion-promise` usa correspondência exata de string — se o Claude escrever a promise com formatação diferente, o loop não encerra.
- Loops sem `--max-iterations` rodam indefinidamente e não podem ser pausados, apenas cancelados com `/cancel-ralph`.
- O Ralph não faz `git rebase` — se `main` avançou durante a execução do loop, você precisará fazer o rebase manualmente antes do PR.
