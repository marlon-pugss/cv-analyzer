import re
import uuid
import os
from PyPDF2 import PdfReader  # Usando PyPDF2 para leitura de PDFs
from models.analysis import Analysis

def read_uploaded_file(uploaded_file):
    # Lê o conteúdo do arquivo PDF carregado diretamente do objeto UploadedFile
    text = ""
    reader = PdfReader(uploaded_file)  # Use o UploadedFile diretamente
    for page in reader.pages:
        text += page.extract_text()  # Extrai o texto de cada página
    return text

def extract_data_analysis(resum_cv, job_id, resum_id, score) -> Analysis:
    """Extrai informações do currículo e retorna um objeto Analysis."""
    # Dicionário inicial para armazenar as seções extraídas
    secoes_dict = {
        "id": str(uuid.uuid4()),  # Gera um UUID único para a análise
        "job_id": job_id,
        "resum_id": resum_id,
        "name": "",
        "skills": [],
        "education": [],
        "languages": [],
        "score": score
    }

    # Padrões regex para capturar as diferentes seções do resumo do currículo
    patterns = {
        "name": r"(?:## Nome Completo\s*|Nome Completo\s*\|\s*Valor\s*\|\s*\S*\s*\|\s*)(.*)",
        "skills": r"## Habilidades\s*([\s\S]*?)(?=##|$)",
        "education": r"## Educação\s*([\s\S]*?)(?=##|$)",
        "languages": r"## Idiomas\s*([\s\S]*?)(?=##|$)",
        "salary_expectation": r"## Pretensão Salarial\s*([\s\S]*?)(?=##|$)"
    }

    def clean_string(string: str) -> str:
        """Remove caracteres indesejados e espaços extras de uma string."""
        return re.sub(r"[\*\-]+", "", string).strip()

    # Loop para buscar e extrair as informações com base nos padrões definidos
    for secao, pattern in patterns.items():
        match = re.search(pattern, resum_cv)
        if match:
            if secao == "name":
                secoes_dict[secao] = clean_string(match.group(1))
            else:
                # Quebra o conteúdo da seção em linhas e limpa cada linha
                secoes_dict[secao] = [clean_string(item) for item in match.group(1).split('\n') if item.strip()]

    # Validação para garantir que seções obrigatórias não estejam vazias
    for key in ["name", "education", "skills"]:
        if not secoes_dict[key] or (isinstance(secoes_dict[key], list) and not any(secoes_dict[key])):
            # Em vez de lançar uma exceção, você pode registrar um aviso e definir um valor padrão
            print(f"A seção '{key}' não pode ser vazia ou uma string vazia. Definindo valor padrão.")
            secoes_dict[key] = "N/A"  # Ou outro valor padrão que você achar apropriado

    # Retorna um objeto Analysis com os dados extraídos
    return Analysis(**secoes_dict)

def get_pdf_paths(directory):
    """Obtém todos os caminhos de arquivos PDF no diretório especificado."""
    pdf_files = []

    for filename in os.listdir(directory):
        if filename.endswith('.pdf'):
            file_path = os.path.join(directory, filename)
            pdf_files.append(file_path)

    return pdf_files
