from ansi import Color, Cursor
from collections import Counter
from random import choice
from sys import stderr


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
        self.__hints: list[WordleLetterHint] = list(
            map(lambda c: WordleLetterHint(c), word)
        )
        self.__guesses: list[str] = []
        self.__finished: bool = False
        self.__guess_count = guess_count
        self.__winner = False
        self.__last_guess_hints: list[tuple[str, Color]] = []
        self.is_hard_mode = is_hard_mode

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
        self.__last_guess_hints = colored
        rv = ""
        for char, color in colored:
            rv += color + char.upper() + " " + Color.RESET
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
                map(lambda s: s.strip().lower(), dict_file.readlines())
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
        # print(goal)
        # session = WordleSession("llama", guess_count=6)
        session = WordleSession(goal, guess_count=6, is_hard_mode=is_hard_mode)
        self.__sessions.append(session)

        while not session.is_finished():
            guess = self.get_guess(session)
            session.guess(guess)
            print(Cursor.erase_display + Cursor.home)
            session.print_previous_guesses()
        if session.did_win():
            print("congratulations you're won!")
        else:
            print(f"eeeeeeeeeeeeyikes, you couldn't even guess {session.goal}")

    def get_guess(self, session: WordleSession) -> str:
        def is_valid_guess(guess: str | None) -> bool:
            if guess is None:
                return False
            if not guess:
                print(Cursor.prev_line + Cursor.erase_line_right, end="")
                return False
            if not self.__dict.is_in_dictionary(guess):
                print(Cursor.erase_line_right + "", end="")
                print(f"{guess} is not a valid guess")
                print(Cursor.prev_line_2 + Cursor.erase_line_right, end="")
                return False
            if (session.is_hard_mode
                    and not session.is_valid_hard_mode_guess(guess)):
                print("hard mode violation")
                print(Cursor.prev_line_2 + Cursor.erase_line_right, end="")
                return False
            return True

        guess: str | None = None
        while not is_valid_guess(guess):
            try:
                guess = input("guess: ").lower()
            except EOFError:
                print(Cursor.line_start + Cursor.erase_line_right, end="")
                guess = None
        assert guess is not None
        return guess

    def list_sessions(self) -> None:
        for id, session in enumerate(self.__sessions):
            print(f"{id + 1})", *str(session).splitlines()[:2], "", sep="\n")

    def examine_session(self, id: int) -> None:
        print(self.__sessions[id - 1])
