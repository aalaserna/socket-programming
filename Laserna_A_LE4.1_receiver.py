# ANDREA A. LASERNA
# CMSC 137

# SERVER
# Checks the CRC of every value, adds the votes, and replies with a status message
# If any value has an error, all data from the sender is disregarded
import socket

from crc_module import mod2div

# Settings matching with sender
HOST = '127.0.0.1'   # receiver binds or listens to this ip address
PORT = 65432        
SHARED_KEY = "1001"  # CRC divisor key (x^3 + 1)

def decode_codeword(bits, key):
    # Check the CRC
    # Returns (True, text) if valid, otherwise (False, None)
    key_len = len(key)
    '''
    Safety check: 
        codewords shorter than (1 char + CRC), 
        OR containing anything other than 0 and 1 is rejected.
    '''
    # Shortest codeword is len 11 (8 bits + 3 bit CRC)
    if len(bits) < key_len + 7 or any(b not in "01" for b in bits):
        return False, None

    # CRC Check: Dividing the whole codeword (data + CRC) must leave a remainder of all 0s
    if "1" in mod2div(bits, key):
        return False, None

    # Remove the CRC bits
    data_bits = bits[:-(key_len - 1)]         
    if len(data_bits) % 8 != 0:
        return False, None

    # Conversion: 8 bits (for loop to get each 8 bit) -> bin to num (base 2) -> chr(num) -> char
    text = "".join(chr(int(data_bits[i:i + 8], 2)) for i in range(0, len(data_bits), 8))
    return True, text


def read_messages(conn):
    # Read one codeword per line until the sender closes its side
    results = []
    with conn.makefile('r') as stream:
        for line in stream:
            bits = line.strip()
            if bits:
                results.append(decode_codeword(bits, SHARED_KEY))
    # results = [(CRC status, data)]
    return results


def parse_messages(results):
    # Turn the verified messages into data
    # Returns (data, None) or (None, error text)
    area_code, eligible, nominees = None, None, []

    # Disregard all data if failure
    # Success   = data, None (no error)
    # Failurue  = None (no data), error
    
    for number, (ok, text) in enumerate(results, 1):
        if not ok:
            return None, f"CRC error detected in message #{number}"

        parts = text.split("|")
        try:
            if parts[0] == "A" and len(parts) == 2 and area_code is None:
                area_code = parts[1]
            elif parts[0] == "N" and len(parts) == 3:
                nominees.append((parts[1], int(parts[2])))
            elif parts[0] == "E" and len(parts) == 2 and eligible is None:
                eligible = int(parts[1])
            else:
                return None, f"Unexpected format in message #{number}"
        except ValueError:
            return None, f"Invalid number in message #{number}"

    # Area code, eligible voters, and at least 1 nominee must exist
    if area_code is None or eligible is None or not nominees:
        return None, "Incomplete data (area code, nominees, or eligible voters missing)"
    # Positive values only
    if eligible <= 0 or any(votes < 0 for _, votes in nominees):
        return None, "Invalid vote or voter count"

    total_votes = sum(votes for _, votes in nominees)
    # Total votes can't exceed eligible voters
    if total_votes > eligible:
        return None, "Total votes is greater than the number of eligible voters"

    return {"area": area_code, "nominees": nominees, "eligible": eligible}, None


def show_results(data):
    nominees, eligible = data["nominees"], data["eligible"]
    total_votes = sum(votes for _, votes in nominees)

    # Highest votes first
    ranked = sorted(nominees, key=lambda item: item[1], reverse=True)

    print(f"\n===== Results for Area Code {data['area']} =====")
    print(f"{'Rank':<6}{'Nominee':<20}{'Votes':>8}{'Percent':>10}")
    for rank, (name, votes) in enumerate(ranked, 1):
        percent = votes / total_votes * 100 if total_votes else 0
        print(f"{rank:<6}{name:<20}{votes:>8}{percent:>9.2f}%")

    turnout = total_votes / eligible * 100
    print("-" * 44)
    print(f"Total votes:            {total_votes}")
    print(f"Total eligible voters:  {eligible}")
    print(f"Voters who voted:       {turnout:.2f}%")


def run_receiver():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Re-run receiver right away
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Step 1. claim address and port
    server_socket.bind((HOST, PORT))
    # Wait for sender to connect
    server_socket.listen(1)
    print(f"[Receiver] Listening on {HOST}:{PORT} ...")
    # Pause until sender connects
    conn, addr = server_socket.accept()
    print(f"[Receiver] Connected to: {addr}")

    # Step 2. read every codeword from the sender
    results = read_messages(conn)
    print(f"[Receiver] {len(results)} messages received.")

    # Step 3. check crc on each codeword
    data, error = parse_messages(results)

    if error:
        # Step 4. if any check fails, discard & err
        print(f"[Receiver] ERROR: {error}. All data disregarded.")
        conn.sendall(f"ERROR: {error}. All data was discarded.".encode('utf-8'))
    else:
        # Step 4. if all pass, parse messages -> add votes -> show results
        print("[Receiver] All CRC checks passed.")
        show_results(data)
        # Step 5. reply OK
        conn.sendall("OK: All data verified and votes added.".encode('utf-8'))

    conn.close()
    server_socket.close()


if __name__ == "__main__":
    run_receiver()