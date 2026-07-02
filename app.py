import os
from datetime import date, timedelta
import json
import streamlit as st
import pandas as pd
import altair as alt
import requests

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

# Definição dos caminhos dos arquivos de dados e config locais
ARQUIVO_DADOS = "dados_financeiros.json"
ARQUIVO_CONFIG = "config_financas.json"

# Helper functions para Autenticação via Supabase Auth
def supabase_login(email, password):
    url = "https://ojiutbtyaxmpwstgnmnn.supabase.co/auth/v1/token?grant_type=password"
    headers = {
        "apikey": "sb_publishable_c-OH1QCwqmsWCmDj9rMq-w_eaqTJgDQ",
        "Content-Type": "application/json"
    }
    payload = {"email": email, "password": password}
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response
    except Exception:
        return None

def supabase_signup(email, password):
    url = "https://ojiutbtyaxmpwstgnmnn.supabase.co/auth/v1/signup"
    headers = {
        "apikey": "sb_publishable_c-OH1QCwqmsWCmDj9rMq-w_eaqTJgDQ",
        "Content-Type": "application/json"
    }
    payload = {"email": email, "password": password}
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response
    except Exception:
        return None

# ----------------- TELA DE AUTENTICAÇÃO CLERK / SUPABASE RLS -----------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "clerk_user_id" not in st.session_state:
    st.session_state.clerk_user_id = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None

