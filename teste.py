import psutil
import socket  # Para acessar os valores das famílias de endereço

# Obtém informações das interfaces de rede
interfaces = psutil.net_if_addrs()

for interface, addrs in interfaces.items():
    print(f"Interface: {interface}")
    if interface == 'Wi-FI':
        for addr in addrs:
            if addr.family == socket.AF_LINK:  # Endereço MAC
                print(f"  MAC Address: {addr.address}")
            elif addr.family == socket.AF_INET:  # Endereço IPv4
                print(f"  IPv4 Address: {addr.address}")
                print(f"  Netmask: {addr.netmask}")
                print(f"  Broadcast: {addr.broadcast}")
            elif addr.family == socket.AF_INET6:  # Endereço IPv6
                print(f"  IPv6 Address: {addr.address}")
