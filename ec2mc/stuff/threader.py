from queue import Queue
from threading import Thread

class Threader(object):
    """thread arbitrary number of functions, then block when results wanted

    Attributes:
        result_queue (Queue): Thread-safe queue that holds the results.
        threads (Thread list): Threads of functions added with add_thread.
    """

    def __init__(self):
        self.result_queue = Queue()
        self.threads = []


    def add_thread(self, func, fargs):
        """add a function to be threaded

        Args:
            func (function): Function to thread.
            fargs (tuple): Arguments to pass to the func function.
        """
        self.threads.append(Thread(
            target=lambda f, args: self.result_queue.put([args[0], f(*args)]),
            args=(func, fargs)))
        self.threads[-1].start()


    def get_results(self, return_dict=False):
        """block threads until all are done, then return their results

        Args:
            return_dict (bool): Return dict instead of list. Threads' 
                function's first argument used as key.
        """

        for thread in self.threads:
            thread.join()

        if return_dict:
            results = {}
            while not self.result_queue.empty():
                key, value = self.result_queue.get()
                results[key] = value
        else:
            results = []
            while not self.result_queue.empty():
                results.append(self.result_queue.get()[1])

        return results
