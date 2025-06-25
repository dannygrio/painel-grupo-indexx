import streamlit as st
import pandas as pd
from datetime import datetime

# Simulação de dados (normalmente viria da API Kobana)
boletos = pd.DataFrame({
    "Nome": ["João Silva", "Ana Lima", "Carlos Souza", "João Silva", "Ana Lima", "Carlos Souza", "João Silva"],
    "CPF/CNPJ": ["123.456.789-00", "234.567.890-00", "345.678.901-00", "123.456.789-00", "234.567.890-00", "345.678.901-00", "123.456.789-00"],
    "Status": ["Vencido", "Vencido", "Pago", "Vencido", "Pago", "Vencido", "Vencido"],
    "Valor": [200.00, 150.00, 300.00, 180.00, 150.00, 210.00, 220.00],
    "Data de Vencimento": ["2025-06-01", "2025-06-01", "2025-06-01", "2025-06-05", "2025-06-05", "2025-06-06", "2025-06-07"],
    "Data de Pagamento": ["", "", "2025-06-01", "", "2025-06-05", "", ""]
})

# Título e login
st.title("🔐 Painel Interno – Gestão Grupo Indexx")

senha = st.text_input("Digite a senha de acesso", type="password")
if senha != "admin123":
    st.warning("Acesso restrito. Digite a senha correta.")
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
