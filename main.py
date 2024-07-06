import subprocess
import sys


# TODO: HANDLE UNCLOSED SESSION, PROBABLY WITH LONG SLEEP, MAKE CLOSE SESSION ON __DEL__ IN REQUEST CLASS
# TODO: FIGURE OUT STATES AND WORKFLOW IN UNIT
# TODO: MAKE SETTINGS FROM BOT PASS


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
