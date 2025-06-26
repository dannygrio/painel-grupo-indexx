# Painel Executivo Grupo Indexx – Boletos Kobana – Versão 1.0 (26/06/2025)

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# Configurações
st.set_page_config(page_title="Painel Executivo – Grupo Indexx", layout="wide")
st.title("📊 Painel Executivo – Boletos Kobana")

# Login
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if not st.session_state["logado"]:
    senha = st.text_input("Digite a senha de acesso", type="password")
    if senha == st.secrets["auth"]["senha"]:
        st.session_state["logado"] = True
        st.rerun()
    else:
        st.stop()

# Token via secrets
KOBANA_API_KEY = st.secrets["kobana"]["api_token"]
headers = {
    "Authorization": f"Bearer {KOBANA_API_KEY}",
    "Content-Type": "application/json"
}

# Buscar boletos com paginação
@st.cache_data(ttl=600)
def buscar_boletos():
    boletos = []
    page = 1
    while True:
        r = requests.get(
            "https://api.kobana.com.br/v1/bank_billets",
            headers=headers,
            params={"per_page": 100, "page": page, "sort": "-created_at"},
            timeout=10
        )
        if r.status_code != 200:
            raise Exception(f"Erro {r.status_code}: {r.text}")
        data = r.json()
        pagina = data if isinstance(data, list) else data.get("bank_billets", [])
        if not pagina:
            break
        boletos.extend(pagina)
        if len(pagina) < 100:
            break
        page += 1
    return boletos

# Carrega boletos
try:
    dados = buscar_boletos()
except Exception as e:
    st.error(f"Erro ao buscar dados: {e}")
    st.stop()

# Transforma em DataFrame
df = pd.DataFrame([{
    "Nome": b.get("customer_person_name", ""),
    "CPF/CNPJ": b.get("customer_cnpj_cpf", ""),
    "Status API": b.get("status", ""),
    "Valor": float(b.get("amount", 0)) / 100,
    "Vencimento": b.get("expire_at"),
    "Pago em": b.get("paid_at")
} for b in dados])

# Converte datas
df["Vencimento"] = pd.to_datetime(df["Vencimento"], errors="coerce")
df["Pago em"] = pd.to_datetime(df["Pago em"], errors="coerce")

# Tradução de status para exibição
df["Status"] = df["Status API"].map({
    "opened": "Em aberto",
    "paid": "Pago",
    "overdue": "Vencido",
    "canceled": "Cancelado"
}).fillna(df["Status API"])

# Filtros de análise
hoje = datetime.now().date()
ontem = hoje - timedelta(days=1)
inicio_mes = hoje.replace(day=1)

pagos = df[df["Status API"] == "paid"]
vencidos = df[df["Status API"] == "overdue"]
abertos = df[df["Status API"] == "opened"]
pagos_ontem = pagos[pagos["Pago em"].dt.date == ontem]
pagos_mes = pagos[pagos["Pago em"].dt.date >= inicio_mes]

# Contagem de clientes com 3 boletos vencidos
vencidos_c3 = vencidos["CPF/CNPJ"].value_counts()
clientes_c3 = vencidos[vencidos["CPF/CNPJ"].isin(vencidos_c3[vencidos_c3 == 3].index)]
clientes_c3 = clientes_c3[["Nome", "CPF/CNPJ"]].drop_duplicates()

# Dashboard
col1, col2, col3 = st.columns(3)
col1.metric("📄 Total de Boletos", len(df))
col2.metric("💰 Boletos Pagos", len(pagos))
col3.metric("📬 Em Aberto", len(abertos))

col4, col5, col6 = st.columns(3)
col4.metric("⚠️ Vencidos", len(vencidos))
col5.metric("📆 Pagos Ontem", len(pagos_ontem))
col6.metric("📅 Valor Pago no Mês", f"R$ {pagos_mes['Valor'].sum():,.2f}".replace(".", ","))

st.markdown("---")
st.subheader("🚨 Clientes com 3 Boletos Vencidos")
st.dataframe(clientes_c3)
st.download_button("📥 Baixar lista (CSV)", clientes_c3.to_csv(index=False), file_name="clientes_3_vencidos.csv")

st.markdown("---")
st.subheader("📋 Todos os Boletos (com status traduzido)")
st.dataframe(df.drop(columns=["Status API"]))
st.download_button("📥 Baixar todos os boletos (CSV)", df.to_csv(index=False), file_name="boletos_completos.csv")
