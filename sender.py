# CLIENT
# Sends area code, each nominee with total votes, and total eligible voters
# Every value is sent as its own message with a CRC attached
import random
import socket

from crc_module import encode_data

# Settings matching with receiver
HOST = '127.0.0.1'   # sender connects to ip address
PORT = 65432         
SHARED_KEY = "1001"  # CRC divisor key (x^3 + 1)

def ask_text(prompt):
    # Ask for non-empty ASCII text
    while True:
        value = input(prompt).strip()
        if value and value.isascii() and "|" not in value:
            return value
        print("Please enter plain text without the '|' character.")


def ask_int(prompt, minimum=0):
    # Ask for a whole number that is at least minimum
    while True:
        try:
            number = int(input(prompt))
            if number >= minimum:
                return number
        except ValueError:
            pass
        print(f"  Please enter a whole number >= {minimum}.")


def collect_input():
    area_code = ask_text("Area code: ")
    count = ask_int("Number of nominees: ", minimum=1)
    nominees = []
    for i in range(1, count + 1):
        name = ask_text(f"  Nominee {i} name: ")
        votes = ask_int(f"  Total votes for {name}: ")
        nominees.append((name, votes))
    eligible = ask_int("Total eligible voters: ", minimum=1)
    return area_code, nominees, eligible


def build_messages(area_code, nominees, eligible):
    # First letter tells the receiver what it is
    messages = [f"A|{area_code}"]
    messages += [f"N|{name}|{votes}" for name, votes in nominees]
    messages.append(f"E|{eligible}")
    return messages

def flip_random_bit(codeword):
    # Simulate noise by flipping a random position in the codeword
    position = random.randrange(len(codeword))
    flipped = "1" if codeword[position] == "0" else "0"
    return codeword[:position] + flipped + codeword[position + 1:]


def run_sender():
    # Step 1. ask user for data
    area_code, nominees, eligible = collect_input()
    # Step 2. turn each value into a text message
    messages = build_messages(area_code, nominees, eligible)

    # Step 3. encode every message with CRC
    codewords = []
    print("\n[Sender] Messages with CRC:")
    for number, text in enumerate(messages, 1):
        # Adds len(key)-1 zeros, divides by 1001 using mod 2, remainder is the CRC
        codeword, data_bits = encode_data(text, SHARED_KEY)
        # Everything after msg bits is the crc
        crc = codeword[len(data_bits):]
        print(f"  #{number} '{text}'  CRC = {crc}")
        codewords.append(codeword)

    # Optional: corrupt one message to test the receiver's error handling
    if input("\nSimulate a transmission error? (y/N): ").strip().lower() == "y":
        target = random.randrange(len(codewords))
        codewords[target] = flip_random_bit(codewords[target])
        print(f"[Sender] A bit was flipped in message #{target + 1}.")

    # TCP connection to receiver
    try:
        # IPv4, TCP
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))
    except ConnectionRefusedError:
        print("[Sender] Could not connect. Start receiver.py first and check the IP and port.")
        return

    # Step 4. send everything to receiver
    # New line is how the receiver tells where one codeword ends, encode into bytes for the socket to send
    client_socket.sendall(("\n".join(codewords) + "\n").encode('utf-8'))
    # Done sending
    client_socket.shutdown(socket.SHUT_WR)
    print("[Sender] All values sent.")

    # Step 5. receiver's reply
    response = client_socket.recv(1024).decode('utf-8')
    print(f"[Sender] Status from receiver: {response}")
    client_socket.close()


if __name__ == "__main__":
    run_sender()