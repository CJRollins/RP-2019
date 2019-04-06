import tcod as libtcod

from entity import Entity
from map_objects.game_map import GameMap
from inputHandlers import handle_keys
from renderFunctions import render_all, clear_all

def main():
    SCREEN_WIDTH = 80
    SCREEN_HEIGHT = 50
    MAP_WIDTH = 80
    MAP_HEIGHT = 45
    
    ROOM_MAX_SIZE = 10
    ROOM_MIN_SIZE = 6
    MAX_ROOMS = 30

    colors = {
        'dark_wall': libtcod.color.Color(0, 0, 100),
        'dark_ground': libtcod.color.Color(50,50,150)
    }

    player = Entity(int(SCREEN_WIDTH / 2), int(SCREEN_HEIGHT / 2), '@', libtcod.white)

    entities = [player]

    libtcod.console_set_custom_font('arial12x12.png', libtcod.FONT_TYPE_GRAYSCALE|libtcod.FONT_LAYOUT_TCOD)
    libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'RL - 2019', False)

    con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

    game_map = GameMap(MAP_WIDTH, MAP_HEIGHT)
    game_map.make_map(MAX_ROOMS, ROOM_MIN_SIZE, ROOM_MAX_SIZE, MAP_WIDTH, MAP_HEIGHT, player)

    key = libtcod.Key()
    mouse = libtcod.Mouse()

    while not libtcod.console_is_window_closed():
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS, key, mouse)

        render_all(con, game_map, entities, SCREEN_WIDTH, SCREEN_HEIGHT, colors)
        
        libtcod.console_flush()

        clear_all(con, entities)
        action = handle_keys(key)

        move = action.get('move')
        exit = action.get('exit')
        fullscreen = action.get('fullscreen')

        if move:
            dx, dy = move
            if not game_map.is_blocked(player.x + dx, player.y + dy):
                player.move(dx, dy)

        if exit:
            return True 

        if fullscreen:
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

if __name__ == '__main__':
    main()
