"""
Install the Google AI Python SDK

$ pip install google-generativeai

See the getting started guide for more information:
https://ai.google.dev/gemini-api/docs/get-started/python
"""
import subprocess
import platform
import google.generativeai as genai
from rich.markdown import Markdown
from rich.console import Console

apikey = str(input("API KEY: "))
sysop = platform.system()
print(sysop, type(sysop))
genai.configure(api_key=apikey)

# Create the model
# See https://ai.google.dev/api/python/google/generativeai/GenerativeModel
generation_config = {
  "temperature": 0,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}
safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_NONE",
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_NONE",
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_NONE",
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_NONE",
  },
]

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash-latest",
  safety_settings=safety_settings,
  generation_config=generation_config,
  system_instruction=f"Utilizarei esse prompt para a execução de comando locais na minha maquina {sysop}.\nSempre que uma request começar com 'cmd:' me retorne apenas o comando CLI  para a execução da atividade informada. \nSempre que uma request começar com 'Output:' essa será a saida do comando enviado anteriormente, responda apenas com 'Output recebido'.",
)

chat_session = model.start_chat(
  history=[
  ]
)
while True:
    try:
        quest = str(input(">>> "))
        response = chat_session.send_message(quest) 
        
        if("cmd:" in quest[0:4]):
            cmd = response.text.replace("\n", "")
            cmd = cmd.replace("`", "").strip()
            saida = subprocess.check_output(cmd, shell=True)
            
            if saida.decode() == "":
                print("Saida do comando vazia, nada enviado")
                continue
            
            saida = f"Output:\n{saida.decode()}"
            print(saida)
            response = chat_session.send_message(saida)
            md = Markdown(response.text)
            console = Console()
            console.print(md)
            continue  	
        md = Markdown(response.text)
        console = Console()
        console.print(md)
    except Exception as erro:
        print(f"Erro: {erro}\nNada Enviado")
        continue
    