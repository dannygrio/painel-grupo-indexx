# Painel Kobana – Versão 1.3.1 – Atualizado em 26/06/2025 por Danny

import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Painel Grupo Indexx", layout="wide")
st.title("💳 Painel Interno – Boletos Kobana")

# Login por senha via secrets
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    senha_digitada = st.text_input("Digite a senha de acesso", type="password")
    if "auth" not in st.secrets or "senha" not in st.secrets["auth"]:
        st.error("❌ Senha não configurada corretamente nos secrets.")
        st.stop()
    elif senha_digitada == st.secrets["auth"]["senha"]:
        st.session_state["logado"] = True
        st.rerun()
    elif senha_digitada:
        st.warning("Senha incorreta.")
    st.stop()

# Token via secrets
KOBANA_API_KEY = st.secrets["kobana"]["api_token"]

headers = {
    "Authorization": f"Bearer {KOBANA_API_KEY}",  # <- CORRETO no seu ambiente
    "Content-Type": "application/json",
    "User-Agent": "GrupoIndexxApp/1.3.1"
}

# Traduz status da API
def traduz_status(status):
    return {
        "opened": "Em Aberto",
        "paid": "Pago",
        "expired": "Vencido",
        "canceled": "Cancelado"
    }.get(status, status)

# Busca boletos
@st.cache_data(ttl=3600)
def buscar_boletos():
    boletos = []
    pagina = 1
    while True:
        url = "https://api.kobana.com.br/v1/bank_billets"
        params = {"per_page": 100, "page": pagina, "sort": "-created_at"}
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code != 200:
            st.error(f"Erro {r.status_code}: {r.text}")
            return []
        dados = r.json().get("bank_billets", [])
        if not dados:
            break
        boletos.extend(dados)
        if len(dados) < 100:
            break
        pagina += 1
    return boletos

with st.spinner("🔄 Carregando boletos..."):
    dados_api = buscar_boletos()

if st.checkbox("🔍 Mostrar resposta bruta da API"):
    st.json(dados_api)

if not dados_api:
    st.warning("Nenhum boleto retornado da API. Verifique o token.")
    st.stop()

boletos = pd.DataFrame([{
    "Nome": b.get("customer_person_name", ""),
    "CPF/CNPJ": b.get("customer_cnpj_cpf", ""),
    "Status": traduz_status(b.get("status", "")),
    "Valor": float(b.get("amount", 0)) / 100,
    "Data de Vencimento": b.get("expire_at", ""),
    "Data de Pagamento": b.get("paid_at", "")
} for b in dados_api])

# Menu lateral
col1, col2 = st.columns([1, 4])
with col1:
    menu = st.radio("Funções disponíveis", [
        "📊 Resumo Geral",
        "🚨 Clientes com 3 Boletos Vencidos",
        "🧾 Cancelar Assinatura (simulado)",
        "💣 Deletar Boletos (simulado)",
        "📅 Relatório de Pagamentos"
    ])

with col2:
    if menu == "📊 Resumo Geral":
        total = len(boletos)
        pagos = boletos[boletos["Status"] == "Pago"]
        vencidos = boletos[boletos["Status"] == "Vencido"]
        abertos = boletos[boletos["Status"] == "Em Aberto"]
        st.subheader("📊 Resumo Financeiro")
        st.metric("Total de Boletos", total)
        st.metric("Boletos Vencidos", len(vencidos))
        st.metric("Boletos Pagos", len(pagos))
        st.metric("Valor Total Pago", f"R$ {pagos['Valor'].sum():,.2f}".replace(".", ","))
        st.metric("Boletos em Aberto", len(abertos))

    elif menu == "🚨 Clientes com 3 Boletos Vencidos":
        vencidos = boletos[boletos["Status"] == "Vencido"]
        contagem = vencidos["CPF/CNPJ"].value_counts()
        clientes_com_3 = contagem[contagem == 3].index.tolist()
        resultado = boletos[boletos["CPF/CNPJ"].isin(clientes_com_3)]
        st.subheader("🚨 Clientes com 3 Boletos Vencidos")
        st.dataframe(resultado[["Nome", "CPF/CNPJ"]].drop_duplicates())
        st.download_button("📥 Baixar Excel", resultado.to_csv(index=False), "clientes_3_vencidos.csv")

    elif menu == "🧾 Cancelar Assinatura (simulado)":
        st.subheader("🧾 Cancelar Assinatura")
        doc = st.text_input("Digite o CPF ou CNPJ do cliente")
        if st.button("Cancelar"):
            st.success(f"Assinatura cancelada para {doc} (simulado)")

    elif menu == "💣 Deletar Boletos (simulado)":
        st.subheader("💣 Deletar Boletos")
        doc = st.text_input("Digite o CPF ou CNPJ")
        if doc:
            encontrados = boletos[boletos["CPF/CNPJ"] == doc]
            st.dataframe(encontrados)
            if st.button("Deletar todos (simulado)"):
                st.success(f"Boletos de {doc} deletados (simulado)")

    elif menu == "📅 Relatório de Pagamentos":
        pagos = boletos[boletos["Status"] == "Pago"].copy()
        pagos["Data de Pagamento"] = pd.to_datetime(pagos["Data de Pagamento"])
        total = pagos["Valor"].sum()
        st.metric("Total Pago", f"R$ {total:,.2f}".replace(".", ","))
        st.dataframe(pagos)
        st.download_button("📥 Baixar CSV", pagos.to_csv(index=False), "boletos_pagos.csv")
