from bot import start
from config import get_settings


def main():
    print(get_settings())
    start()


if __name__ == '__main__':
    main()
