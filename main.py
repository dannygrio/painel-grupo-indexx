# Painel Executivo – Versão 26/06/2025 por Danny

import streamlit as st
import pandas as pd
import requests

# Configuração do app
st.set_page_config(page_title="Painel Executivo – Boletos Kobana", layout="centered")
st.title("📊 Painel Executivo – Boletos Ativos (Kobana)")

# Login com senha armazenada no secrets
senha_correta = st.secrets["auth"]["senha"]
senha_digitada = st.text_input("Digite a senha para acessar o painel", type="password")
if senha_digitada != senha_correta:
    st.stop()

# Token e endpoint da API Kobana
KOBANA_API_KEY = st.secrets["kobana"]["api_token"]
headers = {
    "Accept": "application/json",
    "Authorization": f"Token {KOBANA_API_KEY}"
}

# Paginação de boletos com status 'opened' e 'overdue'
def buscar_boletos(status):
    boletos = []
    pagina = 1
    while True:
        url = f"https://api.kobana.com.br/v1/bank_billets?status[]={status}&page={pagina}"
        resposta = requests.get(url, headers=headers)
        if resposta.status_code != 200:
            break
        dados = resposta.json()
        boletos.extend(dados)
        if len(dados) < 100:
            break
        pagina += 1
    return boletos

# Buscar boletos ativos (opened e overdue)
boletos_abertos = buscar_boletos("opened")
boletos_vencidos = buscar_boletos("overdue")
ativos = boletos_abertos + boletos_vencidos

# Exibir indicadores
col1, col2, col3 = st.columns(3)
col1.metric("👥 Boletos em Aberto", len(boletos_abertos))
col2.metric("⚠️ Boletos Vencidos", len(boletos_vencidos))

# Calcular inadimplência ativa
total_boletos_ativos = len(ativos)
inadimplentes_pct = 0.0
clientes_inadimplentes = pd.DataFrame()

if boletos_vencidos:
    df_vencidos = pd.DataFrame([{
        "Nome": b["customer_person_name"],
        "CPF/CNPJ": b["customer_person_document"]
    } for b in boletos_vencidos])

    inadimplentes = (
        df_vencidos.groupby(["Nome", "CPF/CNPJ"])
        .size()
        .reset_index(name="Qtd Vencidos")
    )
    clientes_inadimplentes = inadimplentes[inadimplentes["Qtd Vencidos"] >= 3]
    inadimplentes_pct = (len(clientes_inadimplentes) / total_boletos_ativos) * 100

col3.metric("📊 Inadimplência Ativa", f"{inadimplentes_pct:.2f}%")

# Tabela de clientes com 3 vencidos
st.markdown("### 🚨 Clientes com 3 Boletos Vencidos")
st.dataframe(clientes_inadimplentes[["Nome", "CPF/CNPJ"]], use_container_width=True)
st.download_button(
    "📥 Baixar lista CSV",
    clientes_inadimplentes.to_csv(index=False).encode("utf-8"),
    "clientes_inadimplentes.csv",
    "text/csv"
)

# Tabela completa dos boletos ativos
st.markdown("### 📋 Boletos Ativos (Opened + Overdue)")
df_boletos = pd.DataFrame([{
    "Nome": b["customer_person_name"],
    "CPF/CNPJ": b["customer_person_document"],
    "Status": b["status"],
    "Valor (R$)": float(b["amount"]),
    "Vencimento": b["expire_at"],
    "Tag": b["tags"][0] if b["tags"] else ""
} for b in ativos])

st.dataframe(df_boletos, use_container_width=True)

st.download_button(
    "📥 Exportar todos os boletos (CSV)",
    df_boletos.to_csv(index=False).encode("utf-8"),
    "boletos_ativos.csv",
    "text/csv"
)
