# Simulador Kobana – Versão 1.1.1 – Atualizado em 26/06/2025 por Danny

import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Painel Grupo Indexx", layout="wide")
st.markdown("## 💳 Painel Interno – Boletos Kobana")

# Campo de senha para colar o token da API (funciona como login)
token = st.text_input("Cole aqui o token da API da Kobana", type="password")
if not token:
    st.warning("🔐 É necessário colar o token da API para continuar.")
    st.stop()

# Cabeçalhos para autenticação correta
headers = {
    "Authorization": f"Token token={token}"
}

# Parâmetros da consulta
params = {
    "status": "overdue",  # Pode ser 'paid', 'pending', etc
    "per_page": 100       # Máximo por página
}

# Chamada real à API
with st.spinner("🔄 Buscando boletos vencidos..."):
    resposta = requests.get("https://api.kobana.com.br/v1/bank_billets", headers=headers, params=params)

# Verificação da resposta
if resposta.status_code != 200:
    st.error(f"Erro {resposta.status_code} ao consultar a API: {resposta.text}")
    st.stop()

# Conversão para DataFrame
dados = resposta.json()
boletos = dados if isinstance(dados, list) else dados.get("bank_billets", [])

if not boletos:
    st.info("Nenhum boleto vencido encontrado.")
else:
    df = pd.json_normalize(boletos)
    st.success(f"✅ {len(df)} boletos encontrados.")
    st.dataframe(df[["id", "customer_name", "amount", "status", "due_at"]])
