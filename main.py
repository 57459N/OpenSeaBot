import os
import subprocess
import sys

import config

sys.path.append(os.getcwd())


def main():
    telegram_bot_proc = subprocess.Popen([sys.executable, 'telegram_bot/main.py'])
    server = subprocess.Popen([sys.executable, 'server/main.py', str(config.SERVER_HOST_PORT)])
    go_proxy_server = subprocess.Popen(['proxy_server.exe'])

    try:
        while True:
            pass
    finally:
        telegram_bot_proc.terminate()
        server.terminate()
        go_proxy_server.terminate()


if __name__ == '__main__':
    main()
