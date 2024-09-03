import struct  # Biblioteca que Interpreta bytes como dados binários compactados

import constants as const
from checksum import find_checksum


def create_packet(seq_num, data=None, isACK=None):
    # Se for um pacote de reconhecimento
    if isACK:
        fragment = struct.pack("!II", seq_num, isACK)  # Pacote completo
    # Se for um pacote contendo dados
    else:
        # Criando estrutura de dados do tipo bytearray
        data = str(data).encode()
        data_bytes = bytearray()
        data_bytes.extend(data)
        # Gerando checksum
        header_no_checksum = struct.pack("!I", seq_num)
        packet_no_checksum = header_no_checksum + bytearray(data_bytes)
        checksum = find_checksum(packet_no_checksum)
        checksum = int(checksum, 2)
        # Montando pacote completo (com checksum)
        header = struct.pack("!II", seq_num, checksum)
        fragment = header + bytearray(data)

    return fragment


# Testes de empacotamento
if __name__ == "__main__":
    frag_test1 = create_packet(0, "fragment teste")
    print(frag_test1)
    header = frag_test1[:const.HEADER_SIZE]
    print(header)
    seq_num, checksum = struct.unpack("!II", header)
    print(seq_num)
    print(checksum)
    message_received_bytes = frag_test1[const.HEADER_SIZE:]
    print(message_received_bytes)
