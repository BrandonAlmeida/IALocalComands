#!/bin/python3
import subprocess
from colorama import Fore, Style
import sys
import pygame
from utils import obter_input, add_message_to_thread, create_and_poll_run, transform_input_to_list, execute_command, upload_files, search_files, tts, get_chatinfo, send_msg, output_md

# Main function
def main():

    #vector_store_id = None  # Inicialize como None
    audio = 0
    #Coleta ID do Assitente e APIKEY
    client, thread, assistant = get_chatinfo()

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
                chat_return = send_msg(client, thread.id, assistant.id, quest)
                print(f"{Fore.BLUE}{Style.BRIGHT}COMANDO RETORNADO:{Style.RESET_ALL} {Fore.YELLOW}{Style.BRIGHT}{chat_return}{Style.RESET_ALL}")
                
                #Transforma o retorno em uma lista
                commands = transform_input_to_list(chat_return)
                
                #Executa os comandos na lista
                for command in commands:
                    cmd_output, return_code = execute_command(command)
                    #cmd_output = execute_command(command)                    
                    #Envia o output do comando
                    if cmd_output:
                        chat_return = send_msg(client, thread.id, assistant.id, cmd_output)
                        output_md(chat_return)
                    
                    if audio == 1:
                        tts(client, chat_return)
                        
            except subprocess.CalledProcessError as error:
                err = f"Falha na execução do comando, erro: {error}"
                chat_return = send_msg(client, thread.id, assistant.id, err)
                output_md(chat_return)
                continue
            
            except Exception as error:
                err = f"Falha na execução do comando, erro: {error}"
                chat_return = send_msg(client, thread.id, assistant.id, err)
                output_md(chat_return)
                continue
            
            continue
        
        chat_return = send_msg(client, thread.id, assistant.id, quest)
        if chat_return:
            output_md(chat_return)
            if audio == 1:
                tts(client, chat_return)        
"""
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
 """       


if __name__ == "__main__":
    main()
