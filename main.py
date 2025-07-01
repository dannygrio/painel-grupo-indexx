# Painel Interno – Gestão Grupo Indexx – Versão 1.0.3 – Atualizado em 01/07/2025 por Danny

import streamlit as st
import pandas as pd
import requests
from collections import Counter

st.set_page_config(page_title="Painel Grupo Indexx", layout="centered")
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

st.success("✅ Acesso liberado")

# Função para buscar todos os boletos vencidos (paginado)
@st.cache_data(show_spinner=False)
def fetch_overdue_billets():
    url = "https://api.kobana.com.br/v1/bank_billets"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {st.secrets['auth']['token']}"
    }

    boletos = []
    page = 1

    while True:
        params = {"status": "overdue", "per_page": 50, "page": page}
        r = requests.get(url, headers=headers, params=params, timeout=10)

        if r.status_code != 200:
            st.error(f"Erro ao obter boletos (página {page}): {r.status_code}")
            break

        data = r.json()
        if not isinstance(data, dict):
            st.error("Erro inesperado no retorno da API.")
            break

        items = data.get("items", [])
        if not items:
            break

        boletos.extend(items)
        page += 1

    if not boletos:
        return pd.DataFrame()

    df = pd.json_normalize(boletos)
    return df.rename(columns={
        "customer_person_name": "Cliente",
        "customer_document": "Documento",
        "status": "Status",
        "expire_at": "Vencimento",
        "paid_at": "Pago em",
        "amount": "Valor",
        "tags": "Etiqueta"
    })

# Função para processar e agrupar
def filtrar_clientes_3_vencidos(df):
    contagem = Counter(df["Documento"])
    documentos_criticos = [doc for doc, count in contagem.items() if count >= 3]
    return df[df["Documento"].isin(documentos_criticos)]

# Menu lateral
aba = st.sidebar.radio("Navegação", ["📍 Clientes com 3 Boletos Vencidos", "🗑️ Deletar Assinatura"])

# Conteúdo principal
if aba == "📍 Clientes com 3 Boletos Vencidos":
    df_boletos = fetch_overdue_billets()

    if df_boletos.empty:
        st.info("Nenhum boleto vencido encontrado")
    else:
        df_filtrado = filtrar_clientes_3_vencidos(df_boletos)

        if df_filtrado.empty:
            st.success("Nenhum cliente com 3 boletos vencidos encontrado")
        else:
            st.subheader("🔴 Clientes com 3 ou mais boletos vencidos")
            st.dataframe(df_filtrado)

elif aba == "🗑️ Deletar Assinatura":
    st.info("🔧 Em construção")

# Rodapé
st.markdown("🔒 Desenvolvido por Danny – versão 1.0.3 – 01/07/2025")
