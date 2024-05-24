"""
Assistente desktop com Gemini
"""

import subprocess
import platform
import json
import signal
import os
from colorama import Fore, Style
import google.generativeai as genai
from rich.markdown import Markdown
from rich.console import Console

def obter_input():                                                                                                                                                                  
    """Obtém o input do usuário com destaque em amarelo."""
    print(f"{Fore.BLUE}{Style.BRIGHT}---")
    input_text = input(f"{Fore.GREEN}{Style.BRIGHT}>>> ")
    print(f"{Fore.BLUE}{Style.BRIGHT}---{Style.RESET_ALL}")
    return input_text

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

def send_command_to_gemini(chat_session, command):
    """Envia um comando ao Gemini e retorna a resposta."""
    prompt = create_getcmd_json(command)
    response = chat_session.send_message(prompt)
    return response

def execute_local_command(command):
    """Executa um comando local e retorna a saída."""
    try:
        if "cd " in command[0:3]:
            dpath = command[3:]
            os.chdir(dpath)
            cmdoutdec = subprocess.check_output("pwd", shell=True).decode()
        else:
            cmdoutput = subprocess.check_output(command, shell=True)
            cmdoutdec = cmdoutput.decode()
        return cmdoutdec
    except Exception as erro:
        return f"Erro: {erro}\nNada Enviado"

def handle_user_input(chat_session):
    """Processa a entrada do usuário e interage com o Gemini."""
    while True:
        try:
            quest = obter_input()
            if quest == "$:exit":
                confirmacao = input("Tem certeza que deseja sair? (s/n): ")
                if confirmacao.lower() == 's':
                    print('Saindo...')
                    break

                continue

            if "cmd:" in quest[0:4]:
                response = send_command_to_gemini(chat_session, quest)
                iareturn = response.text
                print(f"COMANDO RETORNADO: {iareturn}")
                cmd = response.text.replace("\n", "").replace("`", "").replace("```", "").replace("cmd:", "").strip()
                cmdoutdec = execute_local_command(cmd)
                if cmdoutdec == "":
                    print("Saida do comando vazia, nada enviado")
                    continue
                response = chat_session.send_message(create_localcmd_json(cmd, cmdoutdec))
                print(cmdoutdec)
                continue

            if "/:" in quest[0:2]:
                cmd = quest.replace("/:", "").strip()
                cmdoutdec = execute_local_command(cmd)
                response = chat_session.send_message(create_localcmd_json(cmd, cmdoutdec))
                print(cmdoutdec)
                continue

            cmd = create_default_json(quest)
            print(type(cmd))
            print(quest)
            response = chat_session.send_message(cmd)
            md = Markdown(response.text)
            console = Console()
            console.print(md)
        except Exception as erro:
            print(f"Erro: {erro}\nNada Enviado")
            continue

def signal_handler(sig, frame):
    """Sai com classe ao utilizar CTRL + C"""
    print(f"Para sair digite {Fore.RED}{Style.BRIGHT}$:exit{Style.RESET_ALL}")

signal.signal(signal.SIGINT, signal_handler)

with open('apikey', 'r') as f:
    api_key = f.read().strip()
apikey = api_key #str(input("API KEY: "))

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
  history=[]
)

handle_user_input(chat_session)