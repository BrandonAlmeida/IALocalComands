#!/bin/python3
from openai import OpenAI
import subprocess
import os
from rich.markdown import Markdown
from rich.console import Console
from colorama import Fore, Style
import sys
import pygame
from utils import get_assistant, create_thread, obter_input, add_message_to_thread, create_and_poll_run, list_thread_messages, transform_input_to_list, execute_command, upload_files, search_files, tts

wrkpath = os.getcwd()


# Main function
def main():
    
    audio = 0
    #Coleta ID do Assitente e APIKEY
    try:
        with open(f"{wrkpath}/ChatGpt/config", "r", encoding="utf-8") as file:
            lines = file.readlines()
            apikey = lines[0].strip()
            assistant_id = lines[1].strip()
    except Exception as err:
        print(f"Arquivo de configuração não encontrado, erro: {err}")
        apikey = str(input("Informe sua APIKEY: "))
        assistant_id = str(input("Informe o ID do ASSISTENTE: "))

    # Configuração do cliente OpenAI
    client = OpenAI(api_key=apikey)
    
    assistant = get_assistant(client, assistant_id)
    thread = create_thread(client)
    vector_store_id = None  # Inicialize como None

    while True:

        quest = obter_input()
        if "audio()" in quest[0:8]:
            if audio == 0:
                audio = 1
                pygame.mixer.init()
                print("Retorno de voz ligado.")
            else:
                audio = 0
                print("Retorno de voz desligado.")
            continue
        
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
                    if audio == 1:
                        tts(client, chat_return)
                        
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
            if audio == 1:
                tts(client, chat_return)

if __name__ == "__main__":
    main()
