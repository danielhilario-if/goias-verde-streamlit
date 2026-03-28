# Produto Streamlit - Projeto Goiás Verde

Esta pasta contem a versao do produto Streamlit para o projeto Goiás Verde.

## Estrutura

- `app.py`: interface principal do produto
- `src/pages/`: modulos de cada tela do produto
- `src/components/`: componentes compartilhados de interface e selecao de dataset
- `src/config/`: configuracoes de navegacao, estilos e defaults
- `src/auth.py`: autenticacao Supabase e sessao de login
- `src/ml/`: registro e montagem dinamica dos modelos de regressao
- `src/state.py`: cache e estado compartilhado da sessao
- `src/pipeline.py`: funcoes de carregamento e processamento
- `assets/logo_CEAGRE.avif`: logo usado na interface
- `requirements.txt`: dependencias do app
- `tests/`: testes automatizados (`pytest`)

## Python

Este app deve ser executado com Python `3.10`.

## Como criar o ambiente

```bash
cd produto_streamlit
python3.10 -m venv .venv
source .venv/bin/activate
pip install -U pip wheel
pip install -r requirements.txt
```

## Como rodar

```bash
source .venv/bin/activate
python -m streamlit run app.py
```

> Use sempre `python -m streamlit` para garantir que o Streamlit do `.venv` e utilizado.

## Como rodar os testes

```bash
source .venv/bin/activate
pytest tests/ -v
```

## Dados

O produto foi mantido desacoplado de caminhos fixos. O fluxo esperado e enviar o CSV ou Excel pela aba `Upload`.

Se quiser testar com o arquivo existente no workspace, ele esta em:

- `../data/Dados_Fluxo_Solo_RIO VERDE.xlsx`

## Login com Supabase

Para ativar o login:

1. Copie `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml`
2. Preencha `url` e `publishable_key` do seu projeto Supabase
3. Reinicie o app

Exemplo:

```toml
[supabase]
enabled = true
url = "https://SEU-PROJETO.supabase.co"
publishable_key = "SUA_CHAVE_PUBLISHABLE"
admin_emails = ["admin@dominio.com"]
# allow_signup = true  # defina false para desabilitar o auto-cadastro
```

Use a chave `publishable` ou `anon`, nunca a `service_role`.

### Alternativa: variaveis de ambiente

Em vez do `secrets.toml`, voce pode exportar as seguintes variaveis antes de rodar:

```bash
export SUPABASE_URL="https://SEU-PROJETO.supabase.co"
export SUPABASE_PUBLISHABLE_KEY="SUA_CHAVE_PUBLISHABLE"
python -m streamlit run app.py
```
