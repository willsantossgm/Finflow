import os
from datetime import date
import json
import streamlit as st
import pandas as pd
import altair as alt

# Importando a classe do nosso backend
from backend.financas import GerenciadorFinancas

# Configuração da página do Streamlit
st.set_page_config(
    page_title="FinFlow - Controle Financeiro Premium",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização personalizada via CSS para dar um toque premium e moderno
st.markdown("""
    <style>
    /* Estilo do título */
    .title-container {
        background: linear-gradient(135deg, #0f766e 0%, #115e59 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .title-text {
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 700;
        font-size: 2.5rem;
        margin: 0;
        letter-spacing: 1px;
        color: #99f2c8;
    }
    .subtitle-text {
        font-family: 'Inter', sans-serif;
        font-weight: 300;
        font-size: 1.1rem;
        opacity: 0.9;
        margin-top: 0.5rem;
        color: #e2e8f0;
    }
    /* Estilos dos painéis de saldo */
    .metric-card {
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        border: 1px solid #334155;
        text-align: center;
    }
    .saldo-positivo {
        background-color: #064e3b;
        border-left: 5px solid #10b981;
        color: #10b981;
    }
    .saldo-negativo {
        background-color: #7f1d1d;
        border-left: 5px solid #ef4444;
        color: #f87171;
    }
    .metric-title {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        opacity: 0.8;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin-top: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Definição dos caminhos dos arquivos de dados
ARQUIVO_DADOS = "dados_financeiros.json"
ARQUIVO_CONFIG = "config_financas.json"

# Inicialização e persistência no Session State do Streamlit
if "gerenciador" not in st.session_state:
    st.session_state.gerenciador = GerenciadorFinancas()
    if os.path.exists(ARQUIVO_DADOS):
        try:
            st.session_state.gerenciador.carregar_dados(ARQUIVO_DADOS)
        except Exception as e:
            st.error(f"Erro ao carregar dados salvos: {e}")

# Carregar configurações iniciais (Renda, Limite de Gastos e Categorias)
if "renda_mensal" not in st.session_state:
    st.session_state.renda_mensal = 0.0
if "limite_gastos" not in st.session_state:
    st.session_state.limite_gastos = 1500.0
if "categorias" not in st.session_state:
    st.session_state.categorias = ["Alimentação", "Moradia", "Transporte", "Lazer", "Saúde"]

if os.path.exists(ARQUIVO_CONFIG):
    try:
        with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as f:
            config = json.load(f)
            st.session_state.renda_mensal = config.get("renda_mensal", 0.0)
            st.session_state.limite_gastos = config.get("limite_gastos", 1500.0)
            if "categorias" in config:
                st.session_state.categorias = config["categorias"]
    except Exception:
        pass

# Cabeçalho da aplicação
st.markdown("""
    <div class="title-container">
        <h1 class="title-text">✨ FinFlow</h1>
        <p class="subtitle-text">Controle Financeiro Premium • Design Moderno & Gestão Inteligente</p>
    </div>
""", unsafe_allow_html=True)

# ----------------- BARRA LATERAL (SIDEBAR) -----------------
st.sidebar.markdown("### ⚙️ Configurações Gerais")
renda_input = st.sidebar.number_input(
    "Defina sua Renda Mensal (R$):",
    min_value=0.0,
    value=st.session_state.renda_mensal,
    step=100.0,
    format="%.2f"
)

limite_input = st.sidebar.number_input(
    "Defina seu Limite de Gastos (R$):",
    min_value=0.0,
    value=st.session_state.limite_gastos,
    step=100.0,
    format="%.2f"
)

if st.sidebar.button("💾 Salvar Configurações", use_container_width=True):
    st.session_state.renda_mensal = renda_input
    st.session_state.limite_gastos = limite_input
    try:
        with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
            json.dump({
                "renda_mensal": renda_input,
                "limite_gastos": limite_input,
                "categorias": st.session_state.categorias
            }, f)
        st.sidebar.success("Configurações salvas!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Erro ao salvar configurações: {e}")

# ----------------- PAINEL CENTRAL (SALDO) -----------------
renda_atual = st.session_state.renda_mensal
total_gastos = sum(g.valor for g in st.session_state.gerenciador.gastos)
saldo_restante = st.session_state.gerenciador.calcular_saldo_restante(renda_atual)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Renda Mensal", f"R$ {renda_atual:,.2f}")

with col2:
    st.metric("Total de Gastos", f"R$ {total_gastos:,.2f}")

with col3:
    if saldo_restante >= 0:
        st.markdown(f"""
            <div class="metric-card saldo-positivo">
                <div class="metric-title">Saldo Restante</div>
                <div class="metric-value">R$ {saldo_restante:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="metric-card saldo-negativo">
                <div class="metric-title">Saldo Restante (Déficit)</div>
                <div class="metric-value">R$ {saldo_restante:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ----------------- SEÇÃO: METAS E LIMITE DE GASTOS -----------------
limite_mensal = st.session_state.limite_gastos
if limite_mensal > 0:
    porcentagem_limite = min(total_gastos / limite_mensal, 1.0)

    st.markdown("### 🎯 Minhas Metas")

    # Exibe informações numéricas claras
    col_meta1, col_meta2 = st.columns([3, 1])
    with col_meta1:
        st.progress(porcentagem_limite)
    with col_meta2:
        st.markdown(f"Consumido: **R$ {total_gastos:,.2f}** de **R$ {limite_mensal:,.2f}** ({porcentagem_limite*100:.1f}%)")

    # Alertas visuais com base no consumo do limite
    if total_gastos >= limite_mensal:
        st.error(f"🚨 **Limite de gastos excedido!** Você ultrapassou o seu teto planejado de R$ {limite_mensal:,.2f}.")
    elif total_gastos >= limite_mensal * 0.8:
        st.warning(f"⚠️ **Cuidado!** Você está quase atingindo seu limite (mais de 80% do teto de R$ {limite_mensal:,.2f} consumido).")
    else:
        st.success("✅ Seu nível de gastos está dentro da meta estipulada para o mês.")

    st.markdown("---")

# ----------------- CORPO PRINCIPAL: ADICIONAR E LISTAR -----------------
col_form, col_list = st.columns([1, 2])

with col_form:
    st.markdown("### 📝 Adicionar Novo Gasto")
    
    # Estados locais de valor para limpar após adicionar gasto
    if "val_descricao" not in st.session_state:
        st.session_state.val_descricao = ""
    if "val_valor" not in st.session_state:
        st.session_state.val_valor = 0.0

    descricao = st.text_input("Descrição do Gasto", value=st.session_state.val_descricao, placeholder="Ex: Mercado Municipal, Gasolina, Uber")
    valor = st.number_input("Valor (R$)", min_value=0.0, value=st.session_state.val_valor, step=5.0, format="%.2f")
    
    # Monta as opções do dropdown com a opção especial no final
    opcoes_dropdown_cat = st.session_state.categorias + ["➕ Criar Nova Categoria..."]
    
    # Garante a categoria selecionada ativa
    if "selected_categoria" not in st.session_state:
        st.session_state.selected_categoria = st.session_state.categorias[0]
        
    try:
        default_idx = opcoes_dropdown_cat.index(st.session_state.selected_categoria)
    except ValueError:
        default_idx = 0

    categoria_selecionada = st.selectbox(
        "Categoria",
        options=opcoes_dropdown_cat,
        index=default_idx
    )

    # Condicional reativa para criar nova categoria
    if categoria_selecionada == "➕ Criar Nova Categoria...":
        nova_categoria_input = st.text_input("Digite o nome da nova categoria:", placeholder="Ex: Educação, Presentes").strip()
        if st.button("Salvar Categoria", use_container_width=True):
            if nova_categoria_input:
                cat_normalizada = nova_categoria_input.capitalize()
                if cat_normalizada not in st.session_state.categorias:
                    st.session_state.categorias.append(cat_normalizada)
                    # Define a categoria recém-criada como selecionada
                    st.session_state.selected_categoria = cat_normalizada
                    try:
                        # Salva permanentemente as categorias
                        with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
                            json.dump({
                                "renda_mensal": st.session_state.renda_mensal,
                                "limite_gastos": st.session_state.limite_gastos,
                                "categorias": st.session_state.categorias
                            }, f)
                        st.success(f"Categoria '{cat_normalizada}' criada e selecionada!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar nova categoria: {e}")
                else:
                    st.warning("Esta categoria já existe!")
            else:
                st.error("Por favor, digite um nome válido.")
    else:
        st.session_state.selected_categoria = categoria_selecionada

    data_gasto = st.date_input("Data do Gasto", value=date.today())

    if st.button("Adicionar Gasto ➕", use_container_width=True):
        if not descricao.strip():
            st.error("Por favor, preencha a descrição do gasto.")
        elif valor <= 0:
            st.error("O valor do gasto deve ser maior que zero.")
        elif st.session_state.selected_categoria == "➕ Criar Nova Categoria...":
            st.error("Por favor, crie e salve a nova categoria primeiro ou escolha uma existente.")
        else:
            try:
                # Adiciona e persiste os dados
                st.session_state.gerenciador.adicionar_gasto(
                    descricao=descricao,
                    valor=valor,
                    categoria=st.session_state.selected_categoria,
                    data=data_gasto
                )
                st.session_state.gerenciador.salvar_dados(ARQUIVO_DADOS)
                st.success("Gasto adicionado e salvo com sucesso!")
                
                # Reseta os campos de entrada redefinindo as variáveis do Session State
                st.session_state.val_descricao = ""
                st.session_state.val_valor = 0.0
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao adicionar gasto: {e}")

with col_list:
    st.markdown("### 📊 Histórico de Gastos")

    gastos = st.session_state.gerenciador.gastos

    if len(gastos) == 0:
        st.info("Nenhum gasto cadastrado até o momento.")
    else:
        # Prepara os dados para serem mostrados numa tabela limpa
        dados_tabela = []
        for g in reversed(gastos): # Mostra os mais recentes primeiro
            dados_tabela.append({
                "Descrição": g.descricao,
                "Valor (R$)": f"R$ {g.valor:.2f}",
                "Categoria": g.categoria,
                "Data": g.data.strftime("%d/%m/%Y")
            })

        st.dataframe(dados_tabela, use_container_width=True)

        # Botão para exportar dados em CSV
        df_export = pd.DataFrame([
            {
                "ID": g.id,
                "Descrição": g.descricao,
                "Valor (R$)": g.valor,
                "Categoria": g.categoria,
                "Data": g.data.strftime("%Y-%m-%d")
            }
            for g in gastos
        ])
        csv_data = df_export.to_csv(index=False).encode("utf-8")
        
        st.download_button(
            label="📥 Exportar Gastos (CSV)",
            data=csv_data,
            file_name="gastos_finflow.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.markdown("---")

        # Exclusão de Gastos
        st.markdown("### 🗑️ Excluir Gasto")
        opcoes_exclusao = {
            gasto.id: f"{gasto.descricao} (R$ {gasto.valor:.2f} - {gasto.data.strftime('%d/%m/%Y')})"
            for gasto in gastos
        }
        
        gasto_selecionado_id = st.selectbox(
            "Selecione um gasto para excluir:",
            options=list(opcoes_exclusao.keys()),
            format_func=lambda x: opcoes_exclusao[x],
            key="gasto_excluir_select"
        )
        
        if st.button("Excluir Gasto 🗑️", use_container_width=True):
            if gasto_selecionado_id:
                if st.session_state.gerenciador.remover_gasto(gasto_selecionado_id):
                    try:
                        st.session_state.gerenciador.salvar_dados(ARQUIVO_DADOS)
                        st.success("Gasto excluído com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar dados após exclusão: {e}")
                else:
                    st.error("Erro interno ao tentar remover o gasto.")

        st.markdown("---")

        # Gráfico de distribuição por categoria para dar mais apelo visual
        st.markdown("#### Distribuição de Gastos por Categoria")
        resumo_categorias = st.session_state.gerenciador.agrupar_e_somar_por_categoria()
        if resumo_categorias:
            col_graf1, col_graf2 = st.columns(2)

            df_categorias = pd.DataFrame([
                {"Categoria": cat, "Valor (R$)": total}
                for cat, total in resumo_categorias.items()
            ])

            # Calcula a porcentagem para mostrar no gráfico
            total_geral = df_categorias["Valor (R$)"].sum()
            df_categorias["Porcentagem (%)"] = (df_categorias["Valor (R$)"] / total_geral * 100).round(1)

            with col_graf1:
                st.markdown("<p style='text-align: center; font-size: 0.95rem; opacity: 0.9;'>Total Gasto por Categoria (R$)</p>", unsafe_allow_html=True)
                st.bar_chart(df_categorias, x="Categoria", y="Valor (R$)", color="Categoria", use_container_width=True)

            with col_graf2:
                st.markdown("<p style='text-align: center; font-size: 0.95rem; opacity: 0.9;'>Proporção do Orçamento (%)</p>", unsafe_allow_html=True)
                # Gráfico de rosca interativo com Altair
                grafico_rosca = alt.Chart(df_categorias).mark_arc(innerRadius=60).encode(
                    theta=alt.Theta(field="Valor (R$)", type="quantitative"),
                    color=alt.Color(
                        field="Categoria",
                        type="nominal",
                        scale=alt.Scale(scheme="tealblues") # Tons modernos combinando com a estética
                    ),
                    tooltip=["Categoria", "Valor (R$)", "Porcentagem (%)"]
                ).properties(height=260).interactive()

                st.altair_chart(grafico_rosca, use_container_width=True)
