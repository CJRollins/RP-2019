import tcod as libtcod

from enum import Enum

from gameStates import GameStates

from menus import inventory_menu

class RenderOrder(Enum):
        CORPSE = 1
        ITEM = 2
        ACTOR = 3

def render_all(con, panel, game_map, fov_map, fov_recompute, message_log, entities, screen_width, screen_height, colors, player, bar_width, panel_height, panel_y, mouse, game_state):

        if fov_recompute:
                #Draw tiles in map
                draw_map(con, game_map, fov_map, colors)

        entities_in_render_order = sorted(entities, key=lambda x: x.render_order.value)

        # Draw all entities in the list
        for entity in entities_in_render_order:
                draw_entity(con, entity, fov_map)

        libtcod.console_set_default_foreground(con, libtcod.white)
        libtcod.console_print_ex(con, 1, screen_height -2, libtcod.BKGND_NONE, libtcod.LEFT, 'HP: {0:02}/{1:02}' . format(player.fighter.hp, player.fighter.max_hp))

        libtcod.console_blit(con, 0, 0, screen_width, screen_height, 0, 0,0)

        libtcod.console_set_default_background(panel, libtcod.black)
        libtcod.console_clear(panel)

        # Print the game messages, one line at a time
        y = 1
        for message in message_log.messages:
                libtcod.console_set_default_foreground(panel, message.color)
                libtcod.console_print_ex(panel, message_log.x, y, libtcod.BKGND_NONE, libtcod.LEFT, message.text)
                y += 1

        render_bar(panel, 1, 1, bar_width, 'HP', player.fighter.hp, player.fighter.max_hp, libtcod.light_red, libtcod.darker_red)

        libtcod.console_set_default_foreground(panel, libtcod.light_gray)
        libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT,
            get_name_under_mouse(mouse, entities, fov_map))

        libtcod.console_blit(panel, 0, 0, screen_width, panel_height, 0, 0, panel_y)

        if game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
            if game_state == GameStates.SHOW_INVENTORY:
                inventory_title = 'Press the key next to an item to use it, or Esc to cancel. \n'
            else:
                inventory_title = 'Press the key next to an item to drop it, or Esc to cancel. \n'
            inventory_menu (con, inventory_title, player.inventory, 50, screen_width, screen_height)

def get_name_under_mouse(mouse, entities, fov_map):
    (x,y) = (mouse.cx, mouse.cy)

    names = [entity.name for entity in entities
        if entity.x == x and entity.y == y and libtcod.map_is_in_fov(fov_map, entity.x, entity.y)]
    names = ', '.join(names)

    return names.capitalize()

def render_bar(panel, x, y, total_width, name, value, maximum, bar_color, back_color):
        bar_width = int(float(value) / maximum * total_width)

        libtcod.console_set_default_background(panel, back_color)
        libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)

        libtcod.console_set_default_background(panel, bar_color)
        if bar_width > 0:
                libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)

        libtcod.console_set_default_foreground(panel, libtcod.white)
        libtcod.console_print_ex(panel, int(x + total_width / 2), y, libtcod.BKGND_NONE, libtcod.CENTER, '{0}: {1}/{2}'.format(name, value, maximum))

def draw_map(con, game_map, fov_map, colors):
        for y in range(game_map.height):
                for x in range(game_map.width):
                        visible = libtcod.map_is_in_fov(fov_map, x, y)
                        wall = game_map.tiles[x][y].block_sight

                        if visible:
                                if wall:
                                        libtcod.console_set_char_background(con, x, y, colors.get('light_wall'), libtcod.BKGND_SET)
                                else:
                                        libtcod.console_set_char_background(con, x, y, colors.get('light_ground'), libtcod.BKGND_SET)
                                game_map.tiles[x][y].explored = True
                        elif game_map.tiles[x][y].explored:
                                if wall:
                                        libtcod.console_set_char_background(con, x, y, colors.get('dark_wall'), libtcod.BKGND_SET)
                                else:
                                        libtcod.console_set_char_background(con, x, y, colors.get('dark_ground'), libtcod.BKGND_SET)


def draw_entity(con, entity, fov_map):
        if libtcod.map_is_in_fov(fov_map, entity.x, entity.y):
                libtcod.console_set_default_foreground(con, entity.color)
                libtcod.console_put_char(con, entity.x, entity.y, entity.char, libtcod.BKGND_NONE)

def clear_all(con, entities):
    for entity in entities:
        clear_entity(con, entity)

def clear_entity(con, entity):
    # Erase the character that represents this object
    libtcod.console_put_char(con, entity.x, entity.y, ' ', libtcod.BKGND_NONE)
