# main.py – Painel Grupo Indexx – Versão 1.0.1 – Atualizado em 01/07/2025 por Danny

import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Painel Grupo Indexx", layout="wide")
st.markdown("<h2 style='text-align:center'>🔐 Painel Interno – Gestão Grupo Indexx</h2>", unsafe_allow_html=True)
st.markdown("")

if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    senha = st.text_input("Digite a senha para acessar o painel", type="password")
    if "auth" not in st.secrets or "senha" not in st.secrets["auth"]:
        st.error("Configure a senha em [auth] do secrets.toml")
    elif senha == st.secrets["auth"]["senha"]:
        st.session_state["logado"] = True
        st.rerun()
    elif senha:
        st.error("Senha incorreta")

@st.cache_data(show_spinner=False)
def fetch_overdue_billets():
    cfg     = st.secrets["kobana"]
    api_key = cfg["api_key"]
    base    = cfg.get("base_url", "https://api.kobana.com.br/v1")
    url     = f"{base.rstrip('/')}/bank_billets"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {api_key}"
    }
    params = {
        "status":   "overdue",
        "per_page": 100,
        "page":     1
    }

    todos = []
    try:
        while True:
            r = requests.get(url, headers=headers, params=params, timeout=10)
            st.write("🔍 Status da resposta:", r.status_code)
            st.write("📄 Resposta da API:", r.text)

            if r.status_code != 200:
                st.error(f"Erro na requisição: {r.status_code}")
                break

            json_data = r.json()
            page_data = json_data.get("items", [])
            if not page_data:
                break
            todos.extend(page_data)

            if len(page_data) < params["per_page"]:
                break
            params["page"] += 1

        if not todos:
            return pd.DataFrame()

        df = pd.json_normalize(todos)
        return df.rename(columns={
            "customer_person_name": "Cliente",
            "customer_document":    "Documento",
            "status":               "Status",
            "expire_at":            "Vencimento",
            "paid_at":              "Pago em",
            "amount":               "Valor",
            "tags":                 "Etiqueta"
        })

    except Exception as e:
        st.error(f"Erro ao processar resposta JSON da API: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner=False)
def fetch_subscriptions():
    cfg     = st.secrets["kobana"]
    api_key = cfg["api_key"]
    base    = cfg.get("base_url", "https://api.kobana.com.br/v1")
    url     = f"{base.rstrip('/')}/customer_subscriptions"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {api_key}"
    }
    r = requests.get(url, headers=headers, timeout=10)
    if r.status_code != 200:
        st.error(f"Erro ao obter assinaturas {r.status_code} {r.text}")
        return pd.DataFrame()
    items = r.json()
    df    = pd.json_normalize(items)
    return df.rename(columns={
        "id":                   "ID",
        "customer_person_name": "Cliente",
        "customer_document":    "Documento"
    })

def delete_subscription_by_id(sub_id):
    cfg     = st.secrets["kobana"]
    api_key = cfg["api_key"]
    base    = cfg.get("base_url", "https://api.kobana.com.br/v1")
    url     = f"{base.rstrip('/')}/customer_subscriptions/{sub_id}"
    headers = {
        "accept":        "application/json",
        "authorization": f"Bearer {api_key}"
    }
    r = requests.delete(url, headers=headers, timeout=10)
    if r.status_code in (200, 204):
        st.success(f"Assinatura {sub_id} excluída com sucesso")
    else:
        st.error(f"Falha ao excluir assinatura {sub_id}: {r.status_code} {r.text}")

if st.session_state["logado"]:
    st.success("✅ Acesso liberado")

    menu = st.sidebar.radio("Navegação", [
        "Clientes com 3 Boletos Vencidos",
        "Deletar Assinatura"
    ])

    if menu == "Clientes com 3 Boletos Vencidos":
        df = fetch_overdue_billets()
        if df.empty or "Documento" not in df.columns:
            st.info("Nenhum boleto vencido encontrado")
        else:
            grp  = df.groupby(["Cliente", "Documento"]).size().reset_index(name="qtd_vencidos")
            tres = grp[grp["qtd_vencidos"] >= 3]
            if tres.empty:
                st.info("Nenhum cliente com 3 ou mais boletos vencidos")
            else:
                st.dataframe(tres, use_container_width=True)

    else:
        st.subheader("Deletar assinatura por CPF ou CNPJ")
        doc = st.text_input("Informe CPF ou CNPJ")
        if st.button("Excluir"):
            subs    = fetch_subscriptions()
            achados = subs[subs["Documento"] == doc.strip()]
            if achados.empty:
                st.warning("Nenhuma assinatura encontrada para esse documento")
            elif len(achados) > 1:
                st.warning(f"Encontradas múltiplas assinaturas: {achados['ID'].tolist()}")
            else:
                sub_id = achados.iloc[0]["ID"]
                delete_subscription_by_id(sub_id)

    st.caption("🔒 Desenvolvido por Danny – versão 1.0.1 – 01/07/2025")
