# Painel Grupo Indexx – Versão 1.1.0 – Atualizado em 25/06/2025 por Danny

import streamlit as st
import pandas as pd
import requests

# Configuração do Streamlit
st.set_page_config(page_title="Painel Grupo Indexx", layout="wide")

# ----- LOGIN -----
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    st.markdown("## 🔐 Painel Interno – Gestão Grupo Indexx")
    senha_digitada = st.text_input("Digite a senha de acesso", type="password")
    if "auth" not in st.secrets or "senha" not in st.secrets["auth"]:
        st.error("❌ Senha não configurada corretamente no arquivo de secrets.")
        st.stop()
    elif senha_digitada == st.secrets["auth"]["senha"]:
        st.session_state["logado"] = True
        st.experimental_rerun()
    elif senha_digitada:
        st.warning("Senha incorreta. Acesso negado.")
    st.stop()

# ----- SIDEBAR MENU FIXO -----
st.sidebar.markdown("## 🗂️ Menu")
menu = st.sidebar.radio("Escolha a função", [
    "📊 Resumo Geral",
    "🚨 Clientes com 3 Boletos Vencidos",
    "🧾 Cancelar Assinatura (simulado)",
    "💣 Deletar Boletos (simulado)",
    "📅 Relatório de Pagamentos"
], index=0)

# ----- HEADER API -----
KOBANA_API_KEY = st.secrets["kobana"]["api_token"]
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {KOBANA_API_KEY}",
    "User-Agent": "GrupoIndexxApp/1.0"
}

# ----- FUNÇÃO BUSCAR BOLETOS -----
@st.cache_data(show_spinner="🔄 Buscando boletos na Kobana...", ttl=300)
def buscar_boletos():
    boletos = []
    pagina = 1
    while True:
        url = "https://api.kobana.com.br/v1/bank_billets"
        params = {"per_page": 100, "page": pagina, "sort": "-created_at"}
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            st.error(f"❌ Erro {resp.status_code} ao acessar a API da Kobana.")
            st.stop()
        dados = resp.json()
        if not isinstance(dados, dict) or "bank_billets" not in dados:
            break
        boletos_lidos = dados["bank_billets"]
        if not boletos_lidos:
            break
        boletos.extend(boletos_lidos)
        if len(boletos_lidos) < 100:
            break
        pagina += 1
    return boletos

# ----- DADOS -----
boletos_raw = buscar_boletos()
boletos = pd.DataFrame([{
    "Nome": b.get("customer_person_name") or "",
    "CPF/CNPJ": b.get("customer_cnpj_cpf") or "",
    "Status": b.get("status") or "",
    "Valor": float(b.get("amount", 0)) / 100 if b.get("amount") else 0,
    "Data de Vencimento": b.get("expire_at") or "",
    "Data de Pagamento": b.get("paid_at") or ""
} for b in boletos_raw])

# --------- PAINEL PRINCIPAL ---------

st.markdown("## 🔐 Painel Interno – Gestão Grupo Indexx")

# -- RESUMO GERAL
if menu == "📊 Resumo Geral":
    total = len(boletos)
    pagos = boletos[boletos["Status"] == "paid"]
    vencidos = boletos[boletos["Status"] == "expired"]
    abertos = boletos[boletos["Status"] == "opened"]
    st.subheader("📊 Resumo Financeiro")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total de Boletos", total)
    col2.metric("Boletos Pagos", len(pagos))
    col3.metric("Boletos Vencidos", len(vencidos))
    col4.metric("Boletos em Aberto", len(abertos))
    col5.metric("Valor Total Pago", f"R$ {pagos['Valor'].sum():,.2f}".replace(".", ","))

# -- CLIENTES COM 3 BOLETOS VENCIDOS
elif menu == "🚨 Clientes com 3 Boletos Vencidos":
    vencidos = boletos[boletos["Status"] == "expired"]
    contagem = vencidos["CPF/CNPJ"].value_counts()
    cpf_cnpj_com_3 = contagem[contagem == 3].index
    resultado = vencidos[vencidos["CPF/CNPJ"].isin(cpf_cnpj_com_3)]
    st.subheader("🚨 Clientes com 3 Boletos Vencidos")
    st.dataframe(resultado[["Nome", "CPF/CNPJ", "Data de Vencimento"]].drop_duplicates())
    st.download_button("📥 Baixar Excel", resultado.to_csv(index=False), "clientes_3_vencidos.csv")

# -- CANCELAMENTO (Simulado)
elif menu == "🧾 Cancelar Assinatura (simulado)":
    st.subheader("🧾 Cancelar Assinatura")
    doc = st.text_input("Digite o CPF ou CNPJ do cliente")
    if st.button("Cancelar"):
        st.success(f"Assinatura cancelada para {doc} (simulado)")

# -- DELETAR (Simulado)
elif menu == "💣 Deletar Boletos (simulado)":
    st.subheader("💣 Deletar Boletos")
    doc = st.text_input("Digite o CPF ou CNPJ")
    if doc:
        encontrados = boletos[boletos["CPF/CNPJ"] == doc]
        st.dataframe(encontrados)
        if st.button("Deletar todos (simulado)"):
            st.success(f"Boletos de {doc} deletados (simulado)")

# -- PAGAMENTOS
elif menu == "📅 Relatório de Pagamentos":
    pagos = boletos[boletos["Status"] == "paid"].copy()
    pagos["Data de Pagamento"] = pd.to_datetime(pagos["Data de Pagamento"], errors="coerce")
    total = pagos["Valor"].sum()
    st.subheader("📅 Relatório de Boletos Pagos")
    st.metric("Total Pago", f"R$ {total:,.2f}".replace(".", ","))
    st.dataframe(pagos)
    st.download_button("📥 Baixar CSV", pagos.to_csv(index=False), "boletos_pagos.csv")

