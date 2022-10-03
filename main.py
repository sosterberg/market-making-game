import logging

LOG = logging.getLogger(__name__)


def main():
    logging.basicConfig(filename='market-making-game.log', level=logging.INFO)


if __name__ == '__main__':
    main()
