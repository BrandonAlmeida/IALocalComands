import subprocess
import os
from time import sleep
from openai import OpenAI
from rich.markdown import Markdown
from rich.console import Console
from colorama import Fore, Style

wrkpath = os.getcwd()

# Configuração do cliente OpenAI

#Coleta ID do Assitente e APIKEY
with open(f"{wrkpath}/ChatGpt/config", "r", encoding="utf-8") as file:
    lines = file.readlines()
    apikey = lines[0].strip()
    assistant_id = lines[1].strip()

client = OpenAI(api_key=apikey)

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
    input_text = input(f"{Fore.GREEN}{Style.BRIGHT}>>> ")
    print(f"{Fore.BLUE}{Style.BRIGHT}---{Style.RESET_ALL}")
    return input_text

# Main function
def main():
    assistant = get_assistant(client, assistant_id)
    thread = create_thread(client)
    vector_store_id = None  # Inicialize como None

    while True:
        quest = obter_input()
        if "cmd:" in quest[0:4]:
            try:
                add_message_to_thread(client, thread.id, quest)
                run = create_and_poll_run(client, thread.id, assistant.id)
                messages = list_thread_messages(client, thread.id)
                chat_return = messages.data[0].content[0].text.value
                cmd_output = subprocess.check_output(chat_return, shell=True)
                cmd_output = cmd_output.decode()
                print(cmd_output)
                add_message_to_thread(client, thread.id, cmd_output)
                run = create_and_poll_run(client, thread.id, assistant.id)
                continue
            except Exception as error:
                err = f"Falha na execução do comando, erro: {error}"
                add_message_to_thread(client, thread.id, err)
                run = create_and_poll_run(client, thread.id, assistant.id)
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
