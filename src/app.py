import uuid
import streamlit as st
from helper import extract_data_analysis, read_uploaded_file
from database import AnalyzeDatabase
from ai import GroqClient
from models.resum import Resum
from models.file import File

# Inicializando o banco de dados e o cliente AI
database = AnalyzeDatabase()
ai = GroqClient()

# Permitir o upload de múltiplos arquivos PDF
uploaded_files = st.file_uploader("Carregue seus currículos", type=["pdf"], accept_multiple_files=True)

# Campo para a descrição da vaga
job_description = st.text_area("Descrição da Vaga", placeholder="Insira aqui a descrição da vaga...")

# Verifica se currículos foram carregados e se a descrição da vaga foi fornecida
if uploaded_files and job_description:
    # Valida a descrição da vaga
    st.spinner("Validando a descrição da vaga...")
    
    with st.spinner("Aguarde, validando..."):
        job_validation = ai.validate_job_description(job_description)

    if job_validation == "Descrição de vaga inválida":
        st.warning("⚠️ Descrição de vaga inválida. Por favor, insira uma descrição válida.")
    else:
        # Exibe o total de currículos encontrados
        num_curriculos = len(uploaded_files)
        st.write(f"Total de currículos encontrados: {num_curriculos}")

        # Botão para continuar
        if st.button("Continuar"):
            for uploaded_file in uploaded_files:
                # Lê o conteúdo do arquivo PDF carregado
                content = read_uploaded_file(uploaded_file)

                # Gera resumo, opinião e score do currículo
                with st.spinner(f"Aguarde, analisando curriculo {uploaded_file.name}..."):
                    resum = ai.resume_cv(content)
                    opinion = ai.generate_opinion(content, job_description)
                    score = ai.generate_score(content, job_description)

                # Salva os dados processados no banco de dados
                resum_schema = Resum(
                    id=str(uuid.uuid4()),
                    job_id=job_description,  # Caso você tenha um ID de trabalho correspondente
                    content=resum,
                    file=uploaded_file.name,
                    opinion=opinion
                )

                file_schema = File(
                    file_id=str(uuid.uuid4()),
                    job_id=job_description  # Caso você tenha um ID de trabalho correspondente
                )

                analyzis_schema = extract_data_analysis(resum, job_description, resum_schema.id, score)

                database.resums.insert(resum_schema.model_dump())
                database.analysis.insert(analyzis_schema.model_dump())
                database.files.insert(file_schema.model_dump())

                # Exibe as análises
                st.subheader(f"Análise do Currículo: {uploaded_file.name}")
                st.write("### Resumo:")
                st.markdown(resum)
                st.write("### Opinião Crítica:")
                st.markdown(opinion)
                st.write("### Pontuação:")
                st.write(f"Pontuação Final: {score}")
else:
    # Mensagem de aviso caso não haja arquivos ou descrição
    st.warning("⚠️ Nenhum currículo carregado ou descrição da vaga fornecida.")
