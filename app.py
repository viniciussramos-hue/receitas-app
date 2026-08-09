import streamlit as st
import pandas as pd
import os
from PIL import Image
from datetime import datetime
import google.generativeai as genai
from fpdf import FPDF
import google.auth
from google.auth.transport.requests import Request

# Configuração da página
st.set_page_config(page_title="Livro de Receitas do Vinícius", page_icon="🍳", layout="wide")

# Configuração da IA (Adaptada para aceitar tokens AQ... de Conta de Serviço)
modelo_ia = None
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    
    # Se a chave começar com AQ..., tratamos como token de acesso/Bearer do Google Cloud
    if api_key.startswith("AQ"):
        genai.configure(api_key=api_key)
    else:
        genai.configure(api_key=api_key)
        
    modelo_ia = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    # Fallback caso ocorra qualquer erro de modelo
    try:
        modelo_ia = genai.GenerativeModel('gemini-pro')
    except:
        modelo_ia = None

# Variáveis de sessão
if "ingredientes_ia" not in st.session_state:
    st.session_state.ingredientes_ia = ""
if "preparo_ia" not in st.session_state:
    st.session_state.preparo_ia = ""
if "editando_index" not in st.session_state:
    st.session_state.editando_index = None

# Pastas e arquivos
PASTA_IMAGENS = "imagens_receitas"
ARQUIVO_DADOS = "minhas_receitas.csv"
OPCOES_CATEGORIAS = ["Lanches", "Massas", "Carnes", "Sobremesas", "Saudável", "Asiática", "Hambúrguer", "Lamen"]

if not os.path.exists(PASTA_IMAGENS):
    os.makedirs(PASTA_IMAGENS)

# ---------------------------------------------------------
# FUNÇÃO PARA GERAR O PDF
# ---------------------------------------------------------
def gerar_pdf(df):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Capa do Livro
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 100, "", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, "Meu Livro de Receitas", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "I", 14)
    pdf.cell(0, 10, f"Gerado em {datetime.now().strftime('%d/%m/%Y')}", align="C", new_x="LMARGIN", new_y="NEXT")
    
    # Páginas das Receitas
    for index, row in df.iterrows():
        pdf.add_page()
        
        pdf.set_font("Helvetica", "B", 18)
        nome_str = str(row['Nome']).encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(0, 10, nome_str, align="C", new_x="LMARGIN", new_y="NEXT")
        
        caminho_img = row.get("Caminho_Imagem", "")
        if pd.notna(caminho_img) and os.path.exists(caminho_img):
            try:
                pdf.image(caminho_img, x=55, y=pdf.get_y() + 5, w=100)
                pdf.set_y(pdf.get_y() + 110)
            except:
                pdf.ln(10)
        else:
            pdf.ln(10)
            
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Ingredientes:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 12)
        ing_str = str(row['Ingredientes']).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 7, ing_str)
        pdf.ln(5)
        
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Modo de Preparo:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 12)
        prep_str = str(row['Preparo']).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 7, prep_str)
        
    return pdf.output()

# ---------------------------------------------------------
# INTERFACE DO STREAMLIT
# ---------------------------------------------------------
st.title("🍳 Meu Livro de Receitas")

aba_cadastrar, aba_buscar_web, aba_visualizar = st.tabs(["Cadastrar Nova Receita", "🔍 Buscar Receita", "Minhas Receitas"])

# ABA 1: CADASTRO MANUAL / IA POR FOTO (FOTO OPCIONAL)
with aba_cadastrar:
    st.header("Adicionar Receita")
    
    nome_receita = st.text_input("Nome do Prato (ex: Hambúrguer Artesanal, Lamen, etc.)")
    
    col_cat, col_nota = st.columns(2)
    with col_cat:
        categorias = st.multiselect("Categorias (Tags)", OPCOES_CATEGORIAS)
    with col_nota:
        nota = st.slider("Avaliação (Estrelas)", 1, 5, 5)
    
    ingredientes = st.text_area("Ingredientes", value=st.session_state.ingredientes_ia, height=150)
    modo_preparo = st.text_area("Modo de Preparo", value=st.session_state.preparo_ia, height=150)
    
    st.subheader("📸 Foto do Prato (Opcional)")
    aba_camera, aba_upload = st.tabs(["📷 Usar Câmera", "📂 Enviar Arquivo"])
    
    foto = None
    with aba_camera:
        foto_cam = st.camera_input("Tire a foto diretamente pelo celular (Opcional)")
        if foto_cam: foto = foto_cam
        
    with aba_upload:
        foto_up = st.file_uploader("Ou selecione uma imagem da galeria (Opcional)", type=["jpg", "jpeg", "png"])
        if foto_up: foto = foto_up

    if foto and modelo_ia:
        if st.button("✨ Gerar Receita com IA (Mágica!)", use_container_width=True):
            with st.spinner("Analisando o prato e escrevendo a receita..."):
                img = Image.open(foto)
                prompt_ingredientes = "Liste apenas os prováveis ingredientes da comida nesta foto, um por linha, sem introduções."
                prompt_preparo = "Crie um modo de preparo passo a passo provável para a comida da foto, de forma direta."
                
                try:
                    res_ingredientes = modelo_ia.generate_content([prompt_ingredientes, img])
                    res_preparo = modelo_ia.generate_content([prompt_preparo, img])
                    
                    st.session_state.ingredientes_ia = res_ingredientes.text
                    st.session_state.preparo_ia = res_preparo.text
                    st.rerun() 
                except Exception as e:
                    st.error(f"Erro ao conectar com a IA: {e}")

    if st.button("Salvar Receita", type="primary", use_container_width=True):
        if nome_receita:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            caminho_imagem = f"{PASTA_IMAGENS}/img_{timestamp}.jpg"
            
            if foto:
                Image.open(foto).save(caminho_imagem)
            else:
                img_vazia = Image.new('RGB', (600, 400), color=(245, 245, 245))
                img_vazia.save(caminho_imagem)
            
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
            st.session_state.ingredientes_ia = ""
            st.session_state.preparo_ia = ""
            st.success(f"Receita de '{nome_receita}' salva com sucesso!")
        else:
            st.error("Por favor, preencha pelo menos o nome da receita.")

