import streamlit as st
import tempfile
import os
from openai import OpenAI
import google.generativeai as genai

# --- Configuração das APIs ---
# O Streamlit Cloud puxa essas chaves dos "Secrets" que vamos configurar depois
try:
    client_openai = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("⚠️ Chaves de API não encontradas! Configure os Secrets no painel do Streamlit.")
    st.stop()

# Configuração do modelo Gemini
modelo_gemini = genai.GenerativeModel('gemini-1.5-flash')

# --- Interface da Página ---
st.set_page_config(page_title="Gerador de Atas", page_icon="🎙️", layout="wide")
st.title("🎙️ Transcrição e Gerador de Atas Automático")
st.markdown("Faça o upload do áudio para transcrever e gerar a ata estruturada.")

# --- Upload de Áudio ---
arquivo_audio = st.file_uploader("Carregue o áudio (MP3, WAV, M4A)", type=['mp3', 'wav', 'm4a'])

if arquivo_audio is not None:
    st.audio(arquivo_audio)
    
    if st.button("Processar Reunião", type="primary"):
        texto_bruto = ""
        
        # 1. ETAPA DE TRANSCRIÇÃO (Whisper)
        with st.spinner("🎧 Transcrevendo o áudio... (Isso pode levar alguns minutos)"):
            extensao = f".{arquivo_audio.name.split('.')[-1]}" 
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=extensao) as tmp_file:
                tmp_file.write(arquivo_audio.getvalue())
                tmp_file_path = tmp_file.name
            
            try:
                with open(tmp_file_path, "rb") as audio_file:
                    transcricao = client_openai.audio.transcriptions.create(
                        model="whisper-1", 
                        file=audio_file,
                        language="pt"
                    )
                texto_bruto = transcricao.text
                st.success("✅ Transcrição concluída!")
                
                with st.expander("Ver transcrição completa"):
                    st.write(texto_bruto)
                    
            except Exception as e:
                st.error(f"Erro na transcrição: {e}")
                st.stop()
            finally:
                if os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)
                    
        # 2. ETAPA DE GERAÇÃO DA ATA (Gemini)
        if texto_bruto:
            with st.spinner("🧠 Analisando texto e gerando a ata estruturada..."):
                prompt = f"""
                Você é um assistente executivo especialista em criar atas claras e objetivas.
                Leia a transcrição abaixo e crie uma ata profissional contendo:
                
                1. **Resumo Geral:** Um parágrafo sobre o tema central da conversa.
                2. **Pontos Principais:** Lista com os principais assuntos discutidos.
                3. **Decisões Tomadas:** O que ficou efetivamente decidido.
                4. **Datas e Prazos Agendados:** Se houver menção a datas, eventos futuros ou prazos, liste-os de forma destacada.
                
                Transcrição da reunião:
                {texto_bruto}
                """
                
                try:
                    resposta = modelo_gemini.generate_content(prompt)
                    st.divider()
                    st.subheader("📋 Ata da Reunião")
                    st.markdown(resposta.text)
                except Exception as e:
                    st.error(f"Erro ao gerar a ata: {e}")
