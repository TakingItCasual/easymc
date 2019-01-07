from queue import Queue
from threading import Thread

class Threader:
    """thread arbitrary number of functions, then block when results wanted

    Attributes:
        _result_queue (Queue): Thread-safe queue that holds the results.
        _threads (list[Thread]): Threads of functions added with add_thread.
    """

    def __init__(self):
        self._result_queue = Queue()
        self._threads = []


    def _worker(self, func, fargs):
        """insert threaded function into queue to make its return retrievable

        The index of the thread and the threaded function's first arg are
        inserted into the queue, preceding the threaded function itself.

        Args: See add_thread
        """
        return self._result_queue.put([
            len(self._threads), fargs[0], func(*fargs)])


    def add_thread(self, func, fargs):
        """add a function to be threaded

        Args:
            func (function): Function to thread.
            fargs (tuple): Argument(s) to pass to the func function.

        Raises:
            ValueError: If func isn't callable, or if fargs not a tuple.
        """
        if not callable(func):
            raise ValueError("func must be a function.")
        if not isinstance(fargs, tuple) or not fargs:
            raise ValueError("fargs must be a non-empty tuple.")

        self._threads.append(Thread(target=self._worker, args=(func, fargs)))
        self._threads[-1].start()


    def get_results(self, return_dict=False):
        """block all threads, sort by thread index, then return thread results

        Args:
            return_dict (bool): Return dict instead of list. Threaded
                functions' first arguments used as keys.
        """
        for thread in self._threads:
            thread.join()

        thread_data = []
        while not self._result_queue.empty():
            thread_data.append(self._result_queue.get())
        thread_data.sort(key=lambda thread_index: thread_index[0])

        if return_dict:
            return {first_arg: thread_return for
                _, first_arg, thread_return in thread_data}
        return [thread_return for _, _, thread_return in thread_data]
