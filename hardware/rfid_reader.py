import sys

def read_rfid():
    rfid = input("Scan RFID/NFC badge: ")  # Simulating RFID input
    return rfid.strip()

if __name__ == "__main__":
    print("Scanned RFID:", read_rfid())
