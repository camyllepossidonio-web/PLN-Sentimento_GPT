"""
MIT License

Copyright (c) 2026 AI & Python Software Architecture

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import json
import streamlit as st
from openai import AzureOpenAI

# ==============================================================================
# CONFIGURAÇÃO DE SEGURANÇA E AMBIENTE (LOCAL VS PRODUCTION)
# ==============================================================================
# Para configurar localmente, crie um arquivo na pasta do seu projeto em:
# .streamlit/secrets.toml
#
# Adicione as seguintes chaves no secrets.toml:
# [azure_openai]
# api_key = "6t2pTNsmNafDyo53MDAFIrvvQRBZXP7dLcr5j3TLxMS34LQVq3ZUJQQJ99CHACHYHv6XJ3w3AAAAACOGT7os"
# endpoint = "https://marcelomaffeis-05082026-resource.services.ai.azure.com/"
# deployment_name = "gpt-4.1-mini"
# api_version = "2024-02-15-preview"
# ==============================================================================

# Definições Padrão (Fallback com os dados do Microsoft Foundry fornecidos)
AZURE_API_KEY = st.secrets.get("azure_openai", {}).get(
    "api_key",
    "6t2pTNsmNafDyo53MDAFIrvvQRBZXP7dLcr5j3TLxMS34LQVq3ZUJQQJ99CHACHYHv6XJ3w3AAAAACOGT7os"
)
AZURE_ENDPOINT = st.secrets.get("azure_openai", {}).get(
    "endpoint",
    "https://marcelomaffeis-05082026-resource.services.ai.azure.com/"
).replace("&quot;", "").strip()

AZURE_DEPLOYMENT = st.secrets.get("azure_openai", {}).get(
    "deployment_name",
    "gpt-4.1-mini"
)
AZURE_API_VERSION = st.secrets.get("azure_openai", {}).get(
    "api_version",
    "2024-02-15-preview"
)

# Configuração da Página do Streamlit
st.set_page_config(
    page_title="Extrator Inteligente de Dados - Azure AI",
    page_icon="🧠",
    layout="wide"
)

# Inicialização do Cliente Azure OpenAI
@st.cache_resource
def get_azure_client():
    return AzureOpenAI(
        azure_endpoint=AZURE_ENDPOINT,
        api_key=AZURE_API_KEY,
        api_version=AZURE_API_VERSION
    )

try:
    client = get_azure_client()
except Exception as e:
    st.error(f"Erro ao inicializar o cliente Azure OpenAI: {e}")
    st.stop()

# ==============================================================================
# INTERFACE DO USUÁRIO
# ==============================================================================

st.title("🧠 Extrator Inteligente de Dados")
st.caption("Solução Enterprise utilizando Microsoft Azure OpenAI & Streamlit")

st.markdown("""
Esta aplicação analisa textos em linguagem natural para extrair informações estruturadas automaticamente 
(análise de sentimento com pontuação, tópico principal, entidades mencionadas e nível de urgência).
""")

# Campo de Entrada
user_text = st.text_area(
    "Digite ou cole o texto para análise:",
    height=180,
    placeholder="Exemplo: Falei hoje com a Dra. Ana e o Carlos sobre o atraso crítico na entrega do relatório financeiro. Estamos muito preocupados com os impactos no prazo do projeto."
)

if st.button("🚀 Processar Texto", type="primary", use_container_width=True):
    if not user_text.strip():
        st.warning("Por favor, insira um texto válido antes de processar.")
    else:
        with st.spinner("Analisando dados via Azure OpenAI..."):
            # System Prompt para forçar a saída JSON exata requerida
            system_prompt = """
            Você é um assistente especialista em extração e estruturação de dados.
            Sua tarefa é analisar o texto do usuário e retornar EXCLUSIVAMENTE um objeto JSON válido.
            Não inclua marcações markdown (como ```json) adicionais se puder evitar, retorne apenas a estrutura raw JSON.

            O JSON DEVE conter estritamente as seguintes chaves:
            1. 'sentimento': texto curto descrevendo o sentimento geral (ex: Positivo, Negativo, Neutro, Preocupado, Urgente).
            2. 'porcentagem_sentimento': número entre 0 e 100 indicando a intensidade/confiança do sentimento identificado.
            3. 'assunto_principal': resumo resumido do tópico central do texto.
            4. 'pessoas_citadas': array/lista com os nomes de todas as pessoas ou entidades nomeadas citadas no texto (se houver nenhuma, retorne uma lista vazia []).
            5. 'nivel_de_urgencia': apenas um destes três valores exatos: 'Baixo', 'Medio' ou 'Alto'.
            """

            try:
                response = client.chat.completions.create(
                    model=AZURE_DEPLOYMENT,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_text}
                    ],
                    temperature=0.1
                )

                raw_content = response.choices[0].message.content
                data = json.loads(raw_content)

                st.success("Análise concluída com sucesso!")
                st.subheader("📊 Resultados da Extração")

                # Exibição de Métricas
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    sentimento = data.get("sentimento", "N/A")
                    porcentagem = data.get("porcentagem_sentimento", 0)
                    st.metric(
                        label="Sentimento Identificado", 
                        value=str(sentimento), 
                        delta=f"{porcentagem}% intensidade"
                    )

                with col2:
                    urgencia = data.get("nivel_de_urgencia", "N/A")
                    st.metric(label="Nível de Urgência", value=str(urgencia))

                with col3:
                    pessoas = data.get("pessoas_citadas", [])
                    qtd_pessoas = len(pessoas) if isinstance(pessoas, list) else 0
                    st.metric(label="Pessoas Citadas", value=f"{qtd_pessoas} encontrada(s)")

                st.markdown("---")

                # Detalhamento em Colunas
                col_left, col_right = st.columns(2)

                with col_left:
                    st.markdown("### 📌 Assunto Principal")
                    st.info(data.get("assunto_principal", "Não identificado."))

                    st.markdown("### 👤 Pessoas / Entidades Identificadas")
                    if pessoas and isinstance(pessoas, list):
                        for p in pessoas:
                            st.write(f"- **{p}**")
                    else:
                        st.write("_Nenhuma pessoa citada no texto._")

                with col_right:
                    st.markdown("### 📄 JSON Retornado pela API")
                    st.json(data)

            except Exception as e:
                st.error(f"Ocorreu um erro ao processar a requisição no Azure OpenAI: {e}")

# ==============================================================================
# INSTRUÇÕES DE CONFIGURAÇÃO (SIDERBAR)
# ==============================================================================
with st.sidebar:
    st.header("⚙️ Configuração do Ambiente")
    st.markdown("""
    Para rodar este app localmente utilizando boas práticas de segurança:
    
    1. Crie a pasta **`.streamlit/`** na raiz do projeto.
    2. Crie o arquivo **`secrets.toml`** dentro dela.
    3. Cole o seguinte formato:
    """)
    
    st.code("""
[azure_openai]
api_key = "SUA_CHAVE_AQUI"
endpoint = "SEU_ENDPOINT_AQUI"
deployment_name = "gpt-4.1-mini"
api_version = "2024-02-15-preview"
    """, language="toml")
    
    st.info("O arquivo `.streamlit/secrets.toml` não deve ser enviado para o repositório Git.")
