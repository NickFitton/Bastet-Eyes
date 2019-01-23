import threading


class Subscriber(threading.Thread):
    def __init__(self, element_list, condition):
        self.element_list = element_list
        self.condition = condition
        threading.Thread.__init__(self)

    def run(self):
        pass
