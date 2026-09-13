#!/usr/bin/env python3

from collections import Counter
from collections.abc import Callable
from enum import Enum
from os import read
from random import choice
from sys import stderr
from time import sleep
from functools import partial


class Ansi(str, Enum):
    CSI = "\033["


class Color(str, Enum):
    GREEN = Ansi.CSI + "32m"
    YELLOW = Ansi.CSI + "33m"
    RESET = Ansi.CSI + "0m"


class WordleLetterHint:
    class HintException(Exception):
        pass

    def __init__(self, letter: str) -> None:
        if len(letter) != 1:
            raise self.HintException(f"{letter} is not a letter")
        self.__letter = letter

    @property
    def letter(self) -> str:
        return self.__letter

    def __repr__(self) -> str:
        return f"{self.__letter}"

    def is_correct(self, char: str) -> bool:
        return self.__letter == char


class WordleSession:
    def __init__(self, word: str, guess_count: int = 6,
                 is_hard_mode: bool = False) -> None:
        self.__goal = word
        self.__guess_count = guess_count
        self.is_hard_mode = is_hard_mode
        self.__hints: list[WordleLetterHint] = list(
            map(lambda c: WordleLetterHint(c), word)
        )
        self.__guesses: list[tuple[str, list[Color]]] = []

    @property
    def goal(self) -> str:
        if self.__finished:
            return self.__goal
        return "cheater"

    @property
    def __winner(self) -> bool:
        return (
            bool(len(self.__guesses))
            and all(color is Color.GREEN for color in self.__guesses[-1][1])
        )

    @property
    def __finished(self) -> bool:
        return self.__winner or len(self.__guesses) == self.__guess_count

    def __repr__(self) -> str:
        goalstring = (
            "unfinished"
            if not self.__finished
            else f"goal: {self.__goal} ★"
            if self.__winner
            else f"goal: {self.__goal}"
        )
        guesses = "\n".join(
            self.get_colored_word(guess) for guess in self.__guesses
        )
        return (
            f"{goalstring}\n"
            f"guesses: {len(self.__guesses)}/{self.__guess_count}\n"
            f"{guesses}"
        )

    def get_colored_word(self, guess: tuple[str, list[Color]]) -> str:
        colored_word = ""
        for char, color in zip(*guess):
            colored_word += color.value + char.upper() + " " + Color.RESET
        return colored_word

    def print_previous_guesses(self) -> None:
        for guess in self.__guesses:
            print(self.get_colored_word(guess))

    def is_finished(self) -> bool:
        return self.__finished

    def get_colors(self, guess: str) -> list[Color]:
        colors: list[Color] = []
        char_counts = Counter(map(lambda h: h.letter, self.__hints))
        for i in range(len(guess)):
            guess_char = guess[i]
            hint = self.__hints[i]
            if hint.is_correct(guess_char):
                colors.append(Color.GREEN)
                char_counts[guess_char] -= 1
            else:
                colors.append(Color.RESET)
        for i in range(len(guess)):
            guess_char = guess[i]
            if (
                colors[i] != Color.GREEN
                and guess_char in char_counts
                and char_counts[guess_char] > 0
            ):
                colors[i] = Color.YELLOW
                char_counts[guess_char] -= 1
        return colors

    def guess(self, guess: str) -> None:
        colors = self.get_colors(guess)
        self.__guesses.append((guess, colors))

    def did_win(self) -> bool:
        return self.__finished and self.__winner

    def is_valid_hard_mode_guess(self, guess: str) -> bool:
        if not bool(self.__guesses):
            return True
        rest_guess_chars = list(guess)
        for char, goal_char, color in zip(guess, *self.__guesses[-1]):
            if color == Color.GREEN:
                if char != goal_char:
                    return False
                rest_guess_chars.remove(goal_char)
        for char, goal_char, color in zip(guess, *self.__guesses[-1]):
            if color == Color.YELLOW:
                if goal_char not in rest_guess_chars:
                    return False
                rest_guess_chars.remove(goal_char)
        return True


class WordleDict:
    class DictException(Exception):
        pass

    def __init__(self, path: str, wordlen: int = 5) -> None:
        with open(path) as dict_file:
            self.__dict: set[str] = set(
                map(lambda s: s.strip(), dict_file.readlines())
            )
            for word in self.__dict:
                if len(word) != wordlen:
                    raise self.DictException(
                        "found invalid word in dictionary "
                        f"({word},{len(word)})"
                    )

    def get_random(self) -> str:
        return choice(list(self.__dict))

    def is_in_dictionary(self, word: str) -> bool:
        return word in self.__dict


class Wordle:
    class WordleException(Exception):
        pass

    def __init__(self, path: str = "./words.txt") -> None:
        try:
            self.__dict = WordleDict(path, wordlen=5)
        except Exception as e:
            print(
                f"Error occurred while building dictionary: {e}", file=stderr
            )
            raise self.WordleException from e
        self.__sessions: list[WordleSession] = []

    def run_session(self, is_hard_mode: bool = False) -> None:
        # DEBUG PLACE
        goal = self.__dict.get_random()
        print(goal)
        # session = WordleSession("llama", guess_count=6)
        session = WordleSession(goal, guess_count=6, is_hard_mode=is_hard_mode)
        self.__sessions.append(session)

        while not session.is_finished():
            guess = self.get_guess(session)
            session.guess(guess)
            # print("\033[2J\033[H")
            session.print_previous_guesses()
        if session.did_win():
            print("congratulations you're won!")
        else:
            print(f"eeeeeeeeeeeeyikes, you couldn't even guess {session.goal}")

    def get_guess(self, session: WordleSession) -> str:
        def is_valid_guess(guess) -> bool:
            if not guess:
                return False
            # COMMENTED OUT FOR HARD MODE TESTING
            if not self.__dict.is_in_dictionary(guess):
                print(f"{guess} is not a valid guess")
                return False
            if (session.is_hard_mode
                    and not session.is_valid_hard_mode_guess(guess)):
                print("hard mode violation")
                return False
            return True

        guess = ""
        while not is_valid_guess(guess):
            try:
                guess = input("guess: ").lower()
                # print("\033[2F\033[K", end="")
            except EOFError:
                print("\033[G", sep="", end="")
                pass
        return guess

    def list_sessions(self) -> None:
        for id, session in enumerate(self.__sessions):
            print(f"{id + 1})", *str(session).splitlines()[:2], "", sep="\n")

    def examine_session(self, id: int) -> None:
        print(self.__sessions[id - 1])


class Program:
    GAME_NAME = "Wordle"

    def __init__(self) -> None:
        self.__game = Wordle()
        # print("\033[2J\033[H")
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
            # print("\033[2J\033[H")
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
        print("press any key to continue...", end="", flush=True)
        read(0, 1)

    def __play_round(self, is_hard_mode: bool = False) -> None:
        try:
            print("\033[2J\033[H")
            self.__game.run_session(is_hard_mode)
            self.__wait()
        except Exception as e:
            print(e, e.__cause__, file=stderr)

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
    Program().start()
