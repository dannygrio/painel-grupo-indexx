import streamlit as st
import pandas as pd
import requests
from collections import Counter

# Configuração da página
st.set_page_config(page_title="Painel Interno – Grupo Indexx", layout="centered")
st.markdown("## 🔐 Painel Interno – Gestão Grupo Indexx")

# Autenticação
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    senha = st.text_input("Digite a senha de acesso", type="password")
    if senha == st.secrets["auth"]["senha"]:
        st.session_state["logado"] = True
        st.success("✅ Acesso liberado")
    else:
        st.stop()
else:
    st.success("✅ Acesso liberado")

# Função para buscar boletos vencidos
@st.cache_data(show_spinner="🔄 Buscando boletos vencidos...")
def fetch_overdue_billets():
    base_url = st.secrets["kobana"]["base_url"]
    endpoint = st.secrets["kobana"]["endpoint"]
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {st.secrets['kobana']['api_key']}"
    }

    all_billets = []
    page = 1

    while True:
        params = {"status": "overdue", "page": page, "per_page": 50}
        r = requests.get(f"{base_url}{endpoint}", headers=headers, params=params, timeout=10)
        if r.status_code != 200:
            st.error(f"Erro ao obter boletos vencidos: {r.status_code} – {r.text}")
            return pd.DataFrame()

        data = r.json()
        items = data.get("items", [])
        if not items:
            break

        all_billets.extend(items)
        page += 1

    df = pd.DataFrame(all_billets)
    return df

# Menu lateral fixo
st.sidebar.markdown("## Navegação")
aba = st.sidebar.radio("", ["🔴 Clientes com 3 Boletos Vencidos", "🗑️ Deletar Assinatura"])

if aba == "🔴 Clientes com 3 Boletos Vencidos":
    df_boletos = fetch_overdue_billets()

    if df_boletos.empty:
        st.info("Nenhum boleto vencido encontrado")
    else:
        # Contagem por CPF/CNPJ
        contagem = Counter(df_boletos["customer_cnpj_cpf"])
        mais_de_tres = [doc for doc, qtd in contagem.items() if qtd >= 3]

        if not mais_de_tres:
            st.info("Nenhum cliente com 3 boletos vencidos")
        else:
            df_filtrado = df_boletos[df_boletos["customer_cnpj_cpf"].isin(mais_de_tres)]
            df_final = df_filtrado[[
                "customer_person_name", "customer_cnpj_cpf", "expire_at", "amount", "url"
            ]].sort_values(by=["customer_cnpj_cpf", "expire_at"])
            st.dataframe(df_final, use_container_width=True)

elif aba == "🗑️ Deletar Assinatura":
    st.warning("⚠️ Função de exclusão ainda não implementada")

# Rodapé
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("🔒 Desenvolvido por Danny – versão 1.0.3 – 01/07/2025")
