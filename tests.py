import unittest

from johncena import CENA, print_subreddit, roll_dice, coinflip

class TestJohnCena(unittest.TestCase):
    def test_wikipedia(self):
        self.assertTrue(True)

    def test_print_subreddit(self):
        print_subreddit("johncena", None)
        self.assertEqual(CENA.text, "https://reddit.com/r/johncena")

    def test_diceroll_array(self):
        roll_dice("3d1", None)
        self.assertEquals(CENA.text, "[1, 1, 1]")

    def test_diceroll_total(self):
        roll_dice("3d1t", None)
        self.assertEquals(CENA.text, "3")

    def test_coinflip(self):
        coinflip("", None)
        outcomes = [
            "https://upload.wikimedia.org/wikipedia/en/d/d2/Toonie_-_front.png",
            "https://upload.wikimedia.org/wikipedia/en/thumb/6/6c/Toonie_-_back.png/220px-Toonie_-_back.png"
        ]
        self.assertTrue(CENA.text in outcomes)



unittest.main()
