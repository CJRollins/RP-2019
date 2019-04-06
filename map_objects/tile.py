class Tile:
    """
    A tile on a map.
        - Can be Blocked
        - Can block sight
    """

    def __init__(self, blocked, block_sight=None):
        self.blocked = blocked

        # By default, if a tile is blocked, it also blocks sight
        if block_sight is None:
            block_sight = blocked

        self.block_sight = block_sight

        self.explored = False