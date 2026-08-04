# Navigation System

## Princípio

A navegação Genesis representa contextos e intenções, não departamentos do
produto. A pessoa deve saber onde está sem conhecer a organização interna do
sistema.

## Estrutura primária

1. **Today** — Command Center e Focus atual.
2. **Projects** — iniciativas e continuidade.
3. **Intelligence** — pedidos, Proposals e trabalhos ativos.
4. **Memory** — contexto vivido e governança.
5. **More** — Missions, Timeline e capacidades especializadas.

**Settings** fica separado no final. Remodeling aparece como Copilot ou dentro
do Project relacionado, não como universo desconectado.

## Workspace switcher

Workspace é a fronteira de contexto mais importante. O seletor mostra nome,
descrição breve e estado. Trocar de Workspace confirma a mudança e atualiza
todo o contexto visível.

## Navegação contextual

Breadcrumbs preservam relações reais:

`Workspace / Project / Proposal`

Não repetir destinos sem significado. Em mobile, mostrar o contexto atual e
permitir regressar um nível por vez.

## Command surface

Uma superfície universal permite encontrar, navegar e iniciar ações por
linguagem natural ou teclado. Resultados agrupam destinos, ações e contexto;
nunca parecem uma lista de comandos técnicos.

## Context persistence

Ao mover-se entre áreas, Genesis preserva Workspace, Project quando aplicável,
filtros relevantes e ponto de retorno. Uma troca intencional de contexto é
sempre perceptível.

## Desktop

Context Rail persistente de 240–272 px, recolhível para ícones com rótulos
acessíveis. Header contextual e conteúdo com largura confortável.

## Tablet

Rail compacto ou overlay; Insight Rail torna-se painel sob demanda. A ação
principal permanece no canvas.

## Mobile

Navegação inferior com Today, Projects, Intelligence e Memory; More contém os
destinos secundários. O contexto aparece num header compacto. Ações críticas não
dependem de hover ou menus escondidos.

## Regras

- máximo de cinco destinos primários visíveis;
- rótulos antes de metáforas;
- localização e Workspace sempre recuperáveis;
- item ativo distinguível além da cor;
- Back devolve ao estado anterior, não a um destino arbitrário;
- nenhum destino chamado “Dashboard” ou “Admin”.
