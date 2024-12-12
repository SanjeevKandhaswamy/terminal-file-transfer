import asyncio

clients = {}  # Dictionary to store client info

# Function to handle each client asynchronously
async def handle_client(reader, writer):
    data = await reader.read(100)  # Receive client name
    client_name = data.decode().strip()
    addr = writer.get_extra_info('peername')
    clients[client_name] = addr  # Register client

    print(f"Client '{client_name}' connected from {addr}")

    while True:
        data = await reader.read(100)  # Wait for file transfer request
        if not data:
            break

        message = data.decode().strip()
        if message.startswith("SEND"):
            _, receiver, file_name = message.split()
            if receiver in clients:
                receiver_addr = clients[receiver]
                # Send the receiver's address to the sender
                writer.write(f"OK {receiver_addr[0]} {receiver_addr[1]} {file_name}".encode())
                await writer.drain()
                print(f"Forwarded file transfer request to {receiver}")
            else:
                writer.write(f"ERROR: Receiver {receiver} not available.".encode())
                await writer.drain()

    writer.close()
    await writer.wait_closed()

# Start the asynchronous server
async def main():
    server = await asyncio.start_server(handle_client, '127.0.0.1', 5001)
    async with server:
        print("Server started, waiting for connections...")
        await server.serve_forever()

asyncio.run(main())
