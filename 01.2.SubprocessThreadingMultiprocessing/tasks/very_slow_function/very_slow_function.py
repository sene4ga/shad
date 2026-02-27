import time
from os import cpu_count


def very_slow_function(x: int) -> int:
    """Function which calculates square of given number really slowly
    :param x: given number
    :return: number ** 2
    """
    time.sleep(0.3)
    return x ** 2


def calc_squares_simple(bound: int) -> list[int]:
    """Function that calculates squares of numbers in range [0; bound)
    :param bound: positive upper bound for range
    :return: list of squared numbers
    """
    ans = [very_slow_function(i) for i in range(bound)]
    return ans


def calc_squares_multithreading(bound: int) -> list[int]:
    """Function that calculates squares of numbers in range [0; bound)
    using threading.Thread
    :param bound: positive upper bound for range
    :return: list of squared numbers
    """
    from threading import Thread
    vector = list(range(bound))
    res = []
    threads = []

    def worker(i):
        ans = very_slow_function(i)
        res.append(ans)

    for arg in vector:
        x = Thread(target=worker, args=(arg,))
        x.start()
        threads.append(x)

    for thread in threads:
        thread.join()

    return res



def calc_squares_multiprocessing(bound: int) -> list[int]:
    """Function that calculates squares of numbers in range [0; bound)
    using multiprocessing.Pool
    :param bound: positive upper bound for range
    :return: list of squared numbers
    """
    from multiprocessing import Pool
    vector = list(range(bound))
    with Pool(processes=cpu_count()) as pool:
        x = pool.map(very_slow_function, vector)
        return x

