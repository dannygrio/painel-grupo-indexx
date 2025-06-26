import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Painel Executivo – Grupo Indexx", layout="wide")
st.title("📊 Painel Executivo – Boletos Kobana")

# Login
senha_correta = st.secrets["auth"]["senha"]
senha = st.text_input("Digite a senha para acessar o painel", type="password")
if senha != senha_correta:
    st.stop()

# Buscar boletos
@st.cache_data(show_spinner="🔄 Carregando boletos da API...")
def buscar_boletos():
    token = st.secrets["kobana"]["api_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    all_boletos = []
    page = 1
    while True:
        url = f"https://api.kobana.com.br/v1/bank_billets"
        params = {
            "page": page,
            "per_page": 100
        }
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            st.error(f"Erro {resp.status_code} ao buscar página {page}")
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

# Transformar em DataFrame
boletos = pd.DataFrame([{
    "Nome": b.get("customer_person_name", ""),
    "CPF/CNPJ": b.get("customer_cnpj_cpf", ""),
    "Status": b.get("status", ""),
    "Valor": float(b.get("amount", 0)) / 100,
    "Vencimento": b.get("due_date", ""),
    "Pagamento": b.get("paid_at", "")
} for b in boletos_raw])

# Converter datas
boletos["Vencimento"] = pd.to_datetime(boletos["Vencimento"], errors="coerce")
boletos["Pagamento"] = pd.to_datetime(boletos["Pagamento"], errors="coerce")

# Análises
total = len(boletos)
pagos = boletos[boletos["Status"] == "paid"]
vencidos = boletos[boletos["Status"] == "overdue"]
abertos = boletos[boletos["Status"] == "opened"]
ontem = datetime.now().date() - timedelta(days=1)
pagos_ontem = pagos[pagos["Pagamento"].dt.date == ontem]

# Clientes com 3 vencidos
contagem = vencidos["CPF/CNPJ"].value_counts()
cpf_3_vencidos = contagem[contagem == 3].index.tolist()
clientes_3_vencidos = vencidos[vencidos["CPF/CNPJ"].isin(cpf_3_vencidos)][["Nome", "CPF/CNPJ"]].drop_duplicates()

# Métricas
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📄 Total de Boletos", total)
    st.metric("⚠️ Vencidos", len(vencidos))
with col2:
    st.metric("💰 Boletos Pagos", len(pagos))
    st.metric("📅 Pagos Ontem", len(pagos_ontem))
with col3:
    st.metric("👥 Em Aberto", len(abertos))
    st.metric("🗓️ Valor Pago no Mês", f"R$ {pagos[pagos['Pagamento'].dt.month == datetime.now().month]['Valor'].sum():,.2f}".replace('.', ','))

st.divider()

# Clientes com 3 boletos vencidos
st.subheader("🚨 Clientes com 3 Boletos Vencidos")
st.dataframe(clientes_3_vencidos, use_container_width=True)
st.download_button("📥 Baixar lista (CSV)", data=clientes_3_vencidos.to_csv(index=False), file_name="clientes_com_3_boletos_vencidos.csv")
