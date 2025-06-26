# Painel Executivo – Kobana – Versão 26/06/2025 por Danny

import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Painel Executivo – Boletos Ativos (Kobana)", layout="wide")
st.markdown("## 📊 Painel Executivo – Boletos Ativos (Kobana)")

# Login
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    senha = st.text_input("Digite a senha para acessar o painel", type="password")
    if senha == st.secrets["auth"]["senha"]:
        st.session_state["logado"] = True
    else:
        st.stop()

# Token
TOKEN = st.secrets["kobana"]["api_token"]
HEADERS = {"Authorization": f"Token token={TOKEN}"}

# Coleta todos os boletos com paginação
def get_boletos():
    all_boletos = []
    page = 1
    while True:
        url = f"https://api.kobana.com.br/v1/bank_billets?page={page}&per_page=100"
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200:
            st.error("Erro ao buscar boletos.")
            break
        data = resp.json()
        if not data:
            break
        all_boletos.extend(data)
        page += 1
    return all_boletos

boletos = get_boletos()

# Filtra boletos ativos (opened e overdue)
ativos = [b for b in boletos if b["status"] in ["opened", "overdue"]]
df_ativos = pd.DataFrame([{
    "Nome": b["customer_person_name"],
    "CPF/CNPJ": b["customer_person_document"],
    "Status": b["status"],
    "Valor (R$)": float(b["amount"]) / 100,
    "Vencimento": b["expire_at"],
    "Tag": ", ".join(b.get("tags", []))
} for b in ativos])

# Clientes com 3 ou mais boletos vencidos ativos
vencidos = [b for b in ativos if b["status"] == "overdue"]
df_vencidos = pd.DataFrame(vencidos)
inadimplentes = (
    df_vencidos.groupby(["customer_person_name", "customer_person_document"])
    .size()
    .reset_index(name="Qtd Vencidos")
)
clientes_inadimplentes = inadimplentes[inadimplentes["Qtd Vencidos"] >= 3]

# Painel de indicadores
col1, col2, col3 = st.columns(3)
col1.metric("👥 Boletos em Aberto", len([b for b in ativos if b["status"] == "opened"]))
col2.metric("⚠️ Boletos Vencidos", len([b for b in ativos if b["status"] == "overdue"]))
if len(ativos) > 0:
    perc = (len([b for b in ativos if b["status"] == "overdue"]) / len(ativos)) * 100
else:
    perc = 0.0
col3.metric("📊 Inadimplência Ativa", f"{perc:.2f}%")

# Lista de clientes com 3 boletos vencidos
st.markdown("### 🚨 Clientes com 3 Boletos Vencidos")
if not clientes_inadimplentes.empty:
    clientes_inadimplentes.columns = ["Nome", "CPF/CNPJ", "Qtd Vencidos"]
    st.dataframe(clientes_inadimplentes)
    st.download_button("📥 Baixar lista CSV", data=clientes_inadimplentes.to_csv(index=False), file_name="clientes_inadimplentes.csv", mime="text/csv")
else:
    st.warning("Nenhum cliente com 3 boletos vencidos.")

# Lista geral de boletos ativos
st.markdown("### 📋 Boletos Ativos (Opened + Overdue)")
st.dataframe(df_ativos)
st.download_button("📥 Exportar todos os boletos (CSV)", data=df_ativos.to_csv(index=False), file_name="boletos_ativos.csv", mime="text/csv")
