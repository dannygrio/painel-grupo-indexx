import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Painel Executivo – Grupo Indexx", layout="wide")
st.title("📊 Painel Executivo – Boletos Ativos (Kobana)")

# Login
senha_correta = st.secrets["auth"]["senha"]
senha = st.text_input("Digite a senha para acessar o painel", type="password")
if senha != senha_correta:
    if senha:
        st.error("Senha incorreta.")
    st.stop()

# Buscar boletos ativos
@st.cache_data(show_spinner="🔄 Buscando boletos ativos...")
def buscar_boletos():
    token = st.secrets["kobana"]["api_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    all_boletos = []
    page = 1
    while True:
        url = "https://api.kobana.com.br/v1/bank_billets"
        params = {"page": page, "per_page": 100}
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            st.error(f"Erro {resp.status_code} ao buscar boletos")
            break
        data = resp.json()
        if not isinstance(data, list) or not data:
            break
        all_boletos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return all_boletos

boletos_raw = buscar_boletos()

# Criar DataFrame com boletos ativos
boletos = pd.DataFrame([{
    "Nome": b.get("customer_person_name", ""),
    "CPF/CNPJ": b.get("customer_cnpj_cpf", ""),
    "Status": b.get("status", ""),
    "Valor (R$)": float(b.get("amount", 0)) / 100,
    "Vencimento": b.get("due_date", ""),
    "Tag": ", ".join(b.get("tags", [])) if isinstance(b.get("tags", []), list) else b.get("tags", "")
} for b in boletos_raw if b.get("status") in ["opened", "overdue"]])

# Converter datas
boletos["Vencimento"] = pd.to_datetime(boletos["Vencimento"], errors="coerce")

# Separar status
boletos_opened = boletos[boletos["Status"] == "opened"]
boletos_overdue = boletos[boletos["Status"] == "overdue"]
total_ativos = len(boletos)
percent_inadimplencia = (len(boletos_overdue) / total_ativos * 100) if total_ativos > 0 else 0

# Clientes com 3 boletos vencidos
contagem_vencidos = boletos_overdue["CPF/CNPJ"].value_counts()
cpf_criticos = contagem_vencidos[contagem_vencidos >= 3].index.tolist()
clientes_criticos = boletos_overdue[boletos_overdue["CPF/CNPJ"].isin(cpf_criticos)]
clientes_criticos = clientes_criticos[["Nome", "CPF/CNPJ"]].drop_duplicates()

# Indicadores
col1, col2, col3 = st.columns(3)
col1.metric("📬 Boletos em Aberto", len(boletos_opened))
col2.metric("⚠️ Boletos Vencidos", len(boletos_overdue))
col3.metric("📊 Inadimplência Ativa", f"{percent_inadimplencia:.2f}%")

st.markdown("---")
st.subheader("🚨 Clientes com 3 Boletos Vencidos")
st.dataframe(clientes_criticos, use_container_width=True)
st.download_button("📥 Baixar lista CSV", data=clientes_criticos.to_csv(index=False), file_name="clientes_com_3_vencidos.csv")

st.markdown("---")
st.subheader("📋 Boletos Ativos (Opened + Overdue)")
st.dataframe(boletos, use_container_width=True)
st.download_button("📥 Exportar todos os boletos (CSV)", data=boletos.to_csv(index=False), file_name="boletos_ativos.csv")
