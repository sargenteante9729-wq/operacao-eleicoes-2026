# Operação Eleições 2026 — Mapa de Ocorrências

Projeto para publicação no GitHub Pages, com atualização automática das ocorrências a partir do Google Sheets.

## Estrutura — NÃO RENOMEAR

```text
operacao-eleicoes-2026/
├── .github/
│   └── workflows/
│       └── sync-google-sheet.yml
├── data/
│   └── ocorrencias.json
├── scripts/
│   └── sync_sheet.py
├── index.html
├── README.md
├── .nojekyll
└── .gitignore
```

## Publicação

1. Crie um repositório vazio no GitHub.
2. Envie **todo o conteúdo desta pasta** para a raiz do repositório.
3. Não renomeie `.github`, `workflows`, `data`, `scripts` ou os arquivos.
4. Em Settings > Pages, selecione `Deploy from a branch`, branch `main`, pasta `/ (root)`.
5. Em Actions, o workflow **Sincronizar ocorrencias** pode ser executado manualmente com `Run workflow`.

## Atualização

O GitHub Actions consulta a planilha publicada a cada 5 minutos e grava os dados em:

`data/ocorrencias.json`

O mapa consulta esse arquivo, evitando acesso direto do navegador ao Google Sheets.

## Privacidade

O arquivo sincronizado contém apenas campos operacionais do mapa. Não publique nomes, matrículas, CPF/RG ou relatos sensíveis em um repositório público.
