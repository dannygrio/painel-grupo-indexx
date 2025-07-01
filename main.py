# ✅ Painel Grupo Indexx – Versão 1.0.3 – Atualizado em 01/07/2025 por Danny
import streamlit as st
import pandas as pd
import requests

# Configuração da página
st.set_page_config(page_title="Painel Grupo Indexx", layout="centered")
st.markdown("## 🔐 Painel Interno – Gestão Grupo Indexx")

# Campo de login
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    senha_digitada = st.text_input("Digite a senha de acesso", type="password")
    if senha_digitada == st.secrets["auth"]["senha"]:
        st.session_state["logado"] = True
        st.success("✅ Acesso liberado")
    else:
        st.stop()
else:
    st.success("✅ Acesso liberado")

# Menu lateral
menu = st.sidebar.radio("🔧 Navegação", ["🔴 Clientes com 3 Boletos Vencidos", "🗑️ Deletar Assinatura"])

# Função para buscar boletos vencidos com paginação
@st.cache_data(ttl=3600)
def fetch_overdue_billets():
    base_url = st.secrets["kobana"]["base_url"]
    endpoint = st.secrets["kobana"]["endpoint"]
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {st.secrets['kobana']['api_key']}"
    }

    page = 1
    all_billets = []

    while True:
        params = {"status": "overdue", "page": page, "per_page": 50}
        r = requests.get(f"{base_url}{endpoint}", headers=headers, params=params, timeout=10)
        if r.status_code != 200:
            st.error(f"Erro ao obter boletos vencidos: {r.status_code} – {r.text}")
            return pd.DataFrame()
        
        items = r.json()
        if not items:
            break

        all_billets.extend(items)
        page += 1

    return pd.DataFrame(all_billets)

# Página de clientes com 3 boletos vencidos
if menu == "🔴 Clientes com 3 Boletos Vencidos":
    df_boletos = fetch_overdue_billets()

    if df_boletos.empty:
        st.info("Nenhum boleto vencido encontrado")
    else:
        # Agrupar por CPF/CNPJ e contar
        agrupado = df_boletos.groupby("customer_cnpj_cpf").size().reset_index(name="qtd_vencidos")
        filtrado = agrupado[agrupado["qtd_vencidos"] >= 3]
        if filtrado.empty:
            st.info("Nenhum cliente com 3 boletos vencidos")
        else:
            st.warning("⚠️ Clientes com 3 boletos vencidos encontrados:")
            st.dataframe(filtrado, use_container_width=True)

# Rodapé
st.markdown("🔒 Desenvolvido por Danny – versão 1.0.3 – 01/07/2025")
