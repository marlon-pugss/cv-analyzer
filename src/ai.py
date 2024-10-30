import re
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import json

# Carregar as variáveis de ambiente do arquivo .env
load_dotenv()
class GroqClient:
    def __init__(self, model_id="llama-3.1-70b-versatile"):
        # Carregar a chave de API do ambiente
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("A chave de API não foi encontrada no arquivo .env.")

        # Inicializar o modelo de linguagem com o ID especificado
        self.model_id = model_id
        try:
            self.client = ChatGroq(model=model_id, api_key=self.api_key)
        except Exception as e:
            print(f"Erro ao inicializar o cliente Groq: {e}")
            raise

    def generate_response(self, prompt):
        # Enviar o prompt ao modelo e obter a resposta
        response = self.client.invoke(prompt)
        return response.content

    def validate_job_description(self, job_text):
        """
        Verifica se o texto fornecido é uma descrição de vaga válida.

        Args:
            job_text (str): O texto para verificar.

        Returns:
            str: Retorna o texto da vaga se for uma descrição válida,
                 caso contrário, retorna "Descrição de vaga inválida".
        """
        prompt = f'''
            Por favor, analise o texto abaixo e determine se ele representa uma descrição válida de vaga de emprego.
            
            **Texto da vaga para análise:**
            {job_text}

            Responda apenas com "Descrição de vaga válida" se o texto realmente for uma descrição de vaga.
            Se o texto não corresponder a uma descrição de vaga de emprego, responda com "Descrição de vaga inválida".
        '''

        # Enviar o prompt ao modelo e receber a resposta
        response = self.generate_response(prompt=prompt).strip()

        # Verificar a resposta e retornar o texto apropriado
        return job_text if response == "Descrição de vaga válida" else "Descrição de vaga inválida"

    def resume_cv(self, cv):
        prompt = f'''
            **Solicitação de Resumo de Currículo em Markdown:**
            
            # Curriculo do candidato para resumir:
            
            {cv}

            Por favor, gere um resumo do currículo fornecido, formatado em Markdown, seguindo rigorosamente o modelo abaixo. **Não adicione seções extras, tabelas ou qualquer outro tipo de formatação diferente da especificada.** Preencha cada seção com as informações relevantes, garantindo que o resumo seja preciso e focado.

            **Formato de Output Esperado:**

            ```markdown
            ## Nome Completo
            nome_completo aqui

            ## Experiência
            experiencia aqui

            ## Habilidades 
            habilidades aqui

            ## Educação 
            educacao aqui

            ## Idiomas 
            idiomas aqui
            '''
        
        result_raw = self.generate_response(prompt=prompt)
        
        try:
            result = result_raw.split('```markdown')[1]
        except:
            result = result_raw
        return result

    def generate_score(self, cv, job, max_attempts=10):
        prompt = f'''
            **Objetivo:** Avaliar um currículo com base em uma vaga específica e calcular a pontuação final. A nota máxima é 10.0.

            **Instruções:**

            1. **Experiência (Peso: 30%)**: Avalie a relevância da experiência em relação à vaga.
            2. **Habilidades Técnicas (Peso: 25%)**: Verifique o alinhamento das habilidades técnicas com os requisitos da vaga.
            3. **Educação (Peso: 10%)**: Avalie a relevância da formação acadêmica para a vaga.
            4. **Idiomas (Peso: 10%)**: Avalie os idiomas e sua proficiência em relação à vaga.
            5. **Pontos Fortes (Peso: 15%)**: Avalie a relevância dos pontos fortes para a vaga.
            6. **Pontos Fracos (Desconto de até 10%)**: Avalie a gravidade dos pontos fracos em relação à vaga.
            
            Curriculo do candidato
            
            {cv}
            
            Vaga que o candidato está se candidatando
            
            {job}

            **Output Esperado:**
            ```
            Pontuação Final: x.x
            ```
        '''
        
        for attempt in range(max_attempts):
            result_raw = self.generate_response(prompt=prompt)
            score = self.extract_score_from_result(result_raw)
            if score is not None:
                return score
            print(f"Tentativa {attempt + 1} falhou. Tentando novamente...")
        
        raise ValueError("Não foi possível gerar a pontuação após várias tentativas.")

    def extract_score_from_result(self, result_raw):
        pattern = r"(?i)Pontuação Final[:\s]*([\d,.]+(?:/\d{1,2})?)"
        match = re.search(pattern, result_raw)
        
        if match:
            score_str = match.group(1)
            if '/' in score_str:
                score_str = score_str.split('/')[0]
            score_str = score_str.strip()
            if score_str in ["", ".", ","]:
                return None
            return float(score_str.replace(',', '.'))
        return None

    def generate_opinion(self, cv, job):
        if not cv or not job:
            raise ValueError("O currículo e a descrição da vaga não podem ser vazios.")
        
        prompt = f'''
            Por favor, analise o currículo fornecido em relação à descrição da vaga aplicada e crie uma opinião ultra crítica e detalhada. A sua análise deve incluir os seguintes pontos:
            Você deve pensar como o recrutador chefe que está analisando e gerando uma opinião descritiva sobre o currículo do candidato que se candidatou para a vaga.
            
            Formate a resposta de forma profissional, coloque títulos grandes nas seções.

            1. **Pontos de Alinhamento**: Identifique e discuta os aspectos do currículo que estão diretamente alinhados com os requisitos da vaga. Inclua exemplos específicos de experiências, habilidades ou qualificações que correspondem ao que a vaga está procurando.

            2. **Pontos de Desalinhamento**: Destaque e discuta as áreas onde o candidato não atende aos requisitos da vaga. Isso pode incluir falta de experiência em áreas-chave, ausência de habilidades técnicas específicas, ou qualificações que não correspondem às expectativas da vaga.

            3. **Pontos de Atenção**: Identifique e discuta características do currículo que merecem atenção especial. Isso pode incluir aspectos como a frequência com que o candidato troca de emprego, lacunas no histórico de trabalho, ou características pessoais que podem influenciar o desempenho no cargo, tanto de maneira positiva quanto negativa.

            Sua análise deve ser objetiva, baseada em evidências apresentadas no currículo e na descrição da vaga. Seja detalhado e forneça uma avaliação honesta dos pontos fortes e fracos do candidato em relação à vaga.

            **Currículo Original:**
            {cv}

            **Descrição da Vaga:**
            {job}
            
            Você deve devolver essa análise crítica formatada como se fosse um relatório analítico do currículo com a vaga, e deve estar formatado com títulos grandes em destaque.
        '''

        try:
            result_raw = self.generate_response(prompt=prompt)
            return result_raw
        except Exception as e:
            print(f"Erro ao gerar opinião: {e}")
            return "Erro ao gerar a análise. Tente novamente mais tarde."

    def extract_candidate_summary(self, cv):
        prompt = f'''
            **Solicitação de Extração de Informações do Candidato:**

            Por favor, analise o seguinte currículo e extraia as seguintes informações:
            - Nome
            - Email
            - Telefone
            - Localização

            **Currículo do Candidato:**
            {cv}

            **Formato do Output:**
            ```json
            {{
                "Nome": "nome do candidato",
                "Email": "email do candidato",
                "Telefone": "telefone do candidato",
                "Localização": "localização do candidato"
            }}
            ```
        '''
        try:
            result_raw = self.generate_response(prompt=prompt)
            return json.loads(result_raw)
        except json.JSONDecodeError:
            print("Erro ao decodificar o JSON da resposta.")
            return None
        except Exception as e:
            print(f"Erro ao extrair informações do candidato: {e}")
            return None

    def classify_score(self, score):
        if score < 7:
            return "A pontuação está abaixo do ideal. Considere revisar o currículo para destacar suas experiências e habilidades. Cada detalhe conta!"
        elif 7 <= score < 9:
            return "Bom trabalho! Sua pontuação é aceitável, mas há espaço para melhorias. Revise seu currículo e veja onde pode destacar ainda mais suas experiências e habilidades."
        else:
            return "Excelente! Sua pontuação é impressionante. Você está no caminho certo e deve continuar assim. Boa sorte na sua busca pela vaga!"

    def test_connection(self):
        try:
            response = self.client.invoke("Teste de conexão")
            print("Conexão bem-sucedida:", response)
        except Exception as e:
            print("Falha na conexão:", e)
