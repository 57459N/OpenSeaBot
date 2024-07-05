import asyncio
import subprocess
import sys
import aiohttp


async def send_message(slave_id, message):
    async with aiohttp.ClientSession() as session:
        url = f'http://127.0.0.1:{8888 + slave_id}/message'
        async with session.post(url, json={'message': message}) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"Received from slave {slave_id}: {data['response']}")
            else:
                print(f"Failed to send message to slave {slave_id}")


async def handle_user_input(slaves):
    while True:
        user_input = await asyncio.get_event_loop().run_in_executor(None, input, "> ")
        if user_input.startswith("send "):
            parts = user_input.split(" ", 2)
            if len(parts) == 3:
                try:
                    slave_id = int(parts[1])
                    message = parts[2]
                    if slave_id in slaves:
                        asyncio.create_task(send_message(slave_id, message))
                    else:
                        print(f"Slave {slave_id} is not running.")
                except ValueError:
                    print("Invalid command format. Use: send <slave_id> <message>")
            else:
                print("Invalid command format. Use: send <slave_id> <message>")
        elif user_input.startswith("create "):
            parts = user_input.split(" ")
            if len(parts) == 2:
                try:
                    slave_id = int(parts[1])
                    if slave_id not in slaves:
                        process = subprocess.Popen([sys.executable, 'slave.py', str(slave_id)])
                        slaves[slave_id] = process
                        await asyncio.sleep(1)  # Ensure the server is started
                        print(f"Slave {slave_id} created.")
                    else:
                        print(f"Slave {slave_id} is already running.")
                except ValueError:
                    print("Invalid command format. Use: create <slave_id>")
            else:
                print("Invalid command format. Use: create <slave_id>")
        elif user_input.startswith("close "):
            parts = user_input.split(" ")
            if len(parts) == 2:
                try:
                    slave_id = int(parts[1])
                    if slave_id in slaves:
                        slaves[slave_id].terminate()
                        slaves[slave_id] = None
                        print(f"Slave {slave_id} closed.")
                    else:
                        print(f"Slave {slave_id} is not running.")
                except ValueError:
                    print("Invalid command format. Use: close <slave_id>")
            else:
                print("Invalid command format. Use: close <slave_id>")
        elif user_input == "exit":
            break
        else:
            print("Unknown command. Use: send <slave_id> <message>, create <slave_id>, close <slave_id> or exit")


async def main():
    # Initialize slaves dictionary
    slaves = {}

    # Handle user input
    user_input_task = asyncio.create_task(handle_user_input(slaves))

    # Wait for user input task to complete (which happens on "exit" command)
    await user_input_task

    # Stop slaves
    for slave_id, process in slaves.items():
        if process is not None:
            process.terminate()

    print("All slaves have been stopped.")


if __name__ == '__main__':
    asyncio.run(main())
