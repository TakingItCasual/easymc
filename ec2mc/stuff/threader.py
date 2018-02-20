from threading import Thread

class Threader(object):
    """Thread arbitrary number of functions, then block when results wanted.

    Attributes:
        threads (list): Threads of functions added with add_thread.
        results (list): Results to be returned by join_threads.
    """

    def __init__(self):
        self.threads = []
        self.results = []

    def add_thread(self, func, args):
        """Add a function to be threaded."""
        self.threads.append(Thread(target=func, args=(self.results, *args)))
        self.threads[-1].start()

    def join_threads(self):
        """Block for the threads' results."""
        for thread in self.threads:
            thread.join()
        return self.results
