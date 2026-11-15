# sender.py
import socket
from crc_module import encode_data

def ask_int(prompt):
    """Keep asking until the user types a whole number."""
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("  Please enter a whole number.")


def ask_yes_no(prompt):
    """Keep asking until the user answers yes or no. Returns True for yes."""
    while True:
        choice = input(prompt).strip().lower()
        if choice in ["yes", "y"]:
            return True
        if choice in ["no", "n"]:
            return False
        print("  Please type y or n.")


def collect_input():        # ask the user, return area, nominees list, eligible
    nominee_list = []
    area_code = input("Area Code: ")

    while True:
        nominee = input("Nominee Name: ")
        votes = ask_int("Number of Votes: ")
        nominee_list.append((nominee, votes))   # one (name, votes) pair per nominee

        if not ask_yes_no("Add another nominee? (y/n): "):
            print("Done adding nominees.")
            break

    eligible_voters = ask_int("Eligible Voters Count: ")
    return area_code, nominee_list, eligible_voters
    
# def build_messages(...):    # return a list of strings, one per value
#     return 0

# def encode_all(messages):   # return a list of codewords using encode_data
#     return 0

def run_sender():
    # Agreed standard key representation (e.g., x^3 + 1 -> 1001)
    SHARED_KEY = "1001" 
    
    # Create client socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 65432))
    
    payload = "Hello"
    encoded_bits, _ = encode_data(payload, SHARED_KEY)
    
    print(f"[Sender] Original text: {payload}")
    print(f"[Sender] Transmitting bits: {encoded_bits}")
    
    # Send raw binary string over the socket stream
    client_socket.sendall(encoded_bits.encode('utf-8'))
    
    # Wait for Receiver's Acknowledgement (ACK/NACK)
    response = client_socket.recv(1024).decode('utf-8')
    print(f"[Sender] Feedback from server: {response}")
    
    client_socket.close()

if __name__ == "__main__":

    area, nominees, eligible = collect_input()
    run_sender()
