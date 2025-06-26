# Painel Kobana – Grupo Indexx – Versão 26/06/2025 por Danny

import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Painel Grupo Indexx", layout="wide")
st.title("💳 Painel Interno – Boletos Kobana")

# Login por senha (armazenada em secrets)
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    senha = st.text_input("Digite a senha de acesso", type="password")
    if senha == st.secrets["auth"]["senha"]:
        st.session_state["logado"] = True
    else:
        st.stop()

# Cabeçalhos e token da API Kobana
KOBANA_API_KEY = st.secrets["kobana"]["api_token"]
headers = {
    "Authorization": f"Token token={KOBANA_API_KEY}",
    "Content-Type": "application/json"
}

# Função para buscar boletos paginados
@st.cache_data(show_spinner="🔄 Carregando boletos da Kobana...")
def buscar_boletos():
    boletos = []
    pagina = 1

    while True:
        url = "https://api.kobana.com.br/v1/bank_billets"
        params = {"per_page": 100, "page": pagina, "sort": "-created_at"}
        r = requests.get(url, headers=headers, params=params)

        if r.status_code != 200:
            raise Exception(f"Erro {r.status_code}: {r.text}")

        json_data = r.json()
        dados_pagina = json_data if isinstance(json_data, list) else json_data.get("bank_billets", [])

        if not dados_pagina:
            break

        boletos.extend(dados_pagina)
        if len(dados_pagina) < 100:
            break

        pagina += 1

    return boletos

# Carregar dados
try:
    dados_api = buscar_boletos()
    if not dados_api:
        st.warning("Nenhum boleto retornado da API. Verifique o token ou conexão.")
        st.stop()
except Exception as e:
    st.error(f"❌ Erro ao buscar boletos: {e}")
    st.stop()

# Transformar em DataFrame
boletos = pd.DataFrame([{
    "Nome": b.get("customer_person_name", ""),
    "CPF/CNPJ": b.get("customer_cnpj_cpf", ""),
    "Status": b.get("status", ""),
    "Valor": float(b.get("amount", 0)) / 100,
    "Data de Vencimento": b.get("expire_at", ""),
    "Data de Pagamento": b.get("paid_at", "")
} for b in dados_api])

# Menu lateral
menu = st.sidebar.radio("📋 Menu", [
    "📊 Resumo Geral",
    "🚨 Clientes com 3 Boletos Vencidos",
    "🧾 Cancelar Assinatura (simulado)",
    "💣 Deletar Boletos (simulado)",
    "📅 Relatório de Pagamentos"
])

# Funções
if menu == "📊 Resumo Geral":
    total = len(boletos)
    pagos = boletos[boletos["Status"].str.lower() == "paid"]
    vencidos = boletos[boletos["Status"].str.lower() == "expired"]
    abertos = total - len(pagos) - len(vencidos)
    st.subheader("📊 Resumo Financeiro")
    st.metric("Total de Boletos", total)
    st.metric("Boletos Vencidos", len(vencidos))
    st.metric("Boletos Pagos", len(pagos))
    st.metric("Valor Total Pago", f"R$ {pagos['Valor'].sum():,.2f}".replace(".", ","))
    st.metric("Boletos em Aberto", abertos)

elif menu == "🚨 Clientes com 3 Boletos Vencidos":
    vencidos = boletos[boletos["Status"].str.lower() == "expired"]
    contagem = vencidos["CPF/CNPJ"].value_counts()
    cpf_cnpj_com_3 = contagem[contagem == 3].index
    resultado = vencidos[vencidos["CPF/CNPJ"].isin(cpf_cnpj_com_3)]
    st.subheader("🚨 Clientes com 3 Boletos Vencidos")
    st.dataframe(resultado[["Nome", "CPF/CNPJ"]].drop_duplicates())
    st.download_button("📥 Baixar Excel", resultado.to_csv(index=False), "clientes_3_vencidos.csv")

elif menu == "🧾 Cancelar Assinatura (simulado)":
    st.subheader("🧾 Cancelar Assinatura")
    doc = st.text_input("Digite o CPF ou CNPJ do cliente")
    if st.button("Cancelar"):
        st.success(f"Assinatura cancelada para {doc} (simulado)")

elif menu == "💣 Deletar Boletos (simulado)":
    st.subheader("💣 Deletar Boletos")
    doc = st.text_input("Digite o CPF ou CNPJ")
    if doc:
        encontrados = boletos[boletos["CPF/CNPJ"] == doc]
        st.dataframe(encontrados)
        if st.button("Deletar todos (simulado)"):
            st.success(f"Boletos de {doc} deletados (simulado)")

elif menu == "📅 Relatório de Pagamentos":
    pagos = boletos[boletos["Status"].str.lower() == "paid"].copy()
    pagos["Data de Pagamento"] = pd.to_datetime(pagos["Data de Pagamento"])
    total = pagos["Valor"].sum()
    st.metric("Total Pago", f"R$ {total:,.2f}".replace(".", ","))
    st.dataframe(pagos)
    st.download_button("📥 Baixar CSV", pagos.to_csv(index=False), "boletos_pagos.csv")
