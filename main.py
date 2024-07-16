import os
import subprocess
import sys

sys.path.append(os.getcwd())


def main():
    telegram_bot_proc = subprocess.Popen([sys.executable, 'telegram_bot/main.py'])
    server = subprocess.Popen([sys.executable, 'server/main.py', '8887'])

    try:
        while True:
            pass
    finally:
        telegram_bot_proc.terminate()
        server.terminate()


if __name__ == '__main__':
    main()
