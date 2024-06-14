import signal
import pygame
import subprocess
import socket
import threading
from pathlib import Path
from colorama import Fore, Style
from time import sleep
import os

def get_user():
    return f"CHATGPT {os.getenv('USER')}"

def get_host():
    return socket.gethostname()

def get_current_dir():
    return os.getcwd()

def get_git_branch():
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"],
            stderr=subprocess.STDOUT
        ).strip().decode('utf-8')
        if branch:
            return f"‹{branch}› "
        return ""
    except subprocess.CalledProcessError:
        return ""

def get_return_code():
    return_code = os.getenv('?', 0)
    return f"{return_code} ↵" if return_code != 0 else ""

def get_venv():
    venv = os.getenv("VIRTUAL_ENV")
    if venv:
        return f"‹{os.path.basename(venv)}› "
    return ""

def get_prompt():
    user_host = f"\033[1m\033[92m{get_user()}👽:\033[91m{get_host()}\033[0m"
    current_dir = f"📁:\033[1m\033[93m{get_current_dir()} \033[0m"
    vcs_branch = get_git_branch()
    venv_prompt = get_venv()
    return_code = get_return_code()
    user_symbol = "#" if os.geteuid() == 0 else "$"
    
    prompt = f"╭─{user_host}{current_dir}{venv_prompt}{vcs_branch}\n╰─\033[1m{user_symbol}\033[0m "
    rprompt = f"\033[1m{return_code}\033[0m"
    
    return prompt, rprompt

#Função Text to Speech
def tts(client, text):
    speech_file_path = Path(__file__).parent
    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="echo",
        input=text,
    ) as response:
        response.stream_to_file(f"{speech_file_path}/speech.mp3")
        
    pygame.mixer.music.load(f"{speech_file_path}/speech.mp3")
    pygame.mixer.music.play(loops=0, start=0.0)
    while pygame.mixer.music.get_busy():
        pygame.time.delay(100)
        
    os.remove(f"{speech_file_path}/speech.mp3")    


#Função para executar comandos no sistema operacional
def execute_command(command):
    # Inicia o processo com Popen
    if "cd ~" in command[0:4]:
        home_path = os.getenv('HOME')
        command = command.replace("~", home_path)
    if "cd " in command[0:3]:
        dpath = command[3:]
        os.chdir(dpath)
        cmdoutdec = subprocess.check_output("pwd", shell=True).decode()
    else:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    output_lines = []

    def read_output(stream, prefix=''):
        while True:
            line = stream.readline()
            if not line:
                break
            print(f"{prefix}{line.strip()}")
            output_lines.append(f"{prefix}{line.strip()}")

    stdout_thread = threading.Thread(target=read_output, args=(process.stdout,))
    stderr_thread = threading.Thread(target=read_output, args=(process.stderr, 'Erro: '))

    stdout_thread.start()
    stderr_thread.start()

    def signal_handler(sig, frame):
        print('Interrompido! Encerrando o comando...')
        process.terminate()

    signal.signal(signal.SIGINT, signal_handler)

    stdout_thread.join()
    stderr_thread.join()

    # Espera o processo terminar e retorna o código de saída
    process.wait()
    rc = process.returncode

    complete_output = "\n".join(output_lines)
    return complete_output, rc

#Função para criar lista de comandos
def transform_input_to_list(input_str):
    # Divida a string de entrada por vírgulas
    command_list = input_str.split(',')
    # Remova espaços em branco no início e no fim de cada comando
    command_list = [cmd.strip() for cmd in command_list]
    return command_list

# Função para buscar o assistente
def get_assistant(client, assistant_id):
    return client.beta.assistants.retrieve(assistant_id=assistant_id)

# Função para criar uma thread
def create_thread(client):
    return client.beta.threads.create()

# Função para adicionar mensagem à thread
def add_message_to_thread(client, thread_id, content):
    return client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=content
    )

# Função para criar e monitorar execução da thread
def create_and_poll_run(client, thread_id, assistant_id):
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions=""
    )

    while run.status != "completed":
        print(run.status)
        sleep(2)
        run = client.beta.threads.runs.retrieve(run.id)  # Atualiza o status da run

    return run

# Função para listar mensagens da thread
def list_thread_messages(client, thread_id):
    return client.beta.threads.messages.list(thread_id=thread_id)

# Função para fazer upload e monitoramento de arquivos
def upload_files(client, file_paths):
    file_streams = [open(path, "rb") for path in file_paths]

    vector_store = client.beta.vector_stores.create(name="Uploaded Files")

    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams
    )

    print(file_batch.status)
    print(file_batch.file_counts)

    return vector_store.id

#Função para consultar arquivos
def search_files(client, vector_store_id, query):
    search_result = client.beta.vector_stores.search(
        vector_store_id=vector_store_id,
        query=query
    )
    return search_result

#Estilização do input
def obter_input():
    """Obtém o input do usuário com destaque em amarelo."""
    print(f"{Fore.BLUE}{Style.BRIGHT}---{Style.RESET_ALL}")
    prompt, rprompt = get_prompt()
    print(prompt, end="")
    try:
        input_lines = []
        while True:
            line = input()
            input_lines.append(line)
    except EOFError:
        input_text = '\n'.join(input_lines)

    #input_text = input(f"{Fore.GREEN}{Style.BRIGHT}>>> ")
    print(f"{Fore.BLUE}{Style.BRIGHT}---{Style.RESET_ALL}")
    return input_text