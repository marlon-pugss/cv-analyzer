import re
import os  # Importado para carregar a chave de API
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import json  # Importando json para manipulação de dados

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
            self.client = ChatGroq(model=model_id, api_key=self.api_key)  # Passar a chave de API aqui
        except Exception as e:
            print(f"Erro ao inicializar o cliente Groq: {e}")
            raise

    def generate_response(self, prompt):
        # Enviar o prompt ao modelo e obter a resposta
        response = self.client.invoke(prompt)
        return response.content

    def resume_cv(self, cv):
        # Criar o prompt para gerar um resumo do currículo em Markdown
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
        
        # Gerar a resposta usando o modelo de linguagem
        result_raw = self.generate_response(prompt=prompt)
        
        # Tentar extrair o conteúdo após o marcador ```markdown
        try:
            result = result_raw.split('```markdown')[1]
        except:
            # Se não conseguir, retornar a resposta bruta
            result = result_raw
        return result

    def generate_score(self, cv, job, max_attempts=10):
        # Criar o prompt para calcular a pontuação do currículo com base na vaga
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
            
            **Atenção:** Seja rigoroso ao atribuir as notas. A nota máxima é 10.0, e o output deve conter apenas "Pontuação Final: x.x".
        '''
        
        # Tentar gerar a pontuação em múltiplas tentativas, caso necessário
        for attempt in range(max_attempts):
            # Gerar a resposta usando o modelo de linguagem
            result_raw = self.generate_response(prompt=prompt)
            
            # Extrair a pontuação da resposta gerada
            score = self.extract_score_from_result(result_raw)
        
            # Se a pontuação foi extraída com sucesso, retornar a pontuação
            if score is not None:
                return score
            
            # Se falhar, exibir mensagem de erro e tentar novamente
            print(f"Tentativa {attempt + 1} falhou. Tentando novamente...")
        
        # Lançar um erro se não conseguir gerar a pontuação após várias tentativas
        raise ValueError("Não foi possível gerar a pontuação após várias tentativas.")

    def extract_score_from_result(self, result_raw):
        """Extrair a pontuação final da resposta gerada."""
        # Definir o padrão de regex para buscar a pontuação na resposta
        pattern = r"(?i)Pontuação Final[:\s]*([\d,.]+(?:/\d{1,2})?)"
        
        # Procurar pela pontuação na resposta
        match = re.search(pattern, result_raw)
        
        if match:
            # Se encontrado, extrair o valor da pontuação
            score_str = match.group(1)
            print(f"Valor de score_str: '{score_str}'")
            
            if '/' in score_str:
                score_str = score_str.split('/')[0]
            
            # Garantir que o valor é numérico e válido
            score_str = score_str.strip()  # Remove espaços extras
            
            # Verifica se score_str é vazio ou contém apenas um ponto ou vírgula
            if score_str in ["", ".", ","]:
                print("Pontuação inválida encontrada. Retornando None.")
                return None  # Retorna None se for um valor inválido
            
            # Retornar a pontuação como um número float
            return float(score_str.replace(',', '.'))

        # Retornar None se não encontrar a pontuação
        return None

    def generate_opinion(self, cv, job):
        """
        Gera uma análise crítica do currículo em relação à descrição da vaga.

        Args:
            cv (str): O currículo do candidato.
            job (str): A descrição da vaga.

        Returns:
            str: A análise crítica formatada.
        """
        
        # Verificar se cv e job não estão vazios
        if not cv or not job:
            raise ValueError("O currículo e a descrição da vaga não podem ser vazios.")
        
        # Criar o prompt para gerar uma opinião crítica sobre o currículo
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
            # Gerar a resposta usando o modelo de linguagem
            result_raw = self.generate_response(prompt=prompt)
            return result_raw
        except Exception as e:
            # Tratar erros durante a chamada do modelo
            print(f"Erro ao gerar opinião: {e}")
            return "Erro ao gerar a análise. Tente novamente mais tarde."

    def extract_candidate_summary(self, cv):
        """
        Extrai um resumo breve das informações do candidato.

        Args:
            cv (str): O currículo do candidato.

        Returns:
            dict: Um dicionário com as informações do candidato.
        """
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

            **Atenção:** Não inclua explicações, apenas forneça as informações extraídas no formato JSON especificado acima.
        '''

        try:
            # Gerar a resposta usando o modelo de linguagem
            result_raw = self.generate_response(prompt=prompt)
            # Retornar a resposta processada
            return json.loads(result_raw)
        except json.JSONDecodeError:
            print("Erro ao decodificar o JSON da resposta.")
            return None  # Retornar None se a resposta não puder ser decodificada
        except Exception as e:
            print(f"Erro ao extrair informações do candidato: {e}")
            return None

    def test_connection(self):
        try:
            response = self.client.invoke("Teste de conexão")
            print("Conexão bem-sucedida:", response)
        except Exception as e:
            print("Falha na conexão:", e)

# Exemplo de uso:
if __name__ == "__main__":
    client = GroqClient()
    # Aqui você pode testar outros métodos conforme necessário
