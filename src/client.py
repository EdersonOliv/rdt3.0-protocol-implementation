import math
import random
import socket
import struct
import tkinter as tk
from tkinter import messagebox, ttk

import constants as const
from checksum import find_checksum
from create_packet import create_packet


class App(tk.Tk):
    def __init__(self):
        # Configurações da janela
        tk.Tk.__init__(self)
        tk.Tk.title(self, "Defina o endereço do servidor")
        tk.Tk.columnconfigure(self, 0, weight=1)
        tk.Tk.rowconfigure(self, 0, weight=1)
        tk.Tk.resizable(self, False, False)
        # Criando socket UDP
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Atribuindo uma porta aleatória entre 1000 e 9998 para o cliente
        self.CLIENT_PORT = random.randint(1000, 9998)
        self.client_socket.bind(("", self.CLIENT_PORT))
        # Definindo servidor
        self.SERVER_ADRR = ("", 0)
        self.find_server()

    def header(self):
        tk.Tk.title(self, "RDT3.0 Implementation")
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        header_frame.columnconfigure(0, weight=1)
        header_frame.rowconfigure(0, weight=1)
        tk.Label(header_frame, text="Endereço: ").grid(
            row=0, column=0, padx=5, pady=1, sticky=tk.W
        )
        tk.Label(header_frame, text="Porta: ").grid(
            row=1, column=0, padx=5, pady=1, sticky=tk.W
        )
        tk.Label(header_frame, text=self.SERVER_ADRR[0]).grid(
            row=0, column=1, padx=5, pady=1, sticky=tk.W
        )
        tk.Label(header_frame, text=self.SERVER_ADRR[1]).grid(
            row=1, column=1, padx=5, pady=1, sticky=tk.W
        )

    def body(self):
        # Frame do log
        view_frame = ttk.Frame(self)
        view_frame.grid(row=1, column=0, padx=2, pady=2, sticky=tk.EW)
        view_frame.columnconfigure(0, weight=1)
        view_frame.rowconfigure(0, weight=1)
        his = tk.Text(view_frame, height=15, width=40, cursor="arrow")
        his.grid(row=0, column=0, columnspan=3, padx=2, pady=2)
        his.config(state=tk.DISABLED)
        sbar = tk.Scrollbar(view_frame, command=his.yview)
        sbar.grid(row=0, column=4)
        his.config(yscrollcommand=sbar.set)
        # Frame de entrada e envio
        send_frame = ttk.Frame(self)
        send_frame.grid(row=2, column=0, padx=0, pady=5, sticky=tk.W)
        send_frame.columnconfigure(0, weight=1)
        send_frame.rowconfigure(0, weight=1)
        tk.Label(send_frame, text="Entrada:").grid(
            row=0, column=0, padx=5, pady=2, sticky=tk.W
        )
        msg = tk.Text(send_frame, height=4, width=30)
        msg.focus_set()
        msg.grid(row=1, column=0, columnspan=3, rowspan=3, padx=5, pady=2)
        msg.focus_set()
        ttk.Button(send_frame, text="Enviar", command=lambda: message(msg, his, 0)).grid(
            column=3, row=1
        )
        ttk.Button(send_frame, text="Corromper", command=lambda: message(msg, his, 1)).grid(
            column=3, row=2
        )
        ttk.Button(send_frame, text="Duplicar", command=lambda: message(msg, his, 2)).grid(
            column=3, row=3
        )

        def message(msg, his, choice):
            data = msg.get("1.0", "end-1c")
            msg.delete("1.0", tk.END)
            msg.focus_set()
            if data == "":
                messagebox.showwarning("Atenção", "Campo vazio!")
            else:
                his.config(state=tk.NORMAL)
                his.insert(tk.END, f"Você digitou: {data}\n")
                his.config(state=tk.DISABLED)

                modified_message = self.send(data, choice)

                his.config(state=tk.NORMAL)
                his.insert(tk.END, f"Servidor retornou: {modified_message}\n")
                his.insert(tk.END, "---------------------------------------\n")
                his.config(state=tk.DISABLED)

    def send(self, data, choice):
        # Variáveis de controle de envio e recebimento dos dados
        seq_num = 0  # Número de sequência envio do pacote
        packet_sent = True  # Controle do status de envio do pacote
        # Codificando o conteúdo e definindo as configurações de empacotamento
        contents = data
        packet_size = const.FRAG_SIZE
        packet_index = 0
        packet_count = math.ceil(len(contents) / packet_size)  # Quantidade total de pacotes
        # Enviando os pacotes
        while True:
            if packet_index < packet_count:
                # Preparando um pacote de tamanho packet_size
                packet = contents[:packet_size]
                packet = create_packet(seq_num, packet)
                # Teste de corrupção de pacote
                if choice == 1:
                    data = str(contents[:packet_size]).encode()
                    data_bytes = bytearray()
                    data_bytes.extend(data)
                    checksum = int("00000000", 2)  # Gerando checksum invalido
                    header = struct.pack("!II", seq_num, checksum)  # Header compactado com checksum
                    packet = header + bytearray(data)  # Pacote completo (com checksum invalido)
                    choice = 0
                # Enviando pacote para o servidor e aguardando resposta
                self.client_socket.settimeout(const.TIMEOUT)
                self.client_socket.sendto(packet, self.SERVER_ADRR)
                try:
                    response = self.client_socket.recv(const.BUFF_SIZE)
                    received_seq_num, _ = struct.unpack("!II", response)
                    if received_seq_num != seq_num:
                        pass
                # Se o tempo de espera acabar, enviar novamente
                except TimeoutError:
                    print("Tempo de envio do pacote excedeu o tempo limite!")
                    print("Reenviando pacote...")
                    packet_sent = False
                # Teste de duplicação de pacote
                if choice == 2:
                    packet_sent = False
                    choice = 0
                # Em caso de resposta positiva, definir o novo pacote a ser enviado
                if packet_sent:
                    contents = contents[packet_size:]  # Remove o pacote enviado do conteúdo
                    packet_index += 1  # Incrementa o índice do pacote
                    if seq_num == 0:
                        seq_num = 1
                    else:
                        seq_num = 0
                # Reestabelece status 'True' para fazer nova conferência
                packet_sent = True
            # Se todos os pacotes foram enviados
            else:
                message = create_packet(seq_num, None, 1)
                self.client_socket.settimeout(const.TIMEOUT)
                self.client_socket.sendto(message, self.SERVER_ADRR)
                break
        # Recebendo resultado do servidor
        modified_message = self.received()
        return modified_message

    def received(self):
        seq_num = 0
        received_list = []
        while True:
            self.client_socket.settimeout(None)
            packet_received = self.client_socket.recv(const.BUFF_SIZE)
            # Caso o pacote contenha conteúdo
            if len(packet_received) > const.HEADER_SIZE:
                header = packet_received[:const.HEADER_SIZE]  # Separando o Header
                packet_received = packet_received[const.HEADER_SIZE:]  # Separando os dados
                seq_num_received, checksum = struct.unpack("!II", header)  # Desempacotando o header
                # Gerando checksum do lado do receptor (cliente neste caso)
                header_no_checksum = struct.pack('!I', seq_num_received)
                packet_no_checksum = (header_no_checksum + packet_received)
                checksum_check = find_checksum(packet_no_checksum)
                # Normalizando o checksum para comparação
                checksum = bin(checksum)[2:]
                checksum = "0" * (len(checksum_check) - len(checksum)) + checksum
                # Converte a sequência de bytes da mensagem recebida em uma string
                decoded_packet = packet_received.decode(encoding="ISO-8859-1")
                # Fazendo a verificação do numero de sequencia e checksum
                if seq_num_received != seq_num:
                    print("Detectado pacote duplicado!")
                    message = create_packet(seq_num, None, 1)
                    self.client_socket.sendto(message, self.SERVER_ADRR)
                elif checksum != checksum_check:
                    print("Detectado pacote corrompido!")
                    print("Aguardando reenvio do pacote...")
                # Caso o pacote esteja correto
                else:
                    received_list.append(decoded_packet)
                    message = create_packet(seq_num, None, 1)
                    self.client_socket.sendto(message, self.SERVER_ADRR)
                    if seq_num == 0:
                        seq_num = 1
                    else:
                        seq_num = 0
            else:
                content = "".join(received_list)  # Juntando os pacotes
                return content

    def find_server(self):
        initial_frame = ttk.Frame(self)
        initial_frame.grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        initial_frame.columnconfigure(0, weight=1)
        initial_frame.rowconfigure(0, weight=1)
        tk.Label(initial_frame, text="Endereço: ").grid(row=0, column=0, padx=5, pady=1, sticky=tk.W)
        tk.Label(initial_frame, text="Porta: ").grid(row=1, column=0, padx=5, pady=1, sticky=tk.W)
        adrr = tk.Text(initial_frame, height=1, width=30)
        adrr.grid(row=0, column=1, padx=5, pady=1, sticky=tk.W)
        adrr.focus_set()
        tk.Label(initial_frame, text=f"{const.SERVER_PORT}").grid(row=1, column=1, padx=5, pady=1, sticky=tk.W)
        # Botão para conectar ao servidor
        entrar = ttk.Button(initial_frame, text="Entrar", command=lambda: self.to_enter(initial_frame, adrr))
        entrar.grid(row=2, column=0, columnspan=2, padx=5, pady=2)

    def to_enter(self, frame, adrr):
        ip = adrr.get("1.0", "end-1c")
        if (ip == ""):
            messagebox.showwarning("Atenção", "Endereço invalido!")
        else:
            # Define o endereço do servidor
            self.SERVER_ADRR = (ip, const.SERVER_PORT)
            frame.destroy()
            # Frames principais
            self.header()
            self.body()


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
