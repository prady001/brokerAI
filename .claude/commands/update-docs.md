Update the documentation for a feature in this project.

## Instructions

1. Identify the feature to document based on the user's argument: $ARGUMENTS
   - If no argument is provided, ask the user which feature or area should be documented.

2. Search the codebase for all files related to the feature (agents, services, routes, models, tools).

3. Read the existing documentation file at `docs/<area>/<feature-name>.md` if it exists.

4. Write or update the documentation file following this exact structure in **pt-BR**:

```markdown
# <Nome da Funcionalidade>

> **Área:** <agentes | api | services | models>
> **Última atualização:** <current date>

## Objetivo
<What the feature does and why it exists. 2–4 sentences.>

## Como funciona
<Step-by-step description of the flow or logic. Use numbered lists or diagrams where helpful.>

## Configuração
<Any environment variables, parameters, or flags required. Reference .env variable names.>

## Exemplos
<At least one concrete example: a message flow, an API call, a tool invocation, etc.>

## Limitações conhecidas
<Edge cases, intentional restrictions, or known issues. Reference relevant ADRs if applicable.>
```

5. After writing the documentation, update `project_status.md`:
   - Mark the related checklist item as completed (`- [x]`) if it exists.
   - If no checklist item exists, add one under the appropriate milestone and mark it complete.

6. Confirm to the user which files were created or updated.
