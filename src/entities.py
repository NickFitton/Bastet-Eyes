import uuid
import numpy as np
from time import time


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
