import argparse
import getpass
import os
import sys

from . import Keychain

DEFAULT_KEYCHAIN_PATH = "~/Dropbox/1Password.agilekeychain"
try:
    EX_DATAERR = os.EX_DATAERR
except AttributeError:
    # os.EX_DATAERR is only available on Unix
    EX_DATAERR = 65


class CLI(object):
    """
    The 1pass command line interface.
    """

    def __init__(self, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
                 getpass=getpass.getpass, arguments=sys.argv[1:]):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.getpass = getpass
        self.arguments = self.argument_parser().parse_args(arguments)
        self.keychain = Keychain(self.arguments.path)

    def run(self):
        """
        The main entry point, performs the appropriate action for the given
        arguments.
        """
        self._unlock_keychain()

        item = self.keychain.item(
            self.arguments.item,
            fuzzy_threshold=self._fuzzy_threshold(),
        )

        if item is not None:
            self.stdout.write("%s\n" % item.password)
        else:
            self.stderr.write("1pass: Could not find an item named '%s'\n" % (
                self.arguments.item,
            ))
            sys.exit(EX_DATAERR)

    def argument_parser(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("item", help="The name of the password to decrypt")
        parser.add_argument(
            "--path",
            default=os.environ.get("ONEPASSWORD_KEYCHAIN", DEFAULT_KEYCHAIN_PATH),
            help="Path to your 1Password.agilekeychain file",
        )
        parser.add_argument(
            "--fuzzy",
            action="store_true",
            help="Perform fuzzy matching on the item",
        )
        parser.add_argument(
            "--no-prompt",
            action="store_true",
            help="Don't prompt for a password, read from STDIN instead",
        )
        return parser

    def _unlock_keychain(self):
        if self.arguments.no_prompt:
            self._unlock_keychain_stdin()
        else:
            self._unlock_keychain_prompt()

    def _unlock_keychain_stdin(self):
        password = self.stdin.read().strip().encode("utf-8")
        self.keychain.unlock(password)
        if self.keychain.locked:
            self.stderr.write("1pass: Incorrect master password\n")
            sys.exit(EX_DATAERR)

    def _unlock_keychain_prompt(self):
        while self.keychain.locked:
            try:
                self.keychain.unlock(self.getpass("Master password: "))
            except KeyboardInterrupt:
                self.stdout.write("\n")
                sys.exit(0)

    def _fuzzy_threshold(self):
        if self.arguments.fuzzy:
            return 70
        else:
            return 100
