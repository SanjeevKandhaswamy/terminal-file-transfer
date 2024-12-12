import asyncio
import socket
import hashlib
import gzip
import os

# Function to compute SHA-256 hash of a file
def compute_hash(file_name):
    sha256 = hashlib.sha256()
    with open(file_name, "rb") as f:
        while chunk := f.read(1024):
            sha256.update(chunk)
    return sha256.hexdigest()

# Compress file using gzip
def compress_file(file_name):
    compressed_file = f"{file_name}.gz"
    with open(file_name, "rb") as f_in, gzip.open(compressed_file, "wb") as f_out:
        f_out.writelines(f_in)
    return compressed_file

# Decompress file using gzip
def decompress_file(file_name):
    decompressed_file = file_name.replace(".gz", "")
    with gzip.open(file_name, "rb") as f_in, open(decompressed_file, "wb") as f_out:
        f_out.writelines(f_in)
    return decompressed_file

# Function to send file over TCP connection
async def send_file(file_name, receiver_ip, receiver_port):
    compressed_file = compress_file(file_name)  # Compress the file
    file_hash = compute_hash(compressed_file)   # Compute hash of the compressed file

    try:
        reader, writer = await asyncio.open_connection(receiver_ip, receiver_port)
        print(f"Connected to receiver at {receiver_ip}:{receiver_port}")

        writer.write(file_hash.encode())  # Send file hash first
        await writer.drain()
        print(f"Sent file hash: {file_hash}")

        # Send the file in chunks
        with open(compressed_file, "rb") as f:
            while chunk := f.read(1024):
                writer.write(chunk)
                await writer.drain()

        print(f"File '{file_name}' sent successfully.")
    except Exception as e:
        print(f"Error sending file: {e}")
    finally:
        writer.close()
        await writer.wait_closed()

# Function to receive a file from a sender
async def receive_file(file_name, connection):
    reader, writer = connection

    try:
        # Receive file hash
        file_hash = await reader.read(64)
        file_hash = file_hash.decode()
        print(f"Received file hash: {file_hash}")

        # Write received file
        compressed_file = f"{file_name}.gz"
        with open(compressed_file, "wb") as f:
            while data := await reader.read(1024):
                f.write(data)
        
        # Compare hashes
        received_hash = compute_hash(compressed_file)
        if received_hash == file_hash:
            print(f"File '{file_name}' received successfully with matching hash: {received_hash}")
            decompress_file(compressed_file)  # Decompress the file
            print(f"File '{file_name}' decompressed.")
        else:
            print(f"Hash mismatch! Expected: {file_hash}, Received: {received_hash}")

    except Exception as e:
        print(f"Error receiving file: {e}")
    finally:
        writer.close()
        await writer.wait_closed()

# Main client function
async def start_client(client_name):
    reader, writer = await asyncio.open_connection('127.0.0.1', 5001)
    writer.write(client_name.encode())  # Send client name to the server
    await writer.drain()

    while True:
        action = input("Enter 'SEND <receiver> <file>' to send a file or 'exit' to quit: ")
        if action.lower() == 'exit':
            break

        if action.startswith("SEND"):
            writer.write(action.encode())  # Send the transfer request to the server
            await writer.drain()

            # Receive OK message with receiver's details
            response = await reader.read(1024)
            response = response.decode()

            if response.startswith("OK"):
                _, receiver_ip, receiver_port, file_name = response.split()
                await send_file(file_name, receiver_ip, receiver_port)
            else:
                print(response)  # Show any error messages

if __name__ == "__main__":
    client_name = input("Enter your name: ")
    asyncio.run(start_client(client_name))
