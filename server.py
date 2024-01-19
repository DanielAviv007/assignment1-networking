import argparse
import socket


# Function to read and return lines from a specified file
def read_file_lines(file_path: str) -> list[str]:
    with open(file_path, "r") as file:
        return file.readlines()


# Function to write a list of strings to a specified file
def write_lines_to_file(file_path: str, lines: list[str]) -> None:
    with open(file_path, "w") as file:
        file.writelines(lines)


# Function to parse and return command line arguments
def get_parsed_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("myPort", type=int, help="server port number")
    parser.add_argument("parentIP", type=str, help="parent server ip address")
    parser.add_argument("parentPort", type=int, help="parent server port number")
    parser.add_argument("ipsFileName", type=str, help="url-to-ip map file path")
    return parser.parse_args()


class Server:
    RECV_BUFFER_SIZE = 1_024

    def __init__(self, server_port: int, parent_ip: str, parent_port: int, ips_file_name: str) -> None:
        self.__server_port: int = server_port
        self.__parent_address: tuple[str, int] = parent_ip, parent_port
        self.__ips_file_name: str = ips_file_name
        # Dictionary mapping URLs to their IP addresses, loaded from a file
        self.__url_to_ip: dict[str, str] = self.__load_url_to_ip_map()
        # Dictionary mapping URLs to a list of pending client addresses
        self.__url_to_pending_clients: dict[str, list[tuple[str, int]]] = dict()
        # Socket for the server
        self.__socket: socket.socket = None

    def run(self) -> None:
        # Initializing the server socket
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Binding the socket to the server's port
        self.__socket.bind(("", self.__server_port))
        while True:
            payload_bytes, address = self.__socket.recvfrom(Server.RECV_BUFFER_SIZE)
            payload = payload_bytes.decode()
            if address == self.__parent_address:  # Handling parent server response "<url>,<ip>"
                self.__handle_parent_response(payload)
            else:  # Handling requests from clients "<url>"
                self.__handle_client_request(payload, address)

    # Function to load URL to IP mappings from a file into a dictionary
    def __load_url_to_ip_map(self) -> dict[str, str]:
        map_lines = read_file_lines(self.__ips_file_name)
        return {url: ip for url, ip in [map_line.split(",") for map_line in map_lines]}

    # Function to save the current URL to IP map to a file
    def __store_url_to_ip_map(self) -> None:
        map_lines = [f"{url},{ip}" for url, ip in self.__url_to_ip.items()]
        write_lines_to_file(self.__ips_file_name, map_lines)

    # Function to add a new URL to IP mapping both to the dictionary and the file
    def __add_url_to_ip_map_entry(self, url: str, ip: str) -> None:
        self.__url_to_ip[url] = ip
        self.__store_url_to_ip_map()

    def __handle_parent_response(self, parent_response: str) -> None:
        # Extracting URL and IP from the parent's response
        url, ip = parent_response.split(",")
        self.__add_url_to_ip_map_entry(url, ip)  # Adding the new mapping
        response_bytes = f"{url},{ip}".encode()  # Encoding the response for transmission
        # Sending the IP to all pending clients that requested this URL
        for client_address in self.__url_to_pending_clients.get(url, []):
            self.__socket.sendto(response_bytes, client_address)
        # Clearing the URL from the list of pending clients
        del self.__url_to_pending_clients[url]

    def __handle_client_request(self, url: str, client_address: tuple[str, int]) -> None:
        # Responding to client requests for URLs
        if url in self.__url_to_ip:  # If the IP for the URL is already known
            ip = self.__url_to_ip[url]
            response_bytes = f"{url},{ip}".encode()
            self.__socket.sendto(response_bytes, client_address)
        else:  # If the IP for the URL is not known
            pending_clients = self.__url_to_pending_clients.get(url, [])
            if not pending_clients:  # If this is the first request for this URL
                # Ask parent server
                request_bytes = url.encode()
                self.__socket.sendto(request_bytes, self.__parent_address)
            # Recording the client's address for sending the IP once it's known
            pending_clients.append(client_address)
            self.__url_to_pending_clients[url] = pending_clients


def main() -> None:
    # Parsing command line arguments and initializing the server
    args = get_parsed_arguments()
    server = Server(args.myPort, args.parentIP, args.parentPort, args.ipsFileName)
    server.run()


if __name__ == "__main__":
    main()
