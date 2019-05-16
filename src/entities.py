import uuid
import numpy as np
from time import time


class NewEntity:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.alive = True
        self.image = None

    @staticmethod
    def touching(_e1, _e2):
        return (
            _e1.x1() < _e2.x2()
            and _e1.x2() > _e2.x1()
            and _e1.y1() < _e2.y2()
            and _e1.y2() > _e2.y1()
        )

    def includes(self, entity):
        _p2a = self.p2()
        _p2b = entity.p2()

        self.x = min(self.x, entity.x)
        self.y = min(self.y, entity.y)
        self.w = abs(self.x - max(_p2a[0], _p2b[0]))
        self.h = abs(self.y - max(_p2a[1], _p2b[1]))

    def set_image(self, frame):
        self.image = frame[self.y : self.y + self.h, self.x : self.x + self.w]

    def p1(self):
        return self.x, self.y

    def p2(self):
        return self.x + self.w, self.y + self.h

    def x1(self):
        return self.x

    def x2(self):
        return self.x + self.w

    def y1(self):
        return self.y

    def y2(self):
        return self.y + self.h

    def kill(self):
        self.alive = False

    def size(self):
        return self.w * self.h

    def scaled_p1(self, scale):
        return int(self.x / scale), int(self.y / scale)

    def scaled_p2(self, scale):
        return int((self.x + self.w) / scale), int((self.y + self.h) / scale)


class Entity:
    def __init__(self, x, y, image):
        self.last_active = time()
        self.first_active = self.last_active
        self.image_time = self.last_active
        self.x = x
        self.y = y
        self.r, self.g, self.b = np.round(255 * np.random.random_sample(3), 0)
        self.image = image
        self.best_image = image
        self.id = uuid.uuid4()

    def size(self):
        return self.image.size

    @staticmethod
    def contains_entity(entity1, entity2):
        x1, y1, w1, h1 = (
            entity1.x,
            entity1.y,
            entity1.image.shape[1],
            entity1.image.shape[0],
        )
        x2, y2, w2, h2 = (
            entity2.x,
            entity2.y,
            entity2.image.shape[1],
            entity2.image.shape[0],
        )

        a = x2 < x1 + w1
        b = y2 < y1 + h1
        c = x2 + w2 > x1
        d = y2 + h2 > y1

        return a and b and c and d

    def intersects_with(self, other_entity):
        return self.contains_entity(self, other_entity) or self.contains_entity(
            other_entity, self
        )

    def is_entity(self, other_entity):
        if self.intersects_with(other_entity):
            return True
        else:
            return False

    def update(self, entity):
        self.last_active = time()
        self.x = entity.x
        self.y = entity.y
        self.image = entity.image
        if (
            self.best_image.shape[0] < entity.image.shape[0]
            and self.best_image.shape[1] < entity.image.shape[1]
        ):
            self.best_image = entity.image
            self.image_time = self.last_active


class Statistic:
    def __init__(self):
        self.initialized_at = time()
        self.entity_count = 0
        self.interim_times = []

    def set_count(self, count):
        self.entity_count = count

    def add_time(self):
        self.interim_times.append(time())

    def print_line(self):
        line = "{},{}".format(self.entity_count, self.initialized_at)
        for interim_time in self.interim_times:
            line += ",{}".format(interim_time)
        line += "\n"
        return line
