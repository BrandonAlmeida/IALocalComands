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
import signal
import json

def create_getcmd_json(content):
  """Cria um JSON para solicitar um comando ao Gemini."""
  data = {
    "type": "getcmd",
    "cmd": "",
    "content": content
  }
  return json.dumps(data)  

def create_localcmd_json(cmd, content):
  """Cria um JSON para enviar o resultado de um comando local."""
  data = {
    "type": "localcmd",
    "cmd": cmd,
    "content": content 
  }
  return json.dumps(data)

def create_default_json(content):
  """Cria um JSON para mensagens padrão."""
  data = {
    "type": "default",
    "cmd": "",
    "content": content
  }
  return json.dumps(data)

def signal_handler(sig, frame):                                                                                                                      
    print('Saindo...')                                                                                                                               
    exit(0)                                                                                                                                          
                                                                                                                                                     
signal.signal(signal.SIGINT, signal_handler)

apikey = str(input("API KEY: "))
sysop = platform.system()
genai.configure(api_key=apikey)

# Create the model
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
  system_instruction=f"""Você é um agente projetado para auxiliar na execução de comandos em um sistema {sysop}. Você receberá instruções em formato JSON.

- Mensagens do tipo "getcmd" solicitam um comando a ser executado. 
- Mensagens do tipo "localcmd" informam o resultado da execução do último comando. 
- Mensagens do tipo "default"  são mensagens informativas. 

Ao receber uma mensagem "getcmd", analise o conteúdo e responda com o comando a ser executado. 

Ao receber uma mensagem "localcmd", analise o conteúdo, que representa a saída do comando, e utilize-o para futuras interações. 

Ao receber uma mensagem "default", responda normalmente.

Responda apenas com o comando solicitado ou com a análise da saída.
""",
)

chat_session = model.start_chat(
  history=[
    {
      "role": "user",
      "parts": [
        create_getcmd_json("listar arquivos da pasta atual"),
      ],
    },
    {
      "role": "model",
      "parts": [
        "ls \n",
      ],
    },
    {
      "role": "user",
      "parts": [
        create_localcmd_json("ls", "drwxr-xr-x  3 user user 4096 mai 17 08:38 Desktop\ndrwxr-xr-x 16 user user 4096 mai 20 14:14 Documents\ndrwxr-xr-x  8 user user 4096 mai 23 08:13 Downloads\ndrwxrwxr-x  5 user user 4096 mai 23 08:08 GitHub\ndrwxr-xr-x  2 user user 4096 mai 17 10:33 Music\ndrwxrwxr-x  4 user user 4096 jan  8 12:34"),
      ],
    },
    {
      "role": "model",
      "parts": [
        "Output recebido",
      ],
    },
  ]
)

while True:
    try:
        quest = str(input(">>> "))
        if quest == "$:exit":                                                                                                                        
            confirmacao = input("Tem certeza que deseja sair? (s/n): ")                                                                              
            if confirmacao.lower() == 's':                                                                                                           
                print('Saindo...')                                                                                                                   
                break
            else:
                continue
        #response = chat_session.send_message(create_default_json(quest))
        if("cmd:" in quest[0:4]):
            prompt = create_getcmd_json(quest)
            response = chat_session.send_message(prompt)
            iareturn = response.text
            print(f"COMANDO RETORNADO: {iareturn}")
            cmd = response.text.replace("\n", "")
            cmd = cmd.replace("`", "")
            cmd = cmd.replace("```", "")
            cmd = cmd.replace("cmd:", "").strip()
            cmdoutput = subprocess.check_output(cmd, shell=True)
            cmdoutdec = cmdoutput.decode()
            
            if cmdoutdec == "":
                print("Saida do comando vazia, nada enviado")
                continue
            
            response = chat_session.send_message(
                create_localcmd_json(cmd, cmdoutdec)
            )
            print(cmdoutdec)
            md = Markdown(response.text)
            console = Console()
            console.print(md)
            continue
        
        if ("/:" in quest[0:2]):
            cmd = quest.replace("/:", "")
            cmd = cmd.strip()
            cmdoutput = subprocess.check_output(cmd, shell=True)
            cmdoutdec = cmdoutput.decode()
            prompt = create_localcmd_json(cmd, cmdoutdec)
            
            response = chat_session.send_message(prompt)

            print(cmdoutdec)
            md = Markdown(response.text)
            console = Console()
            console.print(md)
            continue

        prompt = create_default_json(quest)
        response = chat_session.send_message(prompt)
        md = Markdown(response.text)
        console = Console()
        console.print(md)
    except Exception as erro:
        print(f"Erro: {erro}\nNada Enviado")
        continue