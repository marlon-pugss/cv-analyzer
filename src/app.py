import streamlit as st
from client import GroqClient

# Inicializar o cliente Groq
client = GroqClient()

st.title("Analisador de Currículos")

# Inputs do usuário
cv = st.text_area("Insira o currículo do candidato:", height=300)
job_description = st.text_area("Insira a descrição da vaga:", height=300)

# Botão para prosseguir com a análise
if st.button("Analisar Currículo"):
    if cv and job_description:
        # Gerar resumo do CV
        resume = client.resume_cv(cv)
        st.subheader("Resumo do Currículo:")
        st.markdown(resume)

        # Gerar pontuação
        score = client.generate_score(cv, job_description)
        st.subheader("Pontuação do Currículo:")
        st.write(f"Pontuação: {score:.2f}")

        # Gerar opinião crítica
        opinion = client.generate_opinion(cv, job_description)
        st.subheader("Opinião Crítica:")
        st.markdown(opinion)

        # Extrair informações do candidato
        candidate_info = client.extract_candidate_summary(cv)
        st.subheader("Informações do Candidato:")
        st.json(candidate_info)
    else:
        st.warning("Por favor, insira tanto o currículo quanto a descrição da vaga.")

