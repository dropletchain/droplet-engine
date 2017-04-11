from timeit import default_timer as timer


class TimeKeeper(object):
    def __init__(self):
        self.logged_times = {}
        self.cur_time = 0
        self.start_time_log = {}
        self.curid = 0

    def start_clock(self):
        self.cur_time = timer()

    def stop_clock(self, log_name):
        # store times in milliseconds
        self.logged_times[log_name] = (timer() - self.cur_time) * 1000

    def start_clock_unique(self):
        id = self.curid
        self.curid += 1
        self.start_time_log[id] = timer()
        return id

    def stop_clock_unique(self,log_name, id):
        self.logged_times[log_name] = (timer() - self.start_time_log[id]) * 1000
        del self.start_time_log[id]

    def get_summary(self):
        summary = "[TIMES]"
        for key, value in self.logged_times.iteritems():
            summary += " %s: %s ms, " % (key, value)
        return summary[:-2]