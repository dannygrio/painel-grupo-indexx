# main.py

import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta

st.set_page_config(page_title="Painel Grupo Indexx", layout="wide")
st.markdown("<h2 style='text-align:center'>🔐 Painel Interno – Gestão Grupo Indexx</h2>", unsafe_allow_html=True)
st.markdown("")

if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    senha = st.text_input("Digite a senha de acesso", type="password")
    if "auth" not in st.secrets or "senha" not in st.secrets["auth"]:
        st.error("Configure a senha em [auth] no secrets.toml")
    elif senha == st.secrets["auth"]["senha"]:
        st.session_state["logado"] = True
        st.rerun()
    elif senha:
        st.error("Senha incorreta")

@st.cache_data(show_spinner=False)
def fetch_boletos(status_list, date_field=None, date_value=None):
    cfg      = st.secrets.get("kobana", {})
    api_key  = cfg.get("api_key")
    base_url = cfg.get("base_url", "https://api.kobana.com.br/v1")
    endpoint = cfg.get("endpoint", "/bank_billets")

    if not api_key:
        st.error("Configure api_key em [kobana] no secrets.toml")
        return pd.DataFrame()

    url     = base_url.rstrip("/") + endpoint
    headers = {"Authorization": f"Bearer {api_key}"}
    params  = {"status": ",".join(status_list)}
    if date_field and date_value:
        params[date_field] = date_value

    resp = requests.get(url, headers=headers, params=params, timeout=10)
    if resp.status_code == 404:
        st.error(f"Endpoint não encontrado em {url}")
        return pd.DataFrame()
    if resp.status_code != 200:
        try:
            msg = resp.json().get("error", resp.text)
        except:
            msg = resp.text
        st.error(f"Erro ao obter boletos {msg}")
        return pd.DataFrame()

    items = resp.json().get("items", [])
    df    = pd.json_normalize(items)
    df    = df.rename(columns={
        "customer_person_name": "Cliente",
        "status":              "Status",
        "expire_at":           "Vencimento",
        "paid_at":             "Pago em",
        "amount":              "Valor",
        "tags":                "Etiqueta"
    })
    return df

if st.session_state["logado"]:
    st.success("✅ Acesso liberado")
    menu = st.sidebar.radio("Navegação", ["Visao Geral", "Boletos", "Indicadores", "Configuracoes"])

    hoje  = date.today()
    ontem = (hoje - timedelta(days=1)).isoformat()

    df_ao = fetch_boletos(["opened", "overdue"])
    df_pg = fetch_boletos(["paid"], date_field="paid_at", date_value=ontem)

    if menu == "Visao Geral":
        st.subheader("Visao Geral")
        if "Status" in df_ao.columns:
            total_opened  = int((df_ao["Status"] == "opened").sum())
            total_overdue = int((df_ao["Status"] == "overdue").sum())
        else:
            total_opened = total_overdue = 0
        pagos_ontem = len(df_pg)

        c1, c2, c3 = st.columns(3)
        c1.metric("Boletos Abertos", total_opened)
        c2.metric("Boletos Vencidos", total_overdue)
        c3.metric("Pagos Ontem", pagos_ontem)

    elif menu == "Boletos":
        st.subheader("Boletos Ativos opened e overdue")
        if df_ao.empty:
            st.info("Nenhum boleto aberto ou vencido encontrado")
        else:
            st.dataframe(df_ao[["Cliente","Status","Vencimento","Valor","Etiqueta"]], use_container_width=True)

    elif menu == "Indicadores":
        st.subheader("Indicadores Avancados")
        inad  = int((df_ao["Status"] == "overdue").sum()) if "Status" in df_ao.columns else 0
        multi = int(df_ao.duplicated(subset=["Cliente"], keep=False).sum()) if "Cliente" in df_ao.columns else 0
        fat   = 0
        if "Valor" in df_ao.columns:
            fat = df_ao["Valor"].replace(r"[R\$\s\.]", "", regex=True).astype(float).sum()
        col1, col2, col3 = st.columns(3)
        col1.metric("Inadimplentes Criticos", inad)
        col2.metric("Clientes com >1 Boleto", multi)
        col3.metric("Faturamento Aberto R$", f"{fat:,.2f}")

    else:
        st.subheader("Configuracoes e Ajuda")
        st.code("""
[auth]
senha      = "admin1234"

[kobana]
api_key    = "SEU_TOKEN_AQUI"
base_url   = "https://api.kobana.com.br/v1"
endpoint   = "/bank_billets"
        """, language="toml")

    st.markdown("")
    st.caption("🔒 Painel restrito – Desenvolvido por Danny – Versao 1.0.0 – 02/07/2025")
