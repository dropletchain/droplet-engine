from timeit import default_timer as timer


class TimeKeeper(object):
    def __init__(self):
        self.logged_times = {}
        self.cur_time = 0

    def start_clock(self):
        self.cur_time = timer()

    def stop_clock(self, log_name):
        # store times in milliseconds
        self.logged_times[log_name] = (timer() - self.cur_time) * 1000