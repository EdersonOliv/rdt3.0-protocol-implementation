import math
import socket  # Cria sockets par comunicação em uma rede
import struct  # Biblioteca que Interpreta bytes como dados binários compactados

import constants as const
from checksum import find_checksum
from create_packet import create_packet


class Server:
    def __init__(self):
        self.SERVER_ADRR = (socket.gethostbyname(socket.gethostname()), const.SERVER_PORT)
        self.sever_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sever_socket.bind(self.SERVER_ADRR)
        self.clients_ip = None
        print("-----------------------------------------------------------------")
        print(f"Servidor rodando no endereço [ip: {self.SERVER_ADRR[0]}, port: {self.SERVER_ADRR[1]}]...")

    def received(self):
        seq_num = 0
        received_list = []
        print("-----------------------------------------------------------------")
        while True:
            self.sever_socket.settimeout(None)
            packet_received, client_adrr = self.sever_socket.recvfrom(const.BUFF_SIZE)
            # Caso o pacote contenha conteúdo
            if len(packet_received) > const.HEADER_SIZE:
                header = packet_received[:const.HEADER_SIZE]  # Separando o Header
                packet_received = packet_received[const.HEADER_SIZE:]  # Separando os dados
                seq_num_received, checksum = struct.unpack("!II", header)  # Desempacotando o header
                # Gerando checksum do lado do receptor (servidor neste caso)
                header_no_checksum = struct.pack("!I", seq_num_received)
                packet_no_checksum = header_no_checksum + packet_received
                checksum_check = find_checksum(packet_no_checksum)
                # Normalizando o checksum para comparação
                checksum = bin(checksum)[2:]
                checksum = "0" * (len(checksum_check) - len(checksum)) + checksum
                # Convertendo a sequência de bytes dos dados recebidos em uma string
                decoded_packet = packet_received.decode(encoding="ISO-8859-1")
                # Fazendo a verificação do numero de sequencia e checksum
                if seq_num_received != seq_num:
                    print("Detectado pacote duplicado!")
                    message = create_packet(seq_num, None, 1)
                    self.sever_socket.sendto(message, client_adrr)
                elif checksum != checksum_check:
                    print("Detectado pacote corrompido!")
                    print("Aguardando reenvio do pacote...")
                # Caso o pacote esteja correto
                else:
                    received_list.append(decoded_packet)
                    message = create_packet(seq_num, None, 1)
                    self.sever_socket.sendto(message, client_adrr)
                    if seq_num == 0:
                        seq_num = 1
                    else:
                        seq_num = 0
            # Caso seja um pacote de reconhecimento (confirmação que todos os pacotes foram recebidos)
            else:
                print("Mensagem recebida!")
                print(f"Total de pacotes recebidos({len(received_list)})")
                content = "".join(received_list)  # Juntando os fragmentos
                print("Processando mensagem...")
                modified_message = content.upper()
                print("Processamento concluído!")
                break

        print("Retornando mensagem modificada ao cliente...")
        self.send(modified_message, client_adrr)

    def send(self, data, client_adrr):
        # Variáveis de controle de envio e recebimento dos dados
        seq_num = 0  # Número de sequência de envio do pacote
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
                # Enviando pacote para o cliente e aguardando resposta
                self.sever_socket.settimeout(const.TIMEOUT)
                self.sever_socket.sendto(packet, client_adrr)
                try:
                    _ = self.sever_socket.recv(const.BUFF_SIZE)
                # Se o tempo de espera acabar, enviar novamente
                except TimeoutError:
                    print("Tempo de envio do pacote excedeu o tempo limite!")
                    print("Reenviando pacote...")
                    packet_sent = False
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
                print("Envio concluído!")
                message = create_packet(seq_num, None, 1)
                self.sever_socket.sendto(message, client_adrr)
                break

        # Aguardando por novas mensagens
        self.received()


def main():
    server = Server()
    server.received()


if __name__ == "__main__":
    main()