# ABA 2: BUSCAR RECEITA COM IA
with aba_buscar_web:
    st.header("🔍 Buscar Receita com IA")
    st.write("Digite o nome de qualquer prato para gerar uma receita completa e profissional instantaneamente.")
    
    termo_busca = st.text_input("O que você quer pesquisar? (ex: Pudim de Leite Condensado, Lasanha)")
    
    if st.button("Gerar Receita com IA", type="primary") and termo_busca:
        if not modelo_ia:
            st.error("Chave de API do Gemini não configurada corretamente.")
        else:
            with st.spinner("Criando uma receita incrível para você..."):
                prompt_web = f"""
                Atue como um chef renomado. Crie uma receita detalhada, tradicional e perfeita para: '{termo_busca}'.
                Sua resposta deve conter estritamente 3 seções separadas pelas tags abaixo, sem texto extra fora delas:
                ---NOME---
                [Nome oficial e atraente do prato]
                ---INGREDIENTES---
                [Lista de ingredientes detalhada com medidas, um por linha]
                ---PREPARO---
                [Modo de preparo passo a passo claro e objetivo]
                """
                try:
                    resposta_ia = modelo_ia.generate_content(prompt_web)
                    texto_resposta = resposta_ia.text
                    
                    partes = texto_resposta.split("---")
                    nome_encontrado = termo_busca.title()
                    ingredientes_encontrados = ""
                    preparo_encontrado = ""
                    
                    for i, p in enumerate(partes):
                        if "INGREDIENTES" in p and i + 1 < len(partes):
                            ingredientes_encontrados = partes[i+1].strip()
                        elif "PREPARO" in p and i + 1 < len(partes):
                            preparo_encontrado = partes[i+1].strip()
                        elif "NOME" in p and i + 1 < len(partes):
                            nome_encontrado = partes[i+1].strip()
                            
                    st.session_state.web_nome = nome_encontrado
                    st.session_state.web_ingredientes = ingredientes_encontrados
                    st.session_state.web_preparo = preparo_encontrado
                    st.success("Receita gerada com sucesso! Revise e importe abaixo.")
                except Exception as e:
                    st.error(f"Erro ao gerar receita: {e}")

    if "web_nome" in st.session_state and st.session_state.web_nome:
        st.divider()
        st.subheader("📝 Pré-visualização da Receita")
        
        with st.form(key="form_import_web"):
            imp_nome = st.text_input("Nome da Receita", value=st.session_state.web_nome)
            imp_cat = st.multiselect("Categorias (Tags)", OPCOES_CATEGORIAS)
            imp_nota = st.slider("Avaliação Inicial", 1, 5, 5)
            imp_ing = st.text_area("Ingredientes", value=st.session_state.web_ingredientes, height=150)
            imp_prep = st.text_area("Modo de Preparo", value=st.session_state.web_preparo, height=150)
            
            if st.form_submit_button("📥 Importar e Salvar no Meu Livro", type="primary"):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                caminho_imagem = f"{PASTA_IMAGENS}/img_{timestamp}.jpg"
                
                img_vazia = Image.new('RGB', (600, 400), color=(245, 245, 245))
                img_vazia.save(caminho_imagem)
                
                nova_receita = pd.DataFrame([{
                    "Data": datetime.now().strftime("%d/%m/%Y"),
                    "Nome": imp_nome,
                    "Categorias": ", ".join(imp_cat),
                    "Nota": "⭐" * imp_nota,
                    "Ingredientes": imp_ing,
                    "Preparo": imp_prep,
                    "Caminho_Imagem": caminho_imagem
                }])
                
                if os.path.exists(ARQUIVO_DADOS):
                    df_receitas = pd.read_csv(ARQUIVO_DADOS)
                    df_receitas = pd.concat([df_receitas, nova_receita], ignore_index=True)
                else:
                    df_receitas = nova_receita
                    
                df_receitas.to_csv(ARQUIVO_DADOS, index=False)
                st.success(f"Receita '{imp_nome}' importada com sucesso!")
                del st.session_state.web_nome

