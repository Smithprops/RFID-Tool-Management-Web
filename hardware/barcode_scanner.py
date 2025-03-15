import sys

def read_barcode():
    barcode = input("Scan barcode: ")  # Simulating scanner input
    return barcode.strip()

if __name__ == "__main__":
    print("Scanned barcode:", read_barcode())
