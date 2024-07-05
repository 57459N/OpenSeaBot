import subprocess
import sys


def main():
    telegram_bot_proc = subprocess.Popen([sys.executable, 'telegram_bot/main.py'])

    try:
        while True:
            pass
    finally:
        telegram_bot_proc.terminate()


if __name__ == '__main__':
    main()
