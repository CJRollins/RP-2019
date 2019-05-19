import tcod as libtcod

from components.fighter import Fighter
from components.inventory import Inventory
from death_functions import kill_monster, kill_player
from entity import Entity, get_blocking_entities_at_location
from map_objects.game_map import GameMap
from gameStates import GameStates
from inputHandlers import handle_keys, handle_mouse
from renderFunctions import render_all, clear_all, RenderOrder
from fov_functions import initialize_fov, recompute_fov
from gameMessages import Message, MessageLog

def main():
    SCREEN_WIDTH = 80
    SCREEN_HEIGHT = 50
    MAP_WIDTH = 80
    MAP_HEIGHT = 43

    BAR_WIDTH = 20
    PANEL_HEIGHT = 7
    PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT

    MESSAGE_X = BAR_WIDTH + 2
    MESSAGE_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
    MESSAGE_HEIGHT = PANEL_HEIGHT - 1

    ROOM_MAX_SIZE = 10
    ROOM_MIN_SIZE = 6
    MAX_ROOMS = 30
    MAX_MONSTERS_PER_ROOM = 3
    MAX_ITEMS_PER_ROOM = 2

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
    inventory_component = Inventory(26)
    player = Entity(int(SCREEN_WIDTH / 2), int(SCREEN_HEIGHT / 2), '@', libtcod.white, 'Player', True, RenderOrder.ACTOR,  fighter=fighter_component, inventory=inventory_component)

    entities = [player]

    libtcod.console_set_custom_font('arial12x12.png', libtcod.FONT_TYPE_GRAYSCALE|libtcod.FONT_LAYOUT_TCOD)
    libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'RL - 2019', False,libtcod.RENDERER_SDL2)

    con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
    panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)

    game_map = GameMap(MAP_WIDTH, MAP_HEIGHT)
    game_map.make_map(MAX_ROOMS, ROOM_MIN_SIZE, ROOM_MAX_SIZE, MAP_WIDTH, MAP_HEIGHT, player, entities, MAX_MONSTERS_PER_ROOM, MAX_ITEMS_PER_ROOM)

    fov_recompute = True

    fov_map = initialize_fov(game_map)

    message_log = MessageLog(MESSAGE_X, MESSAGE_WIDTH, MESSAGE_HEIGHT)

    key = libtcod.Key()
    mouse = libtcod.Mouse()

    gameState = GameStates.PLAYERS_TURN
    previous_game_state = gameState

    targeting_item = None

    while not libtcod.console_is_window_closed():
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)

        if fov_recompute:
            recompute_fov(fov_map, player.x, player.y, FOV_RADIUS, FOV_LIGHT_WALLS, FOV_ALGORITHM)

        render_all(con, panel, game_map, fov_map, fov_recompute, message_log, entities, SCREEN_WIDTH, SCREEN_HEIGHT, colors, player, BAR_WIDTH, PANEL_HEIGHT, PANEL_Y, mouse, gameState)

        fov_recompute = False

        libtcod.console_flush()

        clear_all(con, entities)
        action = handle_keys(key, gameState)
        mouse_action = handle_mouse(mouse)

        move = action.get('move')
        pickup = action.get('pickup')
        show_inventory = action.get('show_inventory')
        inventory_index = action.get('inventory_index')
        drop_inventory = action.get('drop_inventory')
        exit = action.get('exit')
        fullscreen = action.get('fullscreen')

        left_click = mouse_action.get('left_click')
        right_click = mouse_action.get('right_click')

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

        elif pickup and gameState == GameStates.PLAYERS_TURN:
            for entity in entities:
                if entity.item and entity.x == player.x and entity.y == player.y:
                    pickup_results = player.inventory.add_item(entity)
                    player_turn_results.extend(pickup_results)

                    break
                else:
                    message_log.add_message(Message('There is nothing here to pick up.', libtcod.yellow))

        if show_inventory:
            previous_game_state = gameState
            gameState = GameStates.SHOW_INVENTORY

        if drop_inventory:
            previous_game_state = gameState
            gameState = GameStates.DROP_INVENTORY

        if inventory_index is not None and previous_game_state != GameStates.PLAYER_DEAD and inventory_index < len(player.inventory.items):
            item = player.inventory.items[inventory_index]

            if gameState == GameStates.SHOW_INVENTORY:
                player_turn_results.extend(player.inventory.use(item, entities=entities, fov_map=fov_map))
            elif gameState == GameStates.DROP_INVENTORY:
                player_turn_results.extend(player.inventory.drop_item(item))

        if gameState == GameStates.TARGETING:
            if left_click:
                target_x, target_y = left_click

                item_use_results = player.inventory.use(targeting_item, entities = entities, fov_map = fov_map, target_x = target_x, target_y = target_y)
                player_turn_results.extend(item_use_results)
            elif right_click:
                player_turn_results.append({'targeting_cancelled': True})
        if exit:
            if gameState in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
                gameState = previous_game_state
            elif gameState == GameStates.TARGETING:
                player_turn_results.append({'targeting_cancelled': True})
            else:
                return True

        if fullscreen:
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

        for player_turn_result in player_turn_results:
            message = player_turn_result.get('message')
            dead_entity = player_turn_result.get('dead')
            item_added = player_turn_result.get('item_added')
            item_consumed = player_turn_result.get('consumed')
            item_dropped = player_turn_result.get('item_dropped')
            targeting = player_turn_result.get('targeting')
            targeting_cancelled = player_turn_result.get('targeting_cancelled')

            if message:
                message_log.add_message(message)

            if dead_entity:
                if dead_entity == player:
                    message, game_state = kill_player(dead_entity)
                else:
                    message = kill_monster(dead_entity)

                message_log.add_message(message)

            if item_added:
                entities.remove(item_added)

                gameState = GameStates.ENEMY_TURN

            if item_consumed:
                gameState = GameStates.ENEMY_TURN

            if targeting:
                previous_game_state = GameStates.PLAYERS_TURN
                gameState = GameStates.TARGETING

                targeting_item = targeting

                message_log.add_message(targeting_item.item.targeting_message)

            if targeting_cancelled:
                gameState = previous_game_state

                message_log.add_message(Message('Targeting cancelled'))
            if item_dropped:
                entities.append(item_dropped)

                gameState = GameStates.ENEMY_TURN


        if gameState == GameStates.ENEMY_TURN:
            for entity in entities:
                if entity.ai:
                    enemy_turn_results = entity.ai.take_turn(player, fov_map, game_map, entities)

                    for enemy_turn_result in enemy_turn_results:
                        message = enemy_turn_result.get('message')
                        dead_entity = enemy_turn_result.get('dead')

                        if message:
                            message_log.add_message(message)

                        if dead_entity:
                            if dead_entity == player:
                                message, gameState = kill_player(dead_entity)
                            else:
                                message = kill_monster(dead_entity)

                            message_log.add_message(message)

                            if gameState == GameStates.PLAYER_DEAD:
                                break

                    if gameState == GameStates.PLAYER_DEAD:
                        break

            else:
                gameState = GameStates.PLAYERS_TURN

if __name__ == '__main__':
    main()
