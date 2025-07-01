import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta

st.set_page_config(page_title="Painel Grupo Indexx", layout="wide")
st.markdown("<h2 style='text-align:center'>🔐 Painel Interno – Gestão Grupo Indexx</h2>",
            unsafe_allow_html=True)

if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    senha = st.text_input("Digite a senha de acesso", type="password")
    if "auth" not in st.secrets or "senha" not in st.secrets["auth"]:
        st.error("Configure a senha em [auth] do secrets.toml")
    elif senha == st.secrets["auth"]["senha"]:
        st.session_state["logado"] = True
        st.rerun()
    elif senha:
        st.error("Senha incorreta")

@st.cache_data(show_spinner=False)
def fetch_boletos(status_list, date_field=None, date_value=None):
    cfg        = st.secrets["kobana"]
    api_key    = cfg.get("api_key")
    base_url   = cfg.get("base_url", "https://api.kobana.com.br/v1")
    endpoint   = cfg.get("endpoint", "/bank_billets")
    if not api_key:
        st.error("Falta api_key em [kobana] no secrets.toml")
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
        msg = resp.json().get("error", resp.text)
        st.error(f"Erro ao obter boletos {msg}")
        return pd.DataFrame()

    items = resp.json().get("items", [])
    df    = pd.json_normalize(items)
    df    = df.rename(columns={
        "customer_person_name": "Cliente",
        "customer_document":    "Documento",
        "status":               "Status",
        "expire_at":            "Vencimento",
        "paid_at":              "Pago em",
        "amount":               "Valor",
        "tags":                 "Etiqueta"
    })
    return df

def delete_subscription(cpf_cnpj):
    cfg        = st.secrets["kobana"]
    api_key    = cfg.get("api_key")
    base_url   = cfg.get("base_url", "https://api.kobana.com.br/v1")
    sub_ep     = cfg.get("sub_endpoint", "/subscriptions")
    if not api_key:
        st.error("Falta api_key em [kobana] no secrets.toml")
        return

    url     = base_url.rstrip("/") + sub_ep.strip("/") + f"/{cpf_cnpj}"
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = requests.delete(url, headers=headers, timeout=10)
    if resp.status_code in (200, 204):
        st.success(f"Assinatura de {cpf_cnpj} deletada com sucesso")
    else:
        msg = resp.json().get("error", resp.text)
        st.error(f"Falha ao deletar assinatura {cpf_cnpj}: {msg}")

if st.session_state["logado"]:
    st.success("✅ Acesso liberado")
    menu = st.sidebar.radio("Navegação", [
        "Clientes com 3 boletos vencidos",
        "Deletar assinatura"
    ])

    hoje  = date.today()
    ontem = (hoje - timedelta(days=1)).isoformat()

    if menu == "Clientes com 3 boletos vencidos":
        df_ao = fetch_boletos(["overdue"])
        if df_ao.empty or "Cliente" not in df_ao.columns:
            st.info("Nenhum boleto vencido encontrado")
        else:
            grp = (
                df_ao
                .groupby(["Cliente", "Documento"])
                .size()
                .reset_index(name="QtdeVencidos")
            )
            tres = grp[grp["QtdeVencidos"] >= 3]
            if tres.empty:
                st.info("Não há clientes com 3 ou mais boletos vencidos")
            else:
                st.dataframe(tres, use_container_width=True)

    else:  # deletar assinatura
        st.subheader("Deletar assinatura por CPF ou CNPJ")
        doc = st.text_input("Informe CPF ou CNPJ")
        if st.button("Deletar assinatura"):
            if doc.strip():
                delete_subscription(doc.strip())
            else:
                st.warning("Informe um CPF ou CNPJ válido")

    st.caption("🔒 Desenvolvido por Danny – Versão 1.0.0 – 03/07/2025")
