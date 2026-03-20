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

modelo_gemini = genai.GenerativeModel('gemini-1.5-flash')

# --- Interface da Página ---
st.set_page_config(page_title="Gerador de Atas", page_icon="🎙️", layout="wide")
st.title("🎙️ Super Gerador de Atas com Gemini")
st.markdown("Faça o upload do áudio. O sistema fará a transcrição e gerará a ata automaticamente.")

arquivo_audio = st.file_uploader("Carregue o áudio (MP3, WAV, M4A, AAC)", type=['mp3', 'wav', 'm4a', 'aac'])

if arquivo_audio is not None:
    st.audio(arquivo_audio)
    
    if st.button("Processar Reunião", type="primary"):
        with st.spinner("🎧 O Gemini está ouvindo o áudio e preparando a ata... (Isso pode levar um minutinho)"):
            extensao = f".{arquivo_audio.name.split('.')[-1]}" 
            
            # Salva o arquivo temporariamente no servidor do Streamlit
            with tempfile.NamedTemporaryFile(delete=False, suffix=extensao) as tmp_file:
                tmp_file.write(arquivo_audio.getvalue())
                tmp_file_path = tmp_file.name
            
            try:
                # 1. Upload do áudio direto para a API do Gemini
                arquivo_gemini = genai.upload_file(tmp_file_path)
                
                # 2. Prompt pedindo a Transcrição E a Ata ao mesmo tempo
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
                
                # O Gemini analisa o áudio e o texto juntos!
                resposta = modelo_gemini.generate_content([arquivo_gemini, prompt])
                
                st.success("✅ Processamento concluído com sucesso!")
                
                # Mostra o resultado na tela
                st.markdown(resposta.text)
                
                # 3. Limpeza: Apaga o arquivo do servidor do Google para proteger a privacidade
                genai.delete_file(arquivo_gemini.name)
                
            except Exception as e:
                st.error(f"Erro ao processar o áudio: {e}")
            finally:
                # Limpeza: Apaga o arquivo temporário do Streamlit
                if os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)
