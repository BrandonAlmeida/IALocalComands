import subprocess
import os
from time import sleep
from openai import OpenAI
from rich.markdown import Markdown
from rich.console import Console
from colorama import Fore, Style
import threading
import sys
import signal
wrkpath = os.getcwd()

#Coleta ID do Assitente e APIKEY
with open(f"{wrkpath}/ChatGpt/config", "r", encoding="utf-8") as file:
    lines = file.readlines()
    apikey = lines[0].strip()
    assistant_id = lines[1].strip()

# Configuração do cliente OpenAI
client = OpenAI(api_key=apikey)

def execute_command(command):
    # Inicia o processo com Popen
    if "cd " in command[0:3]:
        dpath = command[3:]
        os.chdir(dpath)
        cmdoutdec = subprocess.check_output("pwd", shell=True).decode()

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
    print(f"{Fore.BLUE}{Style.BRIGHT}---")
    print(f"{Fore.GREEN}{Style.BRIGHT}>>> ", end="")
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

# Main function
def main():
    assistant = get_assistant(client, assistant_id)
    thread = create_thread(client)
    vector_store_id = None  # Inicialize como None

    while True:
        quest = obter_input()
        if "exit()" in quest[0:7]:
            sys.exit()
        if "cmd:" in quest[0:4]:
            try:
                #Envia a requisição
                add_message_to_thread(client, thread.id, quest)
                run = create_and_poll_run(client, thread.id, assistant.id)
                
                #Recebe o retorno da IA
                messages = list_thread_messages(client, thread.id)
                chat_return = messages.data[0].content[0].text.value
                print(f"{Fore.BLUE}{Style.BRIGHT}COMANDO RETORNADO:{Style.RESET_ALL} {Fore.YELLOW}{Style.BRIGHT}{chat_return}{Style.RESET_ALL}")
                
                #Transforma o retorno em uma lista
                commands = transform_input_to_list(chat_return)
                
                #Executa os comandos na lista
                for command  in commands:
                    cmd_output, return_code = execute_command(command)
                    #cmd_output = execute_command(command)                    
                    #Envia o output do comando
                    if cmd_output:
                        add_message_to_thread(client, thread.id, cmd_output)
                    run = create_and_poll_run(client, thread.id, assistant.id)
                    messages = list_thread_messages(client, thread.id)
                    chat_return = messages.data[0].content[0].text.value
                    mdformat = Markdown(chat_return)
                    console = Console()
                    console.print(mdformat)
                    
            except subprocess.CalledProcessError as error:
                err = f"Falha na execução do comando, erro: {error}"
                add_message_to_thread(client, thread.id, err)
                run = create_and_poll_run(client, thread.id, assistant.id)
                continue
            except Exception as error:
                err = f"Erro inesperado: {error}"
                add_message_to_thread(client, thread.id, err)
                run = create_and_poll_run(client, thread.id, assistant.id)
                continue
            
            continue
        if "upload:" in quest[0:7]:
            try:
                file_paths = quest.split("upload:",1)[1].strip().split()
                vector_store_id = upload_files(client, file_paths)
                assistant = client.beta.assistants.update(
                    assistant_id=assistant.id,
                    tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
                )
                print("Uploaded")
                continue
            except Exception as error:
                err = f"Falha no upload dos arquivos, erro: {error}"
                add_message_to_thread(client, thread.id, err)
                run = create_and_poll_run(client, thread.id, assistant.id)
                continue
        
        if vector_store_id and "search:" in quest[0:7]:
            try:
                query = quest.split("search:", 1)[1].strip()
                search_result = search_files(client, vector_store_id, query)
                print(search_result)
                continue
            except Exception as error:
                err = f"Falha na busca, erro: {error}"
                add_message_to_thread(client, thread.id, err)
                run = create_and_poll_run(client, thread.id, assistant.id)
                continue
        
        add_message_to_thread(client, thread.id, quest)
        run = create_and_poll_run(client, thread.id, assistant.id)
        messages = list_thread_messages(client, thread.id)
        if messages.data:
            chat_return = messages.data[0].content[0].text.value
            mdformat = Markdown(chat_return)
            console = Console()
            console.print(mdformat)

if __name__ == "__main__":
    main()
