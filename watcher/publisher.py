import threading


class Publisher(threading.Thread):
    def __init__(self, element_list, condition):
        self.condition = condition
        self.element_list = element_list
        threading.Thread.__init__(self)

    def run(self):
        pass
