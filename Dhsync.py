import socket
import getpass
import hmac
import hashlib
import os
import time
from utils.secret import convert_zip_send, send_file, receive_file
import subprocess, sys


def initiate_process(peer_ip, peer_port, secret_key):
    while True:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((peer_ip, peer_port))

            # Authenticate the peer
            authenticate, connection = authenticate_peer(client_socket, secret_key)
            if authenticate:
                print('Authenticated and connected to peer.\n')
                connection.send(b'Hello, bro!')
                done = convert_zip_send(connection)
                print('Authenticate Thank you for using the peer-to-peer process manager.')
                client_socket.close()
                break
            else:
                print('Authentication failed. Restarting process...')
                break
                  # Exit the loop to restart the process
        except Exception as e:
            print(f'An error occurred: {e}')

        finally:
            client_socket.close()


def authenticate_peer(connection, secret_key):
    print('Authenticating peer...')
    # Calculate and send the HMAC of the secret key
    message_hmac = hmac.new(secret_key, b'auth', hashlib.sha256).digest()
    connection.send(message_hmac)

    # Receive authentication response
    response = connection.recv(1024)
    print(response.decode())

    return response.decode() == 'Authentication successful', connection

def receive_process(secret_key, local_port=5000, timeout=30):
    status = True
    while status:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Enable reuse of the port
        server_socket.bind(('0.0.0.0', local_port))
        server_socket.listen(1)

        server_socket.settimeout(timeout)
        print('Waiting for connection...')

        start_time = time.time()
        connection = None

        try:
            while True:
                try:
                    connection, address = server_socket.accept()
                    print(f'Connected by {address}')
                    break  # Exit loop if a connection is established
                except socket.timeout:
                    if time.time() - start_time > timeout:
                        print("Connection timed out. No initiator connected.")
                        return

            if authenticate_connection(connection, secret_key):
                print('Peer authenticated.')
                hi_mssg = connection.recv(1024)
                print(hi_mssg.decode(), "\n")
                done = receive_file(connection)
                if done:
                    print('Thank you for using the peer-to-peer process manager. Hope to see you soon.')
                    connection.close()
                    server_socket.close()
                    break
            else:
                print('Authentication failed. Restarting process...')
                break
            status = False
        except Exception as e:
            print(f'An error occurred: {e}')




def authenticate_connection(connection, secret_key):
    # Receive the HMAC from the peer
    peer_hmac = connection.recv(1024)

    # Calculate HMAC on this side using the same key
    server_hmac = hmac.new(secret_key, b'auth', hashlib.sha256).digest()

    # Compare HMACs
    if hmac.compare_digest(server_hmac, peer_hmac):
        connection.send(b'Authentication successful')
        return True
    else:
        connection.send(b'Authentication failed')
        return False
    
def install_requirements():
    try:
        # Attempt to install the packages listed in requirements.txt
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("All required packages are installed.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while installing the packages: {e}")
        sys.exit(1)  # Exit if there is an error installing the packages

def main():
    print("Welcome to the peer-to-peer process manager.\n")
    print("Ensuring Packages are installed required packages are installed. \n")
    install_requirements()
    print("Packages are installed. \n")

    ini = False
    rec = False

    while True:
        choice = input("Do you want to initiate (i) or receive (r) a process? (i/r): ").strip().lower()
        if choice == 'i':
            peer_ip = input("Enter the IP address of the peer: ").strip()
            peer_port = int(input("Enter the port of the peer: ").strip())
            # peer_ip_hard = '192.168.1.104' #"192.168.1.179" #192.168.1.104
            # peer_ip = peer_ip_hard.strip()
            peer_port_hard = 8080
            peer_port = peer_port_hard
            secret_key = getpass.getpass("Enter the secret key: ").strip().encode()
            ini = initiate_process(peer_ip, peer_port, secret_key)
            break
        elif choice == 'r':
            # local_port = int(input("Enter the port to listen on: ").strip())
            local_port_hard = 8080
            local_port = local_port_hard
            secret_key_r = getpass.getpass("Enter the secret key: ").strip().encode()
            rec = receive_process(secret_key_r, local_port)
            break
        else:
            print("Invalid choice. Please enter 'i' to initiate or 'r' to receive.")



if __name__ == "__main__":
    main()