if not st.session_state.authenticated:
    # Cabeçalho da página de login
    st.markdown("""
        <div class="title-container">
            <h1 class="title-text">✨ FinFlow SaaS</h1>
            <p class="subtitle-text">Controle Financeiro Premium • Identidade Segura via Clerk</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='max-width: 500px; margin: 0 auto; padding: 2rem; background-color: #1e293b; border-radius: 12px; border: 1px solid #334155;'>", unsafe_allow_html=True)
    
    auth_option = st.radio("Selecione uma opção:", ["Entrar (Login)", "Registrar-se (Cadastro)"], horizontal=True)
    
    email = st.text_input("E-mail do Clerk", placeholder="nome@provedor.com")
    senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
    
    if auth_option == "Entrar (Login)":
        if st.button("Acessar Conta 🔑", use_container_width=True):
            if email and senha:
                with st.spinner("Conectando ao Clerk..."):
                    res = supabase_login(email, senha)
                    if res is not None and res.status_code == 200:
                        data = res.json()
                        st.session_state.authenticated = True
                        st.session_state.clerk_user_id = f"user_{data['user']['id']}"
                        st.session_state.user_email = email
                        st.success("Autenticado com sucesso!")
                        st.rerun()
                    else:
                        error_detail = res.json().get("error_description", "Senha incorreta ou e-mail inválido.") if res is not None else "Erro de rede ao conectar à nuvem."
                        st.error(f"Erro no Login: {error_detail}")
            else:
                st.error("Preencha todos os campos!")
    else:
        if st.button("Criar Conta Nova 🚀", use_container_width=True):
            if email and senha:
                if len(senha) < 6:
                    st.error("A senha deve ter no mínimo 6 caracteres.")
                else:
                    with st.spinner("Cadastrando no Clerk..."):
                        res = supabase_signup(email, senha)
                        if res is not None and res.status_code in [200, 201]:
                            st.success("Cadastro efetuado! Se necessário, verifique sua caixa de e-mail e faça login.")
                        else:
                            error_detail = res.json().get("message", "E-mail inválido ou já registrado.") if res is not None else "Erro de rede ao conectar à nuvem."
                            st.error(f"Erro no Cadastro: {error_detail}")
            else:
                st.error("Preencha todos os campos!")
                
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop() # Bloqueia toda a renderização abaixo até que faça login!

# ----------------- INICIALIZAÇÃO DO GERENCIADOR AUTENTICADO -----------------
# Garantimos que o GerenciadorFinancas seja instanciado com o ID do Clerk atual
if "gerenciador" not in st.session_state or getattr(st.session_state.gerenciador, "user_id", None) != st.session_state.clerk_user_id or not hasattr(st.session_state.gerenciador, "agrupar_por_categoria_ano"):
    st.session_state.gerenciador = GerenciadorFinancas(user_id=st.session_state.clerk_user_id)
    # Tenta carregar dados do Supabase
    st.session_state.gerenciador.carregar_dados(ARQUIVO_DADOS)

# Carregar configurações locais de Renda e Categorias
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

# Cabeçalho da aplicação (Usuário Logado)
st.markdown(f"""
    <div class="title-container">
        <h1 class="title-text">✨ FinFlow</h1>
        <p class="subtitle-text">Controle Financeiro Premium • Logado como: <b>{st.session_state.user_email}</b></p>
    </div>
""", unsafe_allow_html=True)

# ----------------- BARRA LATERAL (SIDEBAR) -----------------
st.sidebar.markdown("### 👤 Perfil & Autenticação")
st.sidebar.info(f"**Conta:** {st.session_state.user_email}\n\n**Clerk ID:** `{st.session_state.clerk_user_id[:20]}...`")

if st.sidebar.button("🚪 Sair (Logout)", use_container_width=True):
    st.session_state.authenticated = False
    st.session_state.clerk_user_id = None
    st.session_state.user_email = None
    # Limpa o gerenciador
    st.session_state.gerenciador = GerenciadorFinancas()
    st.success("Sessão encerrada!")
    st.rerun()

st.sidebar.markdown("---")
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

# 📅 FILTRO TEMPORAL GLOBAL na Barra Lateral
st.sidebar.markdown("---")
st.sidebar.markdown("### 📅 Filtro de Referência")
meses_disponiveis = st.session_state.gerenciador.obter_meses_disponiveis()
hoje_str = date.today().strftime("%m/%Y")
try:
    default_mes_idx = meses_disponiveis.index(hoje_str)
except ValueError:
    default_mes_idx = len(meses_disponiveis) - 1

mes_filtro = st.sidebar.selectbox(
    "Mês de Referência:",
    options=meses_disponiveis,
    index=default_mes_idx
)

# ----------------- FILTRAGEM DOS DADOS -----------------
gastos_filtrados = st.session_state.gerenciador.filtrar_por_mes_ano(mes_filtro)
renda_atual = st.session_state.renda_mensal
total_gastos = sum(g.valor for g in gastos_filtrados)
saldo_restante = renda_atual - total_gastos

# Criando as abas de Navegação Principal
tab_principal, tab_comparacao = st.tabs(["💰 Controle Financeiro", "📊 Comparação Geral"])

with tab_principal:
    # ----------------- PAINEL CENTRAL (SALDO DO MÊS FILTRADO) -----------------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(f"Renda Mensal ({mes_filtro})", f"R$ {renda_atual:,.2f}")

    with col2:
        st.metric(f"Total de Gastos ({mes_filtro})", f"R$ {total_gastos:,.2f}")

    with col3:
        if saldo_restante >= 0:
            st.markdown(f"""
                <div class="metric-card saldo-positivo">
                    <div class="metric-title">Saldo Restante ({mes_filtro})</div>
                    <div class="metric-value">R$ {saldo_restante:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="metric-card saldo-negativo">
                    <div class="metric-title">Saldo Restante ({mes_filtro})</div>
                    <div class="metric-value">R$ {saldo_restante:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # ----------------- SEÇÃO: METAS E LIMITE DE GASTOS -----------------
    limite_mensal = st.session_state.limite_gastos
    if limite_mensal > 0:
        porcentagem_limite = min(total_gastos / limite_mensal, 1.0)

        st.markdown(f"### 🎯 Metas do Mês ({mes_filtro})")

        col_meta1, col_meta2 = st.columns([3, 1])
        with col_meta1:
            st.progress(porcentagem_limite)
        with col_meta2:
            st.markdown(f"Consumido: **R$ {total_gastos:,.2f}** de **R$ {limite_mensal:,.2f}** ({porcentagem_limite*100:.1f}%)")

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
                        st.session_state.selected_categoria = cat_normalizada
                        try:
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
                    
                    # Reseta os campos
                    st.session_state.val_descricao = ""
                    st.session_state.val_valor = 0.0
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao adicionar gasto: {e}")

    with col_list:
        st.markdown(f"### 📊 Histórico de Gastos ({mes_filtro})")

        if len(gastos_filtrados) == 0:
            st.info(f"Nenhum gasto cadastrado para o mês {mes_filtro}.")
        else:
            dados_tabela = []
            for g in reversed(gastos_filtrados):
                dados_tabela.append({
                    "Descrição": g.descricao,
                    "Valor (R$)": f"R$ {g.valor:.2f}",
                    "Categoria": g.categoria,
                    "Data": g.data.strftime("%d/%m/%Y")
                })

            st.dataframe(dados_tabela, use_container_width=True)

            # Botão de exportação
            df_export = pd.DataFrame([
                {
                    "ID": g.id,
                    "Descrição": g.descricao,
                    "Valor (R$)": g.valor,
                    "Categoria": g.categoria,
                    "Data": g.data.strftime("%Y-%m-%d")
                }
                for g in gastos_filtrados
            ])
            csv_data = df_export.to_csv(index=False).encode("utf-8")
            
            st.download_button(
                label="📥 Exportar Gastos Deste Mês (CSV)",
                data=csv_data,
                file_name=f"gastos_{mes_filtro.replace('/', '_')}.csv",
                mime="text/csv",
                use_container_width=True
            )

            st.markdown("---")

            # Exclusão de Gastos
            st.markdown("### 🗑️ Excluir Gasto")
            opcoes_exclusao = {
                gasto.id: f"{gasto.descricao} (R$ {gasto.valor:.2f} - {gasto.data.strftime('%d/%m/%Y')})"
                for gasto in gastos_filtrados
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

            # Gráficos por Categoria
            st.markdown("#### Distribuição de Gastos por Categoria")
            resumo_categorias = {}
            for g in gastos_filtrados:
                cat_normalizada = g.categoria.strip().capitalize()
                resumo_categorias[cat_normalizada] = resumo_categorias.get(cat_normalizada, 0.0) + g.valor

            if resumo_categorias:
                col_graf1, col_graf2 = st.columns(2)

                df_categorias = pd.DataFrame([
                    {"Categoria": cat, "Valor (R$)": total}
                    for cat, total in resumo_categorias.items()
                ])

                total_geral = df_categorias["Valor (R$)"].sum()
                df_categorias["Porcentagem (%)"] = (df_categorias["Valor (R$)"] / total_geral * 100).round(1)

                with col_graf1:
                    st.markdown("<p style='text-align: center; font-size: 0.95rem; opacity: 0.9;'>Total Gasto por Categoria (R$)</p>", unsafe_allow_html=True)
                    st.bar_chart(df_categorias, x="Categoria", y="Valor (R$)", color="Categoria", use_container_width=True)

                with col_graf2:
                    st.markdown("<p style='text-align: center; font-size: 0.95rem; opacity: 0.9;'>Proporção do Orçamento (%)</p>", unsafe_allow_html=True)
                    grafico_rosca = alt.Chart(df_categorias).mark_arc(innerRadius=60).encode(
                        theta=alt.Theta(field="Valor (R$)", type="quantitative"),
                        color=alt.Color(
                            field="Categoria",
                            type="nominal",
                            scale=alt.Scale(scheme="tealblues")
                        ),
                        tooltip=["Categoria", "Valor (R$)", "Porcentagem (%)"]
                    ).properties(height=260).interactive()

                    st.altair_chart(grafico_rosca, use_container_width=True)

# Nomes dos meses para a Comparação Geral
NOME_MESES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

NOME_MESES_CURTO = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr",
    5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago",
    9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
}

with tab_comparacao:
    st.markdown("## 📊 Comparação Geral")
    st.markdown("Analise o histórico consolidado de gastos organizados por ano e mês, livre de filtros mensais da barra lateral.")
    
    # 1. Filtro de Ano e Seletor de Formato Unificado
    todos_gastos = st.session_state.gerenciador.gastos
    anos_disponiveis = sorted(list(set(g.data.year for g in todos_gastos)))
    ano_atual = date.today().year
    if ano_atual not in anos_disponiveis:
        anos_disponiveis.append(ano_atual)
    anos_disponiveis = sorted(anos_disponiveis)
    
    try:
        default_ano_idx = anos_disponiveis.index(ano_atual)
    except ValueError:
        default_ano_idx = len(anos_disponiveis) - 1
        
    col_ano, col_formato = st.columns([1, 2])
    with col_ano:
        ano_selecionado = st.selectbox(
            "Selecione o Ano de Análise:",
            options=anos_disponiveis,
            index=default_ano_idx
        )
    with col_formato:
        formato_visual = st.radio(
            "📊 Selecione o Formato de Visualização:",
            options=["Rosca ⭕", "Tabela 📋"],
            horizontal=True
        )
    
    # 2. Filtragem e Agrupamento
    gastos_ano = [g for g in todos_gastos if g.data.year == ano_selecionado]
    
    # Inicializa todos os 12 meses com 0.0 para garantir que todos apareçam
    resumo_mensal_ano = {m: 0.0 for m in range(1, 13)}
    for g in gastos_ano:
        resumo_mensal_ano[g.data.month] += g.valor
        
    total_acumulado_ano = sum(resumo_mensal_ano.values())
    
    # 3. Métricas de Destaque
    st.markdown("---")
    
    # Estilizando o cartão de acumulado
    st.markdown(f"""
        <div class="metric-card" style="background-color: #0d9488; border-color: #0f766e; color: white;">
            <div class="metric-title" style="font-size: 1rem; font-weight: 600;">Total Acumulado Gasto em {ano_selecionado}</div>
            <div class="metric-value" style="font-size: 2.5rem; font-weight: 800;">R$ {total_acumulado_ano:,.2f}</div>
        </div>
        <br>
    """, unsafe_allow_html=True)
    
    # Prepara dados mensais
    df_grafico_ano = pd.DataFrame([
        {
            "Mês": NOME_MESES_CURTO[m],
            "Valor": resumo_mensal_ano[m]
        }
        for m in range(1, 13)
    ])
    
    # Prepara dados de categoria
    resumo_cat_ano = st.session_state.gerenciador.agrupar_por_categoria_ano(ano_selecionado)
    if resumo_cat_ano:
        df_cat_ano = pd.DataFrame([
            {"Categoria": cat, "Valor": total}
            for cat, total in resumo_cat_ano.items()
        ])
        total_ano = df_cat_ano["Valor"].sum()
        df_cat_ano["Porcentagem"] = (df_cat_ano["Valor"] / total_ano * 100).round(1)
    else:
        df_cat_ano = pd.DataFrame(columns=["Categoria", "Valor", "Porcentagem"])

    # 4. Renderização Condicional da Tela Inteira
    if formato_visual == "Rosca ⭕":
        # MODO VISUAL (Somente gráficos)
        
        # Linha de Cima: Histórico Mensal
        st.markdown("### 📈 Histórico de Gastos por Mês (R$)")
        chart_monthly = alt.Chart(df_grafico_ano).mark_line(
            color="#0d9488",
            point=alt.OverlayMarkDef(color="#0d9488", size=60)
        ).encode(
            x=alt.X("Mês:N", sort=list(NOME_MESES_CURTO.values()), title="Mês"),
            y=alt.Y("Valor:Q", title="Total Gasto (R$)"),
            tooltip=["Mês", alt.Tooltip("Valor", format="$,.2f", title="Total")]
        ).properties(height=300).interactive()
        st.altair_chart(chart_monthly, use_container_width=True)
        
        st.markdown("---")
        
        # Linha de Baixo: Distribuição por Categoria
        st.markdown("### 🏷️ Distribuição de Gastos por Categoria Anual")
        if not df_cat_ano.empty:
            col_l, col_c, col_r = st.columns([1, 2, 1])
            with col_c:
                st.markdown("<p style='text-align: center; font-size: 1.1rem; font-weight: 600;'>Proporção do Orçamento Anual (%)</p>", unsafe_allow_html=True)
                grafico_pizza_ano = alt.Chart(df_cat_ano).mark_arc(innerRadius=60).encode(
                    theta=alt.Theta(field="Valor", type="quantitative"),
                    color=alt.Color(
                        field="Categoria",
                        type="nominal",
                        scale=alt.Scale(scheme="tealblues")
                    ),
                    tooltip=[
                        alt.Tooltip("Categoria", title="Categoria"),
                        alt.Tooltip("Valor", format="$,.2f", title="Valor"),
                        alt.Tooltip("Porcentagem", format=".1f", title="Proporção (%)")
                    ]
                ).properties(height=320).interactive()
                st.altair_chart(grafico_pizza_ano, use_container_width=True)
        else:
            st.info("Nenhum gasto cadastrado no ano selecionado para analisar categorias.")
            
    else:
        # MODO TABELA (📋) - Esconde todos os gráficos, exibe tabelas mensais e por categoria lado a lado
        col_tab1, col_tab2 = st.columns([1, 1])
        
        with col_tab1:
            st.markdown("### 📅 Tabela Mensal de Gastos")
            df_resumo_ano = pd.DataFrame([
                {
                    "Mês": NOME_MESES[m],
                    "Total Gasto (R$)": f"R$ {resumo_mensal_ano[m]:,.2f}"
                }
                for m in range(1, 13)
            ])
            st.dataframe(df_resumo_ano, use_container_width=True, hide_index=True)
            
        with col_tab2:
            st.markdown("### 🏷️ Detalhamento por Categoria Anual")
            if not df_cat_ano.empty:
                df_resumo_cat_ex = pd.DataFrame()
                df_resumo_cat_ex["Categoria"] = df_cat_ano["Categoria"]
                df_resumo_cat_ex["Valor (R$)"] = df_cat_ano["Valor"].apply(lambda x: f"R$ {x:,.2f}")
                df_resumo_cat_ex["Porcentagem (%)"] = df_cat_ano["Porcentagem"].apply(lambda x: f"{x:.1f}%")
                st.dataframe(df_resumo_cat_ex, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum gasto cadastrado no ano selecionado para analisar categorias.")
