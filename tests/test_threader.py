from time import sleep
from random import randint
import pytest

from ec2mc.stuff.threader import Threader

def test_threader_dict_return():
    """test that functions' first args set as function returns' dict keys"""
    def func(dict_key, multiplier):
        return dict_key*multiplier

    threader = Threader()
    for index in range(5):
        threader.add_thread(func, (index, 10))
    assert threader.get_results(return_dict=True) == {
        0: 0, 1: 10, 2: 20, 3: 30, 4: 40
    }


def test_threader_fifo():
    """test that threader is first-in, first-out"""
    def func(index):
        sleep(randint(5, 25)/100)
        return index

    threader = Threader()
    for index in range(10):
        threader.add_thread(func, (index,))
    assert threader.get_results() == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


def test_threader_add_thread_type_verification():
    """test that add_thread only accepts function and tuple as args 1 and 2"""
    def func(index):
        return index
    not_a_function = "testing"

    with pytest.raises(ValueError) as excinfo:
        threader = Threader()
        threader.add_thread(not_a_function, ("1st arg",))
    assert str(excinfo.value) == "func must be a function."

    with pytest.raises(ValueError) as excinfo:
        threader = Threader()
        threader.add_thread(func, "fargs...")
    assert str(excinfo.value) == "fargs must be a tuple."
