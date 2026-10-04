import argparse


class BaseApp:
    def __init__(self):
        # Your initialization code
        pass

    def __enter__(self):
        # This code runs when entering the 'with' block
        # Return the object itself or whatever resource you want to use
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # This code runs when exiting the 'with' block
        # Handle cleanup here (e.g., closing connections, files, etc.)

        # Return False to let any exceptions propagate, or True to suppress them
        return False

    def add_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show extra output.',
        )

        return parser

    def main(self):
        # Your main application logic here
        pass

    def run(self):
        parser = self.add_args()
        self.args = parser.parse_args()

        self.main()
