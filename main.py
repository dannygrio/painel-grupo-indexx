# Painel Executivo – Boletos Ativos (Kobana) – Versão 26/06/2025 por Danny

import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Painel Executivo – Grupo Indexx", layout="wide")

# Título
st.markdown("## 📊 Painel Executivo – Boletos Ativos (Kobana)")

# Login
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    senha_digitada = st.text_input("Digite a senha para acessar o painel", type="password")
    if senha_digitada == st.secrets["auth"]["senha"]:
        st.session_state["logado"] = True
    else:
        st.stop()

# Função para buscar todos os boletos com paginação
def buscar_boletos(token):
    boletos = []
    page = 1
    while True:
        url = f"https://api.kobana.com.br/v1/bank_billets?status[]=opened&status[]=overdue&page={page}"
        headers = {"Authorization": f"Token token={token}"}
        resposta = requests.get(url, headers=headers)
        if resposta.status_code != 200:
            st.error("Erro ao buscar boletos.")
            return []
        dados = resposta.json()
        boletos.extend(dados)
        if len(dados) < 50:
            break
        page += 1
    return boletos

# Coleta dos boletos
token = st.secrets["kobana"]["api_token"]
dados_boletos = buscar_boletos(token)
df = pd.DataFrame(dados_boletos)

if df.empty:
    st.warning("Nenhum boleto retornado pela API.")
    st.stop()

# Conversão e tratamento
df["due_date"] = pd.to_datetime(df["due_date"])
df["amount"] = df["amount"].astype(float) / 100
df.rename(columns={
    "customer_person_name": "Nome",
    "customer_person_document": "CPF/CNPJ",
    "status": "Status",
    "amount": "Valor (R$)",
    "due_date": "Vencimento",
    "tags": "Tag"
}, inplace=True)

# Cálculos principais
total_boletos = len(df)
boletos_abertos = df[df["Status"] == "opened"]
boletos_vencidos = df[df["Status"] == "overdue"]

inadimplencia_ativa = len(boletos_vencidos) / total_boletos if total_boletos else 0

# Exibição de métricas
col1, col2, col3 = st.columns(3)
col1.metric("👥 Boletos em Aberto", len(boletos_abertos))
col2.metric("⚠️ Boletos Vencidos", len(boletos_vencidos))
col3.metric("📊 Inadimplência Ativa", f"{inadimplencia_ativa:.2%}")

# Clientes com 3 boletos vencidos
st.markdown("### 🚨 Clientes com 3 Boletos Vencidos")

if not boletos_vencidos.empty:
    grupo = boletos_vencidos.groupby(["Nome", "CPF/CNPJ"]).size().reset_index(name="Qtde Vencidos")
    clientes_inadimplentes = grupo[grupo["Qtde Vencidos"] >= 3]

    if not clientes_inadimplentes.empty:
        st.dataframe(clientes_inadimplentes[["Nome", "CPF/CNPJ"]], use_container_width=True)
        st.download_button(
            "📥 Baixar lista CSV",
            clientes_inadimplentes.to_csv(index=False).encode("utf-8"),
            "clientes_inadimplentes.csv",
            "text/csv"
        )
    else:
        st.write("Nenhum cliente com 3 boletos vencidos no momento.")
else:
    st.write("Nenhum boleto vencido disponível no momento.")

# Tabela completa de boletos ativos
st.markdown("### 📋 Boletos Ativos (Opened + Overdue)")
st.dataframe(df[["Nome", "CPF/CNPJ", "Status", "Valor (R$)", "Vencimento", "Tag"]], use_container_width=True)
st.download_button(
    "📥 Exportar todos os boletos (CSV)",
    df.to_csv(index=False).encode("utf-8"),
    "boletos_ativos.csv",
    "text/csv"
)
