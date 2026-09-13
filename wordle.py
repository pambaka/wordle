#!/usr/bin/env python3

from collections import Counter
from collections.abc import Callable
from enum import Enum
from os import read
from random import choice
from sys import stderr
from time import sleep


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
    def __init__(self, word: str, guess_count: int = 6) -> None:
        self.__goal = word
        self.__hints: list[WordleLetterHint] = list(
            map(lambda c: WordleLetterHint(c), word)
        )
        self.__guesses: list[str] = []
        self.__finished: bool = False
        self.__guess_count = guess_count
        self.__winner = False
        self.__last_guess_hints: list[WordleLetterHint] = []

    @property
    def goal(self) -> str:
        if self.__finished:
            return self.__goal
        return "cheater"

    def __repr__(self) -> str:
        guesses = ""
        goalstring = (
            "unfinished"
            if not self.__finished
            else f"goal: {self.__goal} ★"
            if self.__winner
            else f"goal: {self.__goal}"
        )
        for guess in self.__guesses:
            guesses += guess + "\n"
        return (
            f"{goalstring}\n"
            f"guesses: {len(self.__guesses)}/{self.__guess_count}\n"
            f"{guesses}"
        )

    def print_previous_guesses(self) -> None:
        for guess in self.__guesses:
            print(guess)

    def is_finished(self) -> bool:
        return self.__finished

    def set_colors(self, guess: str) -> str:
        colored: list[tuple[str, Color]] = []
        char_counts = Counter(map(lambda h: h.letter, self.__hints))
        for i in range(len(guess)):
            guess_char = guess[i]
            hint = self.__hints[i]
            if hint.is_correct(guess_char):
                colored.append((guess_char, Color.GREEN))
                char_counts[guess_char] -= 1
            else:
                colored.append((guess_char, Color.RESET))
        for i in range(len(guess)):
            guess_char = guess[i]
            if (
                colored[i][1] != Color.GREEN
                and guess_char in char_counts
                and char_counts[guess_char] > 0
            ):
                colored[i] = (guess_char, Color.YELLOW)
                char_counts[guess_char] -= 1
        rv = ""
        self.__last_guess_hints = colored
        for char, color in colored:
            rv += f"{color.value}{char}{Color.RESET.value}"
        return rv

    def guess(self, guess: str) -> None:
        if guess == self.__goal:
            self.__finished = True
            self.__winner = True
        guess = self.set_colors(guess)
        self.__guesses.append(guess)
        if len(self.__guesses) == self.__guess_count:
            self.__finished = True

    def did_win(self) -> bool:
        return self.__finished and self.__winner

    def is_valid_hard_mode_guess(self, guess: str) -> bool:
        rest_guess_chars = list(guess)

        for char, (goal_char, color) in zip(guess, self.__last_guess_hints):
            if color == Color.GREEN:
                if char != goal_char:
                    return False
                rest_guess_chars.remove(goal_char)

        for char, (goal_char, color) in zip(guess, self.__last_guess_hints):
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

    def create_session(self) -> None:
        # DEBUG PLACE
        goal = self.__dict.get_random()
        print(goal)
        self.__sessions.append(
            # WordleSession("llama", guess_count=6)
            WordleSession(goal, guess_count=6)
            )

    def get_guess(self, is_hard_mode: bool = True) -> str:
        def is_valid_guess(guess) -> bool:
            # COMMENTED OUT FOR HARD MODE TESTING
            # if not self.__dict.is_in_dictionary(guess):
            #     print(f"{guess} is not a valid guess")
            #     return False
            if is_hard_mode and not self.__sessions[-1].is_valid_hard_mode_guess(guess):
                print("hard mode violation")
                return False
            return True

        guess = input("guess: ")
        while not is_valid_guess(guess):
            try:
                guess = input("guess: ")
            except EOFError:
                print("\033[G", sep="", end="")
                pass
        return guess

    def do_next_session(self, is_hard_mode: bool) -> None:
        session = list(filter(lambda s: not s.is_finished(), self.__sessions))[
            0
        ]
        while not session.is_finished():
            guess = self.get_guess(is_hard_mode)
            session.guess(guess)
            # print("\033[2J\033[H")
            session.print_previous_guesses()
        if session.did_win():
            print("congratulations you're won!")
        else:
            print(f"eeeeeeeeeeeeyikes, you couldn't even guess {session.goal}")

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
        self.MENU_ITEMS = [
            (["1", "play"], "Play round", Program.__play_round),
            (["2", "hard"], "Play round (Hard mode)", Program.__play_hard_mode_round),
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
            self.__game.create_session()
            self.__game.do_next_session(is_hard_mode)
            self.__wait()
        except Exception as e:
            print(e, file=stderr)

    def __play_hard_mode_round(self) -> None:
        self.__play_round(is_hard_mode=True)

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
