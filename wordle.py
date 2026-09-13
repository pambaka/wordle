#!/usr/bin/env python3

from collections.abc import Callable
from os import read
from sys import stderr
from time import sleep
from functools import partial
from ansi import Cursor
from game import Wordle


class Program:
    GAME_NAME = "Wordle"

    def __init__(self) -> None:
        self.__game = Wordle()
        print(Cursor.erase_display + Cursor.home)
        print(f"Welcome to {self.GAME_NAME}!")
        sleep(1)
        self.__quit = False
        self.MENU_ITEMS: list[tuple[list, str, Callable]] = [
            (["1", "play"], "Play round", Program.__play_round),
            (
                ["2", "hard"],
                "Play round (Hard mode)",
                partial(Program.__play_round, is_hard_mode=True)),
            (
                ["3", "list"],
                "Look at previous session results",
                Program.__list_sessions,
            ),
            (["4", "quit", "q"], "Quit", Program.__quit_game)
        ]

    def start(self) -> None:
        def unpack_options(
            triggers: list[str], description: str, _: Callable
        ) -> str:
            return f"{triggers[0]}) {description}"

        while not self.__quit:
            print(Cursor.erase_display + Cursor.home)
            print(
                *map(lambda t: unpack_options(*t), self.MENU_ITEMS), sep="\n"
            )
            try:
                user_input = input("?: ").lower()
            except EOFError:
                user_input = "quit"
            except Exception:
                user_input = ""
            for trigger_inputs, _, function in self.MENU_ITEMS:
                if user_input in trigger_inputs:
                    function(self)
                    break
            else:
                print("Input not recognized, try again")
        print("Quitting!")

    def __wait(self) -> None:
        print("press Enter to continue...", end="", flush=True)
        read(0, 1)

    def __play_round(self, is_hard_mode: bool = False) -> None:
        try:
            print(Cursor.erase_display + Cursor.home)
            self.__game.run_session(is_hard_mode)
            self.__wait()
        except Exception as e:
            print(e, file=stderr)

    def __list_sessions(self) -> None:
        print("Sessions:")
        self.__game.list_sessions()
        try:
            self.__game.examine_session(int(input("session id: ")))
            self.__wait()
        except IndexError:
            print("index out of bounds")
        except ValueError as e:
            print(f"{str(e).split(': ')[1]} is not a valid id")
        except EOFError:
            pass
        except Exception as e:
            print(e)
            raise

    def __quit_game(self) -> None:
        self.__quit = True


if __name__ == "__main__":
    try:
        Program().start()
    except Wordle.WordleException:
        raise SystemExit(1)