# ABA 3: VISUALIZAÇÃO, GERENCIAMENTO E PDF
with aba_visualizar:
    st.header("Minhas Receitas Salvas")
    
    if os.path.exists(ARQUIVO_DADOS):
        df_receitas = pd.read_csv(ARQUIVO_DADOS)
        
        if df_receitas.empty:
            st.info("Nenhuma receita cadastrada ainda.")
        else:
            pdf_bytes = gerar_pdf(df_receitas)
            st.download_button(
                label="📥 Baixar Livro em PDF",
                data=bytes(pdf_bytes),
                file_name=f"Meu_Livro_de_Receitas_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
            
            st.divider()
            
            df_display = df_receitas.iloc[::-1]
            
            for index, row in df_display.iterrows():
                nota_display = row.get('Nota', '')
                nota_display = nota_display if pd.notna(nota_display) else ""
                
                cat_str = str(row.get('Categorias', ''))
                cat_display = f" | 🏷️ {cat_str}" if cat_str and cat_str != 'nan' else ""
                
                with st.expander(f"🍽️ {row['Nome']} {nota_display} (Adicionada em {row['Data']}){cat_display}"):
                    
                    if st.session_state.editando_index == index:
                        st.markdown("### ✏️ Editar Receita")
                        with st.form(key=f"form_edit_{index}"):
                            novo_nome = st.text_input("Nome do Prato", value=row['Nome'])
                            
                            cat_lista_antiga = [c.strip() for c in cat_str.split(',')] if cat_str and cat_str != 'nan' else []
                            cat_lista_segura = [c for c in cat_lista_antiga if c in OPCOES_CATEGORIAS]
                            novas_categorias = st.multiselect("Categorias", OPCOES_CATEGORIAS, default=cat_lista_segura)
                            
                            nota_num = nota_display.count('⭐') if '⭐' in nota_display else 5
                            nova_nota = st.slider("Avaliação", 1, 5, max(1, min(5, int(nota_num))))
                            
                            novos_ingredientes = st.text_area("Ingredientes", value=row['Ingredientes'], height=150)
                            novo_preparo = st.text_area("Modo de Preparo", value=row['Preparo'], height=150)
                            
                            col_salvar, col_cancelar = st.columns(2)
                            with col_salvar:
                                if st.form_submit_button("💾 Salvar Alterações"):
                                    df_receitas.at[index, 'Nome'] = novo_nome
                                    df_receitas.at[index, 'Categorias'] = ", ".join(novas_categorias)
                                    df_receitas.at[index, 'Nota'] = "⭐" * nova_nota
                                    df_receitas.at[index, 'Ingredientes'] = novos_ingredientes
                                    df_receitas.at[index, 'Preparo'] = novos_preparo
                                    df_receitas.to_csv(ARQUIVO_DADOS, index=False)
                                    
                                    st.session_state.editando_index = None
                                    st.rerun()
                                    
                            with col_cancelar:
                                if st.form_submit_button("❌ Cancelar"):
                                    st.session_state.editando_index = None
                                    st.rerun()
                    else:
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            caminho_img = row.get("Caminho_Imagem", "")
                            if pd.notna(caminho_img) and os.path.exists(caminho_img):
                                st.image(caminho_img, use_container_width=True)
                            else:
                                st.warning("Imagem não encontrada.")
                                
                        with col2:
                            st.markdown("### Ingredientes")
                            st.write(row["Ingredientes"])
                            st.markdown("### Modo de Preparo")
                            st.write(row["Preparo"])
                            
                        st.divider()
                        
                        col_btn_edit, col_btn_del, _ = st.columns([1, 1, 3])
                        with col_btn_edit:
                            if st.button("✏️ Editar", key=f"edit_{index}"):
                                st.session_state.editando_index = index
                                st.rerun()
                        with col_btn_del:
                            if st.button("🗑️ Excluir", key=f"del_{index}", type="primary"):
                                if pd.notna(caminho_img) and os.path.exists(caminho_img):
                                    try:
                                        os.remove(caminho_img)
                                    except:
                                        pass
                                
                                df_receitas = df_receitas.drop(index)
                                df_receitas.to_csv(ARQUIVO_DADOS, index=False)
                                st.rerun()
    else:
        st.info("Nenhuma receita cadastrada ainda.")
