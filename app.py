import streamlit as st
import pandas as pd
import os
from PIL import Image
from datetime import datetime
import google.generativeai as genai

# Configuração da página
st.set_page_config(page_title="Livro de Receitas do Vinícius", page_icon="🍳", layout="wide")

# Configuração da IA (Gemini)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    modelo_ia = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    modelo_ia = None

# Variáveis de sessão para preenchimento automático da IA
if "ingredientes_ia" not in st.session_state:
    st.session_state.ingredientes_ia = ""
if "preparo_ia" not in st.session_state:
    st.session_state.preparo_ia = ""

# Pastas e arquivos
PASTA_IMAGENS = "imagens_receitas"
ARQUIVO_DADOS = "minhas_receitas.csv"

if not os.path.exists(PASTA_IMAGENS):
    os.makedirs(PASTA_IMAGENS)

st.title("🍳 Meu Livro de Receitas")

aba_cadastrar, aba_visualizar = st.tabs(["Cadastrar Nova Receita", "Minhas Receitas"])

# ABA 1: CADASTRO
with aba_cadastrar:
    st.header("Adicionar Receita")
    
    nome_receita = st.text_input("Nome do Prato (ex: Hambúrguer Artesanal, Lamen, etc.)")
    
    # NOVAS FUNCIONALIDADES: Categorias e Avaliação divididas em colunas
    col_cat, col_nota = st.columns(2)
    with col_cat:
        opcoes_categorias = ["Lanches", "Massas", "Carnes", "Sobremesas", "Saudável", "Asiática", "Hambúrguer", "Lamen"]
        categorias = st.multiselect("Categorias (Tags)", opcoes_categorias)
    with col_nota:
        nota = st.slider("Avaliação (Estrelas)", 1, 5, 5)
    
    # Text areas puxando o valor da session_state (gerado pela IA)
    ingredientes = st.text_area("Ingredientes", value=st.session_state.ingredientes_ia, height=150)
    modo_preparo = st.text_area("Modo de Preparo", value=st.session_state.preparo_ia, height=150)
    
    st.subheader("📸 Foto do Prato")
    
    # NOVO VISUAL: Trocando o st.radio por abas para um visual de botões profissionais
    aba_camera, aba_upload = st.tabs(["📷 Usar Câmera", "📂 Enviar Arquivo"])
    
    foto = None
    with aba_camera:
        foto_cam = st.camera_input("Tire a foto diretamente pelo celular")
        if foto_cam: foto = foto_cam
        
    with aba_upload:
        foto_up = st.file_uploader("Ou selecione uma imagem da galeria", type=["jpg", "jpeg", "png"])
        if foto_up: foto = foto_up

    # Botão da Inteligência Artificial
    if foto and modelo_ia:
        if st.button("✨ Gerar Receita com IA (Mágica!)", use_container_width=True):
            with st.spinner("Analisando o prato e escrevendo a receita..."):
                img = Image.open(foto)
                
                # Pedindo para a IA analisar a imagem
                prompt_ingredientes = "Liste apenas os prováveis ingredientes da comida nesta foto, um por linha, sem introduções."
                prompt_preparo = "Crie um modo de preparo passo a passo provável para a comida da foto, de forma direta."
                
                try:
                    res_ingredientes = modelo_ia.generate_content([prompt_ingredientes, img])
                    res_preparo = modelo_ia.generate_content([prompt_preparo, img])
                    
                    # Atualiza os campos na tela
                    st.session_state.ingredientes_ia = res_ingredientes.text
                    st.session_state.preparo_ia = res_preparo.text
                    st.rerun() # Recarrega a tela com os textos preenchidos
                except Exception as e:
                    st.error("Erro ao conectar com a IA. Verifique sua chave de API nos Secrets do Streamlit.")

    # Botão de Salvar
    if st.button("Salvar Receita", type="primary", use_container_width=True):
        if nome_receita and foto:
            # 1. Salvar a imagem física na pasta
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            caminho_imagem = f"{PASTA_IMAGENS}/img_{timestamp}.jpg"
            
            Image.open(foto).save(caminho_imagem)
            
            # 2. Salvar os dados no CSV (agora incluindo Nota e Categorias)
            nova_receita = pd.DataFrame([{
                "Data": datetime.now().strftime("%d/%m/%Y"),
                "Nome": nome_receita,
                "Categorias": ", ".join(categorias),
                "Nota": "⭐" * nota,
                "Ingredientes": ingredientes,
                "Preparo": modo_preparo,
                "Caminho_Imagem": caminho_imagem
            }])
            
            if os.path.exists(ARQUIVO_DADOS):
                df_receitas = pd.read_csv(ARQUIVO_DADOS)
                df_receitas = pd.concat([df_receitas, nova_receita], ignore_index=True)
            else:
                df_receitas = nova_receita
                
            df_receitas.to_csv(ARQUIVO_DADOS, index=False)
            
            # Limpa as áreas de texto geradas pela IA após salvar
            st.session_state.ingredientes_ia = ""
            st.session_state.preparo_ia = ""
            st.success(f"Receita de '{nome_receita}' salva com sucesso!")
        else:
            st.error("Por favor, preencha o nome da receita e inclua uma foto.")

# ABA 2: VISUALIZAÇÃO
with aba_visualizar:
    st.header("Minhas Receitas Salvas")
    
    if os.path.exists(ARQUIVO_DADOS):
        df_receitas = pd.read_csv(ARQUIVO_DADOS)
        
        # Inverte o dataframe para mostrar as mais recentes primeiro
        df_receitas = df_receitas.iloc[::-1]
        
        for index, row in df_receitas.iterrows():
            # Tratamento para não dar erro com receitas antigas que não tinham nota/categoria
            nota_display = row['Nota'] if 'Nota' in row and pd.notna(row['Nota']) else ""
            cat_display = f" | 🏷️ {row['Categorias']}" if 'Categorias' in row and pd.notna(row['Categorias']) and row['Categorias'] != "" else ""
            
            with st.expander(f"🍽️ {row['Nome']} {nota_display} (Adicionada em {row['Data']}){cat_display}"):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    if pd.notna(row["Caminho_Imagem"]) and os.path.exists(row["Caminho_Imagem"]):
                        st.image(row["Caminho_Imagem"], use_container_width=True)
                    else:
                        st.warning("Imagem não encontrada.")
                        
                with col2:
                    st.markdown("### Ingredientes")
                    st.write(row["Ingredientes"])
                    
                    st.markdown("### Modo de Preparo")
                    st.write(row["Preparo"])
    else:
        st.info("Nenhuma receita cadastrada ainda. Vá para a aba 'Cadastrar Nova Receita' para começar!")
