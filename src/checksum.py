# Função para encontrar o Checksum dos pacotes
def find_checksum(data):
    data_bits = bin(int.from_bytes(data))[2:]  # Converte os dados em uma representação binária de bits
    sum_checksum = bin(sum(map(ord, data_bits)))[2:]  # Calcula a soma binária dos bits
    slice_length = 8
    # Adiciona bits em caso de overflow
    if len(sum_checksum) > slice_length:
        x = len(sum_checksum) - slice_length
        sum_checksum = bin(int(sum_checksum[:x], 2) + int(sum_checksum[x:], 2))[2:]
    # Preenche com zeros à esquerda se necessário
    if len(sum_checksum) < slice_length:
        sum_checksum = "0" * (slice_length - len(sum_checksum)) + sum_checksum
    # Calcula o complemento da soma
    return str(sum_checksum)


# Teste de checksum
if __name__ == "__main__":
    print(find_checksum("0".encode()))
