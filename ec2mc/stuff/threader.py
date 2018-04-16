from queue import Queue
from threading import Thread

class Threader(object):
    """thread arbitrary number of functions, then block when results wanted

    Attributes:
        threads (list): Threads of functions added with add_thread.
        results (list): Results to be returned by get_results.
    """

    def __init__(self):
        self.thread_queue = Queue()
        self.threads = []

    def add_thread(self, func, args):
        """add a function to be threaded"""
        self.threads.append(Thread(
            target=lambda q, func_args: q.put(func(*func_args)),
            args=(self.thread_queue, args)))
        self.threads[-1].start()

    def get_results(self, return_dict=False):
        """block threads until all are done, then return their results

        Args:
            return_dict (bool): Return a dict instead of a list. Requires 
                each thread to return a tuple with two values.
        """

        for thread in self.threads:
            thread.join()

        if return_dict:
            results = {}
            while not self.thread_queue.empty():
                key, value = self.thread_queue.get()
                results[key] = value
        else:
            results = []
            while not self.thread_queue.empty():
                results.append(self.thread_queue.get())

        return results
