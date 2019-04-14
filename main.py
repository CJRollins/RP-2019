import tcod as libtcod

from components.fighter import Fighter
from death_functions import kill_monster, kill_player
from entity import Entity, get_blocking_entities_at_location
from map_objects.game_map import GameMap
from gameStates import GameStates
from inputHandlers import handle_keys
from renderFunctions import render_all, clear_all, RenderOrder
from fov_functions import initialize_fov, recompute_fov

def main():
    SCREEN_WIDTH = 80
    SCREEN_HEIGHT = 50
    MAP_WIDTH = 80
    MAP_HEIGHT = 45
    
    ROOM_MAX_SIZE = 10
    ROOM_MIN_SIZE = 6
    MAX_ROOMS = 30
    MAX_MONSTERS_PER_ROOM = 3

    FOV_ALGORITHM = 0
    FOV_LIGHT_WALLS = True
    FOV_RADIUS = 10

    colors = {
        'dark_wall': libtcod.color.Color(0, 0, 100),
        'dark_ground': libtcod.color.Color(50,50,150),
        'light_wall': libtcod.color.Color(130, 110, 50),
        'light_ground': libtcod.color.Color(200, 180, 50)
    
    }

    fighter_component = Fighter(hp=30, defense=2, power=5)
    player = Entity(int(SCREEN_WIDTH / 2), int(SCREEN_HEIGHT / 2), '@', libtcod.white, 'Player', True, RenderOrder.ACTOR,  fighter_component)

    entities = [player]

    libtcod.console_set_custom_font('arial12x12.png', libtcod.FONT_TYPE_GRAYSCALE|libtcod.FONT_LAYOUT_TCOD)
    libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'RL - 2019', False,libtcod.RENDERER_SDL2)

    con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

    game_map = GameMap(MAP_WIDTH, MAP_HEIGHT)
    game_map.make_map(MAX_ROOMS, ROOM_MIN_SIZE, ROOM_MAX_SIZE, MAP_WIDTH, MAP_HEIGHT, player, entities, MAX_MONSTERS_PER_ROOM)

    fov_recompute = True

    fov_map = initialize_fov(game_map)

    key = libtcod.Key()
    mouse = libtcod.Mouse()

    gameState = GameStates.PLAYERS_TURN

    while not libtcod.console_is_window_closed():
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS, key, mouse)

        if fov_recompute:
            recompute_fov(fov_map, player.x, player.y, FOV_RADIUS, FOV_LIGHT_WALLS, FOV_ALGORITHM)

        render_all(con, game_map, fov_map, fov_recompute, entities, SCREEN_WIDTH, SCREEN_HEIGHT, colors, player)
        
        fov_recompute = False
        
        libtcod.console_flush()

        clear_all(con, entities)
        action = handle_keys(key)

        move = action.get('move')
        exit = action.get('exit')
        fullscreen = action.get('fullscreen')

        player_turn_results = []

        if move and gameState == GameStates.PLAYERS_TURN:
            dx, dy = move
            destination_x = player.x + dx
            destination_y = player.y + dy

            if not game_map.is_blocked(destination_x, player.y + dy):
                target = get_blocking_entities_at_location(entities, destination_x, destination_y)

                if target:
                    attack_results = player.fighter.attack(target)
                    player_turn_results.extend(attack_results)
                else:
                    player.move(dx, dy)
                    fov_recompute = True
            
            gameState = GameStates.ENEMY_TURN

        if exit:
            return True 

        if fullscreen:
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

        for player_turn_result in player_turn_results:
            message = player_turn_result.get('message')
            dead_entity = player_turn_result.get('dead')

            if message:
                print(message)
            
            if dead_entity:
                if dead_entity == player:
                    message, game_state = kill_player(dead_entity)
                else:
                    message = kill_monster(dead_entity)
                
                print(message)

        if gameState == GameStates.ENEMY_TURN:
            for entity in entities:
                if entity.ai:
                    enemy_turn_results = entity.ai.take_turn(player, fov_map, game_map, entities)

                    for enemy_turn_result in enemy_turn_results:
                        message = enemy_turn_result.get('message')
                        dead_entity = enemy_turn_result.get('dead')

                        if message:
                            print(message)
                        
                        if dead_entity:
                            if dead_entity == player:
                                message, gameState = kill_player(dead_entity)
                            else:
                                message = kill_monster(dead_entity)

                            print(message)

                            if gameState == GameStates.PLAYER_DEAD:
                                break

                    if gameState == GameStates.PLAYER_DEAD:
                        break

            else:
                gameState = GameStates.PLAYERS_TURN

if __name__ == '__main__':
    main()
