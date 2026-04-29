# Classificador Local de SKUs

Versão adaptada para funcionar apenas com base local + dicionário de regex.

## O que mudou

- Removidas as buscas nas APIs Bluesoft/Cosmos e Open Food Facts.
- A base e o dicionário são lidos apenas em memória pelo Streamlit.
- Nenhum arquivo enviado é salvo automaticamente em pasta local.
- O dicionário de exemplo é gerado por botão de download, também em memória.
- É possível escolher:
  - as colunas da base que formarão o texto usado na classificação;
  - as colunas alvo que serão preenchidas pelo dicionário;
  - quais colunas devem ser sobrescritas, se já existirem valores.
- Ao final, o app mostra estatísticas, gráficos e baixa um Excel com:
  - `Base_Classificada`;
  - `Resumo`;
  - `Auditoria`.

## Como rodar

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Formato do dicionário

O dicionário deve ter, no mínimo, estas colunas:

| Coluna | Obrigatória | Exemplo |
|---|---:|---|
| Coluna Alvo | Sim | CATEGORIA |
| Regex | Sim | `\\b(SUCO|NECTAR)\\b` |
| Classificacao | Sim | SUCO |
| Prioridade | Não | 10 |
| Ativo | Não | SIM |
| Observacao | Não | Regra para sucos |

A regra `.*` funciona como fallback da coluna alvo. Ela só é usada se nenhuma regra anterior casar.

## Observação importante

As regex são aplicadas sobre o texto combinado das colunas da base que você selecionar no painel lateral.
