# Simulador Kobana – Versão 1.0.0 – Atualizado em 01/07/2025 por Danny

import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta

# Configuração da página
st.set_page_config(page_title="Painel Grupo Indexx", layout="wide")
st.markdown("<h2 style='text-align: center;'>🔐 Painel Interno – Gestão Grupo Indexx</h2>", unsafe_allow_html=True)
st.markdown("")

# Sessão de login
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    senha = st.text_input("Digite a senha de acesso", type="password")
    if "auth" not in st.secrets or "senha" not in st.secrets["auth"]:
        st.error("Configuração de senha não encontrada.")
    elif senha == st.secrets["auth"]["senha"]:
        st.session_state["logado"] = True
        st.rerun()
    elif senha != "":
        st.error("Senha incorreta.")

# Função genérica para buscar boletos da Kobana
@st.cache_data(show_spinner=False)
def fetch_boletos(status_list, date_field=None, date_value=None):
    api_key = st.secrets["kobana"]["api_key"]
    base_url = st.secrets["kobana"]["base_url"]
    url = f"{base_url}/boletos"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"status": ",".join(status_list)}
    if date_field and date_value:
        params[date_field] = date_value
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    if resp.status_code != 200:
        st.error(f"Erro ao obter boletos: {resp.text}")
        return pd.DataFrame()
    data = resp.json()
    items = data.get("items", data)
    return pd.json_normalize(items)

# Conteúdo do painel após login
if st.session_state["logado"]:
    st.success("✅ Acesso liberado")
    menu = st.sidebar.radio("Navegação", ["📊 Visão Geral", "📁 Boletos", "📉 Indicadores", "⚙️ Configurações"])

    # preparar datas
    hoje = date.today()
    ontem = (hoje - timedelta(days=1)).isoformat()

    # buscar dados
    df_ao = fetch_boletos(["opened", "overdue"])
    df_pg = fetch_boletos(["paid"], date_field="paid_at", date_value=ontem)

    # renomear colunas conforme necessidade
    if not df_ao.empty:
        df_ao = df_ao.rename(columns={
            "customer_person_name": "Cliente",
            "status": "Status",
            "expire_at": "Vencimento",
            "amount": "Valor",
            "tags": "Etiqueta"
        })

    if not df_pg.empty:
        df_pg = df_pg.rename(columns={
            "customer_person_name": "Cliente",
            "status": "Status",
            "paid_at": "Pago em",
            "amount": "Valor"
        })

    if menu == "📊 Visão Geral":
        st.subheader("Visão Geral")
        total_opened = len(df_ao[df_ao["Status"] == "opened"])
        total_overdue = len(df_ao[df_ao["Status"] == "overdue"])
        pagos_ontem = len(df_pg)

        col1, col2, col3 = st.columns(3)
        col1.metric("Boletos Abertos", total_opened)
        col2.metric("Boletos Vencidos", total_overdue)
        col3.metric("Pagos Ontem", pagos_ontem)

    elif menu == "📁 Boletos":
        st.subheader("Boletos Ativos (opened e overdue)")
        if df_ao.empty:
            st.info("Nenhum boleto aberto ou vencido encontrado.")
        else:
            st.dataframe(df_ao[["Cliente", "Status", "Vencimento", "Valor", "Etiqueta"]], use_container_width=True)

    elif menu == "📉 Indicadores":
        st.subheader("Indicadores Avançados")
        inadimplentes_criticos = len(df_ao[df_ao["Status"] == "overdue"])  # exemplo
        boletos_multiplos = len(df_ao[df_ao.duplicated(subset=["Cliente"], keep=False)])
        faturamento_aberto = df_ao["Valor"].replace(r"[R$\s\.]", "", regex=True).astype(float).sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("Inadimplentes Críticos", inadimplentes_criticos)
        col2.metric("Clientes com >1 Boleto", boletos_multiplos)
        col3.metric("Faturamento Aberto (R$)", f"{faturamento_aberto:,.2f}")

    else:  # Configurações
        st.subheader("Configurações e Ajuda")
        st.write("Edite seu `.streamlit/secrets.toml` para ajustar token e senha")
        st.code("""
[auth]
senha = "SUA_SENHA_AQUI"

[kobana]
api_key = "SEU_TOKEN_KOBANA"
base_url = "https://api.kobana.com.br/v1"
        """, language="toml")

    st.markdown("")
    st.caption("🔒 Painel restrito – Desenvolvido por Danny – Versão 1.0.0 – 01/07/2025")
