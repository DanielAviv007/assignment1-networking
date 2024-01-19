import argparse
import socket


# Function to parse and return command line arguments
def get_parsed_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("serverIP", type=str, help="server ip address")
    parser.add_argument("serverPort", type=int, help="server port number")
    return parser.parse_args()


class Client:
    RECV_BUFFER_SIZE = 1_024

    def __init__(self, server_ip: str, server_port: int) -> None:
        self.__server_address: tuple[str, int] = server_ip, server_port
        self.__socket: socket.socket = None

    def run(self) -> None:
        # Initializing the client socket
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while True:
            # Prompting user for input
            url = input()
            request_bytes = url.encode()
            # Sending user input (url) to the server as a request
            self.__socket.sendto(request_bytes, self.__server_address)
            # Waiting to receive the server's response (ip)
            response_bytes, _ = self.__socket.recvfrom(Client.RECV_BUFFER_SIZE)
            # Server's response is in the format "<url>,<ip>"
            # Extracting IP from the response
            _, ip = response_bytes.decode().split(",")
            # Printing the received IP
            print(ip, end="")


def main() -> None:
    # Parsing command line arguments and initializing the server
    args = get_parsed_arguments()
    client = Client(args.serverIP, args.serverPort)
    client.run()


if __name__ == "__main__":
    main()
