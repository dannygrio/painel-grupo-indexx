import streamlit as st
import pandas as pd
import requests
from datetime import datetime

senha_correta = st.secrets["auth"]["senha"]
KOBANA_API_KEY = st.secrets["kobana"]["api_token"]

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {KOBANA_API_KEY}"
}

# Requisição para obter boletos da Kobana
url = "https://api.kobana.com.br/v1/bank_billets"
params = {
    "per_page": 100,
    "page": 1,
    "sort": "-created_at"
}

response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    dados = response.json()
    st.write("🔍 Conteúdo recebido da API:", dados)  # debug temporário

    if isinstance(dados, list):
        boletos_raw = dados
    else:
        st.error("❌ Estrutura inesperada da resposta da API.")
        st.stop()

    # Transforma em DataFrame
    boletos = pd.DataFrame([{
        "Nome": b.get("customer_person_name", ""),
        "CPF/CNPJ": b.get("customer_cnpj_cpf", ""),
        "Status": b.get("status", ""),
        "Valor": float(b.get("amount", 0)) / 100,
        "Data de Vencimento": b.get("expire_at", ""),
        "Data de Pagamento": b.get("paid_at", "")
    } for b in boletos_raw])

else:
    st.error("Erro ao acessar a API da Kobana.")
    st.stop()

# Título e login
st.title("🔐 Painel Interno – Gestão Grupo Indexx")
senha_digitada = st.text_input("Digite a senha de acesso", type="password")

if senha_digitada != senha_correta:
    st.warning("Senha incorreta. Acesso negado.")
    st.stop()

# Menu lateral
menu = st.sidebar.selectbox("Selecione a função", [
    "📊 Resumo Geral",
    "🧾 Cancelar Assinatura",
    "💣 Deletar Boletos",
    "🚨 Clientes com 3 Boletos Vencidos",
    "📅 Relatório de Pagamentos"
])

# Resumo geral
if menu == "📊 Resumo Geral":
    total_boletos = len(boletos)
    vencidos = boletos[boletos["Status"] == "Vencido"]
    pagos = boletos[boletos["Status"] == "Pago"]
    abertos = total_boletos - len(vencidos) - len(pagos)
    total_pago = pagos["Valor"].sum()

    st.subheader("📊 Resumo Financeiro")
    st.metric("Total de Boletos", total_boletos)
    st.metric("Boletos Vencidos", len(vencidos))
    st.metric("Boletos Pagos", len(pagos))
    st.metric("Valor Total Pago", f"R$ {total_pago:,.2f}".replace(".", ","))
    st.metric("Boletos em Aberto", abertos)

# Cancelar assinatura
elif menu == "🧾 Cancelar Assinatura":
    st.subheader("🧾 Cancelar Assinatura")
    documento = st.text_input("CPF ou CNPJ do cliente")
    if st.button("Cancelar assinatura"):
        st.success(f"Assinatura de {documento} cancelada com sucesso (simulado).")

# Deletar boletos
elif menu == "💣 Deletar Boletos":
    st.subheader("💣 Deletar Boletos (Simulado)")
    documento = st.text_input("CPF ou CNPJ do cliente")
    if documento:
        boletos_cliente = boletos[boletos["CPF/CNPJ"] == documento]
        st.dataframe(boletos_cliente)
        if st.button("Deletar todos os boletos (simulado)"):
            st.success(f"Boletos de {documento} deletados com sucesso (simulado).")

# Relatório de clientes com 3 boletos vencidos
elif menu == "🚨 Clientes com 3 Boletos Vencidos":
    st.subheader("🚨 Clientes com 3 Boletos Vencidos")
    vencidos = boletos[boletos["Status"] == "Vencido"]
    contagem = vencidos["CPF/CNPJ"].value_counts()
    clientes_com_3 = contagem[contagem == 3].index.tolist()
    resultado = boletos[boletos["CPF/CNPJ"].isin(clientes_com_3)]
    st.dataframe(resultado[["Nome", "CPF/CNPJ"]].drop_duplicates())
    st.download_button("📥 Baixar Excel", data=resultado.to_csv(index=False), file_name="clientes_com_3_vencidos.csv", mime="text/csv")

# Relatório de pagamentos
elif menu == "📅 Relatório de Pagamentos":
    st.subheader("📅 Relatório de Boletos Pagos")
    pagos = boletos[boletos["Status"] == "Pago"]
    pagos["Data de Pagamento"] = pd.to_datetime(pagos["Data de Pagamento"])
    total_pago = pagos["Valor"].sum()
    st.metric("Total Pago no Período", f"R$ {total_pago:,.2f}".replace(".", ","))
    st.dataframe(pagos)
    st.download_button("📥 Baixar Pagamentos", data=pagos.to_csv(index=False), file_name="boletos_pagos.csv", mime="text/csv")
