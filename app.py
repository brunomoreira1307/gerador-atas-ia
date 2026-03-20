import streamlit as st
import tempfile
import os
import google.generativeai as genai

# --- Configuração da API do Google ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("⚠️ Chave do Gemini não encontrada nos Secrets do Streamlit!")
    st.stop()

# --- Interface da Página ---
st.set_page_config(page_title="Gerador de Atas", page_icon="🎙️", layout="wide")
st.title("🎙️ Super Gerador de Atas com Gemini")

# --- BUSCADOR AUTOMÁTICO DE TODOS OS MODELOS ---
# Puxa todos os modelos da sua conta que suportam geração de texto/conteúdo
modelos_disponiveis = []
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        modelos_disponiveis.append(m.name)

if not modelos_disponiveis:
    st.error("⚠️ Nenhum modelo de geração encontrado para esta chave de API.")
    st.stop()

# Cria uma caixa de seleção na tela para você escolher o modelo
st.markdown("### ⚙️ Configuração")
modelo_escolhido = st.selectbox("Selecione o modelo 'cérebro' para processar o áudio:", modelos_disponiveis)

# Instancia o modelo escolhido pelo usuário
modelo_gemini = genai.GenerativeModel(modelo_escolhido)

st.divider()
st.markdown("### 📁 Processamento da Reunião")
st.markdown("Faça o upload do áudio. O sistema fará a transcrição e gerará a ata automaticamente.")

arquivo_audio = st.file_uploader("Carregue o áudio (MP3, WAV, M4A, AAC)", type=['mp3', 'wav', 'm4a', 'aac'])

if arquivo_audio is not None:
    st.audio(arquivo_audio)
    
    if st.button("Processar Reunião", type="primary"):
        with st.spinner(f"🎧 O modelo {modelo_escolhido} está processando o áudio... (Isso pode levar um minutinho)"):
            extensao = f".{arquivo_audio.name.split('.')[-1]}" 
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=extensao) as tmp_file:
                tmp_file.write(arquivo_audio.getvalue())
                tmp_file_path = tmp_file.name
            
            try:
                # 1. Upload do áudio para a API do Gemini
                arquivo_gemini = genai.upload_file(tmp_file_path)
                
                # 2. Prompt Inteligente
                prompt = """
                Ouça este arquivo de áudio com muita atenção.
                
                Por favor, atue em duas etapas:
                
                **ETAPA 1: TRANSCRIÇÃO**
                Forneça um resumo muito detalhado ou a transcrição dos pontos principais falados.
                
                **ETAPA 2: ATA DA REUNIÃO**
                Pule algumas linhas, adicione um divisor (---) e crie uma ata profissional contendo:
                1. **Resumo Geral:** Um parágrafo sobre o tema central.
                2. **Pontos Principais:** Lista com os principais assuntos discutidos.
                3. **Decisões Tomadas:** O que ficou efetivamente decidido.
                4. **Datas e Prazos:** Todas as datas, eventos futuros ou prazos mencionados, em destaque.
                """
                
                # Gera o conteúdo combinando o arquivo de áudio e o prompt
                resposta = modelo_gemini.generate_content([arquivo_gemini, prompt])
                
                st.success("✅ Processamento concluído com sucesso!")
                
                # Mostra o resultado na tela
                st.markdown(resposta.text)
                
                # 3. Limpeza do servidor do Google
                genai.delete_file(arquivo_gemini.name)
                
            except Exception as e:
                st.error(f"Erro ao processar o áudio com o modelo {modelo_escolhido}: {e}")
                st.info("Dica: Alguns modelos mais antigos na lista podem não suportar o envio de arquivos de áudio. Tente selecionar outro modelo na caixa acima.")
            finally:
                # Limpeza do arquivo temporário local
                if os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)
