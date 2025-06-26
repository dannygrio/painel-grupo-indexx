# Painel Executivo – Boletos Ativos (Kobana) – Versão 26/06/2025 por Danny

import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Painel Executivo – Grupo Indexx", layout="wide")
st.title("📊 Painel Executivo – Boletos Ativos (Kobana)")

# Login seguro via secrets
senha_digitada = st.text_input("Digite a senha para acessar o painel", type="password")
if senha_digitada != st.secrets["auth"]["senha"]:
    st.stop()

# Token da API Kobana
TOKEN = st.secrets["kobana"]["api_token"]
HEADERS = {"Authorization": f"Token token={TOKEN}"}

# Função para buscar boletos com paginação e múltiplos status
def buscar_boletos(status):
    boletos = []
    page = 1
    while True:
        url = f"https://api.kobana.com.br/v1/bank_billets?status[]={status}&page={page}&per_page=100"
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200:
            st.error(f"Erro ao buscar boletos com status {status}.")
            return []
        dados = resp.json()
        if not dados:
            break
        boletos.extend(dados)
        if len(dados) < 100:
            break
        page += 1
    return boletos

# Buscar boletos opened e overdue
boletos_opened = buscar_boletos("opened")
boletos_overdue = buscar_boletos("overdue")
boletos_ativos = boletos_opened + boletos_overdue

if not boletos_ativos:
    st.warning("Nenhum boleto ativo retornado pela API.")
    st.stop()

# Criar DataFrame dos boletos ativos
df = pd.DataFrame([{
    "Nome": b.get("customer_person_name", ""),
    "CPF/CNPJ": b.get("customer_person_document", ""),
    "Status": b.get("status", ""),
    "Valor (R$)": float(b.get("amount", 0)) / 100,
    "Vencimento": b.get("expire_at", ""),
    "Tag": ", ".join(b.get("tags", []))
} for b in boletos_ativos])

# Tabelas auxiliares
df_vencidos = df[df["Status"] == "overdue"]
df_abertos = df[df["Status"] == "opened"]

# Métricas principais
col1, col2, col3 = st.columns(3)
col1.metric("👥 Boletos em Aberto", len(df_abertos))
col2.metric("⚠️ Boletos Vencidos", len(df_vencidos))
inad_pct = (len(df_vencidos) / len(df)) * 100 if len(df) else 0
col3.metric("📊 Inadimplência Ativa", f"{inad_pct:.2f}%")

# Clientes com 3 boletos vencidos
st.markdown("### 🚨 Clientes com 3 Boletos Vencidos")
if not df_vencidos.empty:
    grupo = df_vencidos.groupby(["Nome", "CPF/CNPJ"]).size().reset_index(name="Qtd Vencidos")
    inadimplentes = grupo[grupo["Qtd Vencidos"] >= 3]

    if not inadimplentes.empty:
        st.dataframe(inadimplentes[["Nome", "CPF/CNPJ", "Qtd Vencidos"]], use_container_width=True)
        st.download_button(
            "📥 Baixar CSV",
            inadimplentes.to_csv(index=False).encode("utf-8"),
            "clientes_inadimplentes.csv",
            "text/csv"
        )
    else:
        st.write("Nenhum cliente com 3 boletos vencidos.")
else:
    st.write("Nenhum boleto vencido no momento.")

# Tabela geral
st.markdown("### 📋 Boletos Ativos (Opened + Overdue)")
st.dataframe(df, use_container_width=True)
st.download_button(
    "📥 Exportar todos os boletos (CSV)",
    df.to_csv(index=False).encode("utf-8"),
    "boletos_ativos.csv",
    "text/csv"
)
