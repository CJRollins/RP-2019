class Entity:
    """
    Generic Object Class
    """
    def __init__(self, x, y, char, color):
        self.x = x 
        self.y = y
        self.char = char
        self.color = color

    def move(self, dx, dy):
        # Move the entity by a given amount
        self.x += dx
        self.y += dy