import pygame as pg
from sys import exit
from pytmx.util_pygame import load_pygame
from pathlib import Path
from collections import deque
import random

#-------------------GLOBAL GAME VARIABLES AND CONSTANTS-------------------

game_window_width = 1280
game_window_height = 640
resizing_factor = 2

which_text_screen = ['intro first', 'intro second', 'after first stage',
                    'after 8', 'end screen', 'sec first', 'sec second',
                    'sec third']
which_map_is_next = [f'map_{x}' for x in range(1,10)]
# index starts from 0!
index_of_current_map = 0
map_loaded = False
game_state = 'resolution selection'

mute_button_state = False
back_to_menu_pressed = False
left_mouse_button_pressed = None

PLAYER_SHOOTING_SPEED = 200 # in milliseconds
MAX_PLAYER_BULLETS = 2
HEAT_DAMAGE_RESISTANCE = 6000 # in milliseconds
INVINCIBILITY_TIME = 3000   # in milliseconds
PLAYER_LIVES = 5
STARTING_PLAYER_HEALTH = 2

LASER_BEAM_FADE_TIME = 1000 # in milliseconds
LASER_CHARGE_TIME = 4200 # in milliseconds
LASER_BEAM_DAMAGE = 2
GRENADE_DAMAGE = 1
ENEMY_BULLET_DAMAGE = 1
SOUNDWAVE_DAMAGE = 1
LAVA_DAMAGE = 1

AVERAGE_SHIELD_SPAWN_TIME = 4  # minutes
average_shield_spawn_time = int(AVERAGE_SHIELD_SPAWN_TIME*60*60)
SHIELD_PLUS_ARMOUR = 3
SHIELD_DESPAWN_TIME = 10000 # milliseconds
MAXIMUM_SHIELD_SPAWN_RADIUS = 10 # in tiles

COMM_BUILDINGS_HITPOINTS = 3

MAIN_BASE_WAVE_SHOOT_TIMER = 3500 # milliseconds
MAIN_BASE_HEALTH = 50

first_stage_to_be_loaded = True
is_R_set = False
is_m_pressed = False
is_c_pressed = False
stage_5_one_building_down = False
stage_5_switch_flag = False
stage_9_buildings_down = False
stage_9_switch_flag = False

# enemy numbers (type 1,2,3,4,5) on the various maps (1,2,..,9)
enemy_numbers = [
                [15, 0, 0, 0, 0],
                [12, 10, 0, 0, 0],
                [12, 12, 0, 0, 0],
                [10, 14, 8, 0, 0],
                [10, 8, 12, 0, 0],
                [9, 8, 7, 7, 0],
                [8, 8, 6, 8, 0],
                [8, 8, 6, 4, 4],
                [6, 12, 8, 8, 8],
]

# probablity distributions for the shooting times of the enemies
TYPE_1_SHOOTING = abs(int(random.gauss(mu=2.6,sigma=1.3)*1000))
TYPE_2_SHOOTING = abs(int(random.gauss(mu=3.0,sigma=1.4)*1000))
TYPE_3_SHOOTING = abs(int(random.gauss(mu=3.2,sigma=1.6)*1000))
TYPE_4_SHOOTING = abs(int(random.gauss(mu=4.1,sigma=1.5)*1000))
TYPE_5_SHOOTING = abs(int(random.gauss(mu=10,sigma=1.2)*1000))

maximum_number_of_enemies = 0
enemies_to_be_spawned = []
spawned_enemy_numbers = [0, 0, 0, 0, 0]
enemy_types_to_be_spawned = []
enemy_numbers_current_map = []
last_spawn_time = 0
next_spawn_time = 0
destroyed_overall_enemies = [0,0,0,0,0]
extra_life_counter = 0
objectives_destroyed = 0

after_win_screen_timer = 0
credits_screen_cleaner = False
credits_timer = 0
credits_timer_switch = False


#---------------------------------FUNCTIONS----------------------------------

def variables_that_depend_on_resolution():
    """The collection of all the global variables and instances that depend on
    our selected screen (window) resolution.
    """

    global R
    global PLAYER_SPEED
    global PLAYER_BULLET_SPEED
    global DEFAULT_HEAT_BAR_WIDTH
    global maximum_shield_spawn_radius
    global MAIN_BASE_PROJECTILE_SPEED
    global PROJECTILE_HITBOX
    global enemy_infos
    global is_R_set
    global text_displayer
    global dist
    global distance

    # forgot to scale the enemy and bullet speeds so I added R
    # (it's only one letter so e.g. the enemy_info won't look like a mess)
    R = int(resizing_factor/2)
    # if the enemy is closer to the destination than dist we set a new goal and 
    # calculate a new path to it
    dist = 2*int(resizing_factor/2)
    distance = dist**2
    PLAYER_SPEED = 2*R
    PLAYER_BULLET_SPEED = 5*R
    DEFAULT_HEAT_BAR_WIDTH = 30*resizing_factor
    maximum_shield_spawn_radius = 10*16*resizing_factor
    MAIN_BASE_PROJECTILE_SPEED = 2*R
    # the bullets are 2x2 pixels big, this number determines how much bigger
    # their hitboxes will be; we change the size with the inflate() method and
    # the number in the brackets is the one be changed if needed e.g. this 1
    # will give the 2x2 bullets a 4x4 hitbox around them
    PROJECTILE_HITBOX = (1)*resizing_factor*2
    # dictionary for the enemy instantiation (the actual speed for type 4, 5 will
    # be 0.5 but if we give non-integer values here it breaks their movement)
    enemy_infos = [
                    {'health': 1, 'speed': 2*R, 'bullet speed': 3*R},
                    {'health': 2, 'speed': 1*R, 'bullet speed': 2*R},
                    {'health': 3, 'speed': 1*R, 'bullet speed': 2*R},
                    {'health': 4, 'speed': 1*R, 'bullet speed': 2*R},
                    {'health': 4, 'speed': 1*R, 'bullet speed': None},
    ]
    text_displayer = StoryScreensDisplayer()
    is_R_set = True


def state_manager():
    """Manages the states of the game (title screen, stages etc.)."""

    if game_state == 'resolution selection':
        resolution_selection()
    elif game_state == 'start menu':
        if not is_R_set:
            variables_that_depend_on_resolution()
        start_menu_screen()
    elif game_state == 'manual screen':
        manual_screen()
    elif game_state in which_text_screen:
        if not text_displayer.text_read_in:
            text_displayer.text_reader()
        text_displayer.text_skip_checker()
    elif game_state in which_map_is_next:
        if not map_loader_instance.map_loaded:
            map_loader_instance.map_loader_instance()
        else:
            group_update_and_draw()
            lose_win_checker()
            shield_spawner()
            enemy_spawn_manager()
            side_panel()
    elif game_state == 'summary screen':
        summary_screen()
    elif game_state == 'lose screen':
        lose_screen()
    elif game_state == 'win wait':
        win_wait()
        side_panel()
    elif game_state == 'credits':
        credits()
        

def group_update_and_draw():
    """Updates the various sprite groups and also draws them onto the screen.
    Checks the condition for and runs the exclusive stage 5 function.
    """

    # I think updating everything before drawing anything makes more sense but
    # here I had to switch them because of the (lava) heat damage bar; the
    # update method draws the surface of it so if we draw everything after the
    # updates we can't see it and I don't want to separate it into a different
    # class or function
    if index_of_current_map == 8:
    
        walkable_group.draw(screen)
        water_group.draw(screen)
        lava_group.draw(screen)
        
        spawn_animation_group.draw(screen)
        objectives_group.draw(screen)
        main_base_center_group.draw(screen)
        enemies_group.draw(screen)
        player_group.draw(screen)
        main_base_group.sprite.soundwave_group.draw(screen)
        main_base_group.sprite.bullet_group.draw(screen)
        for sprite in enemies_group:
            if sprite.type == 5:
                sprite.laser_group.draw(screen)
        wall_group.draw(screen)
        shield_group.draw(screen)
        tank1234_bullet_group.draw(screen)
        main_base_group.draw(screen)
        player_bullets_group.draw(screen)
        explosions_and_collapse_group.draw(screen)

        player_group.update()
        player_bullets_group.update()
        objectives_group.update()
        tank1234_bullet_group.update()
        explosions_and_collapse_group.update()
        enemies_group.update()
        shield_group.update()
        water_group.update()
        lava_group.update()
        spawn_animation_group.update()
        main_base_group.update()

    # this is the same code as in the above if statement excluding the drawing
    # and updating of the "boss building", we only want to do that on the last
    # stage; because the drawing order matters we either do it like this or
    # add a bunch of if statements to the code below which IMO only makes it
    # look more unreadable
    else:
        if index_of_current_map == 4:
            stage_5_switcheroo()
        
        walkable_group.draw(screen)
        water_group.draw(screen)
        lava_group.draw(screen)
        
        spawn_animation_group.draw(screen)
        objectives_group.draw(screen)
        enemies_group.draw(screen)
        player_group.draw(screen)
        for sprite in enemies_group:
            if sprite.type == 5:
                sprite.laser_group.draw(screen)
        wall_group.draw(screen)
        shield_group.draw(screen)
        tank1234_bullet_group.draw(screen)
        player_bullets_group.draw(screen)
        explosions_and_collapse_group.draw(screen)

        player_group.update()
        player_bullets_group.update()
        objectives_group.update()
        tank1234_bullet_group.update()
        explosions_and_collapse_group.update()
        enemies_group.update()
        shield_group.update()
        water_group.update()
        lava_group.update()
        spawn_animation_group.update()
        
    
def lose_win_checker():
    """Checks if we've won the map or lost the game. Also increases the next
    map index and changes the game state.
    """

    global game_state
    global index_of_current_map
    global stage_9_buildings_down

    if index_of_current_map == 8:
        if objectives_destroyed == len(objectives_group) and (stage_9_buildings_down == False):
            stage_9_buildings_down = True
            stage_9_switcheroo()
        if player_group.sprite.lives < 1:
            game_state = 'lose screen'

    else:
        if objectives_destroyed == len(objectives_group):
            game_state = 'summary screen'
            index_of_current_map += 1
            after_stage_cleaner()
            map_loader_instance.map_loaded = False
        if player_group.sprite.lives < 1:
            game_state = 'lose screen'


def after_stage_cleaner():
    """After each stage prepares everything (groups, variables, instances) for
    the next stage.
    """

    global maximum_number_of_enemies
    global objectives_destroyed

    screen.fill('Black')

    walkable_group.empty()
    probable_goal_tile_group.empty()
    wall_group.empty()
    water_group.empty()
    lava_group.empty()
    objectives_group.empty()
    player_bullets_group.empty()
    explosions_and_collapse_group.empty()
    enemies_group.empty()
    shield_group.empty()
    tank1234_bullet_group.empty()
    spawn_animation_group.empty()
    main_base_group.empty()
    main_base_center_group.empty()

    maximum_number_of_enemies = 0
    objectives_destroyed = 0

    map_loader_instance.reset()
    sound_manager.after_stage_reset()


def resolution_selection():
    """Function that draws and manages the startup screen
    (resolution selection).
    """

    global game_window_height
    global game_window_width
    global screen
    global resizing_factor
    global game_state

    # drawing the logo and the buttons
    game_font = pg.font.Font('font/data-latin.ttf', 150)
    game_logo = game_font.render('SIEGE',False,'White')
    game_logo_rect = game_logo.get_rect(topleft = (464,120))
    pg.draw.rect(screen,'White',game_logo_rect,3)
    screen.blit(game_logo,(460,120))

    game_font = pg.font.Font('font/data-latin.ttf', 40)
    resolution_text_surf = game_font.render('Choose a resolution!',False,'White')
    screen.blit(resolution_text_surf,(460,380))

    game_font = pg.font.Font('font/data-latin.ttf', 30)
    resolution_button_1280_surf = game_font.render(
        '1280 x 640 (current)',False,'White')
    resolution_button_1280_rect = resolution_button_1280_surf.get_rect(
        topleft = (300,500))
    screen.blit(resolution_button_1280_surf,(300,500))

    resolution_button_2560_surf = game_font.render('2560 x 1280',False,'White')
    resolution_button_2560_rect = resolution_button_2560_surf.get_rect(
        topleft = (770,500))
    screen.blit(resolution_button_2560_surf,(770,500))

    game_font = pg.font.Font('font/data-latin.ttf', 40)
    quit_button_surf = game_font.render('quit',False,'White')
    quit_button_rect = quit_button_surf.get_rect(topleft = (610,560))
    screen.blit(quit_button_surf,(610,560))
    
    # we can choose resolution or quit
    mouse_position = pg.mouse.get_pos()
    if resolution_button_1280_rect.collidepoint(mouse_position):
        pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
        if left_mouse_button_pressed:
            sound_manager.button_click_sound.play()
            game_state = 'start menu'
            screen.fill('Black')
            pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)
    elif resolution_button_2560_rect.collidepoint(mouse_position):
        pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
        if left_mouse_button_pressed:
            sound_manager.button_click_sound.play()
            resizing_factor = 4
            game_window_width = 2560
            game_window_height = 1280
            screen = pg.display.set_mode((game_window_width, game_window_height))
            game_state = 'start menu'
            screen.fill('Black')
            pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)
    elif quit_button_rect.collidepoint(mouse_position):
        pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
        if left_mouse_button_pressed:
            pg.quit()
            exit()
    else:
        pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)


def start_menu_screen():
    """Manages and draws the start menu screen."""

    global game_state
    global mute_button_state

    # drawing the logo and the buttons
    game_font = pg.font.Font('font/data-latin.ttf', 150*int(resizing_factor/2))
    game_logo = game_font.render('SIEGE',False,'White')
    game_logo_rect = game_logo.get_rect(
        topleft = (464*int(resizing_factor/2),120*int(resizing_factor/2)))
    pg.draw.rect(screen,'White',game_logo_rect,3*int(resizing_factor/2))
    screen.blit(game_logo,(460*int(resizing_factor/2),120*int(resizing_factor/2)))

    game_font = pg.font.Font('font/data-latin.ttf', 40*int(resizing_factor/2))
    start_game_button_surf = game_font.render('start game',False,'White')
    start_game_button_rect = start_game_button_surf.get_rect(
        topleft = (555*int(resizing_factor/2),340*int(resizing_factor/2)))
    screen.blit(start_game_button_surf,
                (555*int(resizing_factor/2),340*int(resizing_factor/2)))

    manual_button_surf = game_font.render('manual',False,'White')
    manual_button_rect = manual_button_surf.get_rect(
        topleft= (595*int(resizing_factor/2),410*int(resizing_factor/2)))
    screen.blit(manual_button_surf,
                (595*int(resizing_factor/2),410*int(resizing_factor/2)))

    quit_button_surf = game_font.render('quit',False,'White')
    quit_button_rect = quit_button_surf.get_rect(
        topleft = (610*int(resizing_factor/2),560*int(resizing_factor/2)))
    screen.blit(quit_button_surf,
                (610*int(resizing_factor/2),560*int(resizing_factor/2)))


    if mute_button_state:
        mute_music_button_surf = game_font.render('unmute music',False,'White')
        mute_music_button_rect = mute_music_button_surf.get_rect(
            topleft= (535*int(resizing_factor/2),480*int(resizing_factor/2)))
        screen.blit(mute_music_button_surf,
                    (535*int(resizing_factor/2),480*int(resizing_factor/2)))
    elif not mute_button_state:
        mute_music_button_surf = game_font.render('mute music',False,'White')
        mute_music_button_rect = mute_music_button_surf.get_rect(
            topleft= (555*int(resizing_factor/2),480*int(resizing_factor/2)))
        screen.blit(mute_music_button_surf,
                    (555*int(resizing_factor/2),480*int(resizing_factor/2)))

    # here we can start a new game, read the manual, mute the music or quit
    mouse_position = pg.mouse.get_pos()
    if start_game_button_rect.collidepoint(mouse_position):
        pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
        if left_mouse_button_pressed:
            sound_manager.button_click_sound.play()
            game_state = 'intro first'
            screen.fill('Black')
            pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)
    elif manual_button_rect.collidepoint(mouse_position):
        pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
        if left_mouse_button_pressed:
            sound_manager.button_click_sound.play()
            game_state = 'manual screen'
            screen.fill('Black')
            pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)
    elif mute_music_button_rect.collidepoint(mouse_position):
        pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
        if left_mouse_button_pressed:
            sound_manager.button_click_sound.play()
            mute_button_state = not mute_button_state
            sound_manager.muting_music()
            screen.fill('Black')
    elif quit_button_rect.collidepoint(mouse_position):
        pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
        if left_mouse_button_pressed:
            pg.quit()
            exit()
    else:
        pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)
        

def manual_screen():
    """Manages and draws the manual screen."""

    global game_state

    # drawing the lines (controls section)
    game_font = pg.font.Font('font/data-latin.ttf', 25*int(resizing_factor/2))
    line = game_font.render("Controls:",False,(65,105,225))
    screen.blit(line,(100*int(resizing_factor/2),60*int(resizing_factor/2)))
    line = game_font.render(
        "- Use the arrow keys for movement. You can shoot with the spacebar.",
        False,'White')
    screen.blit(line,(100*int(resizing_factor/2),90*int(resizing_factor/2)))
    line = game_font.render(
        "- Press the C key during the story screens to display them in "+ 
        "full instantly.",False,'White')
    screen.blit(line,(100*int(resizing_factor/2),120*int(resizing_factor/2)))
    line = game_font.render(
        "- You can mute/un-mute the music while on a stage with the M key.",
        False,'White')
    screen.blit(line,(100*int(resizing_factor/2),150*int(resizing_factor/2)))
    line = game_font.render("- To click on any button use the mouse.",
    False,'White')
    screen.blit(line,(100*int(resizing_factor/2),180*int(resizing_factor/2)))
    line = game_font.render(
        "- Between stages you'll have to press the C key to begin the next stage.",
        False,'White')
    screen.blit(line,(100*int(resizing_factor/2),210*int(resizing_factor/2)))

    # drawing the lines and an image (objectives section)
    line = game_font.render("Objectives:",False,(65,105,225))
    screen.blit(line,(100*int(resizing_factor/2),250*int(resizing_factor/2)))
    line = game_font.render(
        "There is only one. Destroy every communications station:",False,'White')
    screen.blit(line,(100*int(resizing_factor/2),280*int(resizing_factor/2)))
    image = pg.image.load('images/other/comm_station_manual.png').convert_alpha()
    image = pg.transform.scale2x(image)
    image = pg.transform.scale2x(image)
    if resizing_factor == 4:
        image = pg.transform.scale2x(image)
    screen.blit(image,(820*int(resizing_factor/2),255*int(resizing_factor/2)))

    # drawing the lines (tips & tricks section)
    line = game_font.render("Tips & tricks:",False,(65,105,225))
    screen.blit(line,(100*int(resizing_factor/2),320*int(resizing_factor/2)))
    line = game_font.render(
        "- Look out for a randomly appearing upgrade. Be quick, "+ 
        "it won't stay forever!",False,'White')
    screen.blit(line,(100*int(resizing_factor/2),350*int(resizing_factor/2)))
    line = game_font.render(
        "- Be careful around lava. Your vehicle can't endure the extreme heat "+ 
        "for a long time.",False,'White')
    screen.blit(line,(100*int(resizing_factor/2),380*int(resizing_factor/2)))
    line = game_font.render(
        "- You can use the collision system to your advantage if you are "+ 
        "skillful enough, because",False,'White')
    screen.blit(line,(100*int(resizing_factor/2),410*int(resizing_factor/2)))
    line = game_font.render("- vehicles can go through each other",False,'White')
    screen.blit(line,(150*int(resizing_factor/2),440*int(resizing_factor/2)))
    line = game_font.render(
        "- certain projectiles can collide with each other. " +
        "Mostly yours with the enemy ones.",False,'White')
    screen.blit(line,(150*int(resizing_factor/2),470*int(resizing_factor/2)))
    line = game_font.render(
        "- There might be a secret somewhere on one of the stages.",
        False,'Yellow')
    screen.blit(line,(100*int(resizing_factor/2),500*int(resizing_factor/2)))

    # drawing the back button
    game_font = pg.font.Font('font/data-latin.ttf', 40*int(resizing_factor/2))
    back_button_surf = game_font.render('back',False,'White')
    back_button_rect = back_button_surf.get_rect(
        topleft = (610*int(resizing_factor/2),560*int(resizing_factor/2)))
    screen.blit(back_button_surf,
                (610*int(resizing_factor/2),560*int(resizing_factor/2)))

    # making the button interactive
    mouse_position = pg.mouse.get_pos()
    if back_button_rect.collidepoint(mouse_position):
        pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
        if left_mouse_button_pressed:
            sound_manager.button_click_sound.play()
            game_state = 'start menu'
            screen.fill('Black')
    else:
        pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)


def neighbors(current):
    """Determines the neighbors of a tile."""

    neighbors = []
    # North->West->South->East
    directions = [[0,-1],[-1,0],[0,1],[1,0]]
    for direction in directions:
        direction = (direction[0] + current[0],direction[1] + current[1])
        if (0 <= direction[0] <= map_loader_instance.background_tile_layer.width-1 and
            0 <= direction[1] <= map_loader_instance.background_tile_layer.height-1):
            if direction in map_loader_instance.tile_grid:
                neighbors.append(direction)
    return neighbors

    
def pathfinding(start_location,goal_location):
    """Calculates the shortest path from start to finish and returns it.
    It's a simple Breadth first search algorithm.
    """

    start = (start_location[0]//(16*resizing_factor),
            start_location[1]//(16*resizing_factor))
    goal = (goal_location[0]//(16*resizing_factor),
            goal_location[1]//(16*resizing_factor))
    current = (0,0)

    frontier = deque()
    came_from = {}
    frontier.append(start)
    # key: current vertex; value: the previous vertex e.g. if we stepped
    # from A (x_A,y_A) to B (x_B,y_B) then (x_B,y_B): (x_A,y_A)
    came_from[start] = None

    while frontier:
        current = frontier.popleft()
        if current == goal:
            break
    
        for neighbor in neighbors(current):
            if neighbor not in came_from:
                frontier.append(neighbor)
                came_from[neighbor] = current

    # now we have the path but from the goal to our start, so we have to
    # reverse it
    path = deque()
    current = goal

    while current != start:
        path.append(current)
        current = came_from[current]

    path = deque(
                ((point[0]+0.5)*16*resizing_factor,
                (point[1]+0.5)*16*resizing_factor) for point in path)

    path.reverse()
    return path


def inaccesible_tile_separator(screen_width,screen_height):
    """The point of this function is to separate the tiles which we could move on
    but are inacessible. We need this so the pathfinding won't break down.
    """

    # in short: the stages here are 33 horizontal and 20 vertical tiles big;
    # we take the middle one of the vertical tile lines (33/2) and then
    # calculate how many tiles we can reach on the stage from each tile in
    # said vertical tile line (20 here); because we only have small patches
    # of unreachable land there will be at least 1 tile among the 20 from where
    # we can reach the walkable ones; now we have for each tile in said vertical
    # line its coordinates and the number of tiles we can reach starting
    # from there; next we take the maximum of the latter values, set the start
    # position to the coordinates of the tile the maximum value belongs to and
    # calculate again how many tiles we can reach but now from only this tile,
    # this will give us the reachable set of tiles
    # this should work if we have: 1. islands smaller than half the map and
    # 2. the enemies can't spawn (move) on them
    # a simple drawing instead of this confusing rambling would explain it easier
    # but whatever
    frontier = deque()
    visited = []
    y_of_first_tile = 0
    y_of_last_tile = screen_height
    tile_numbers = []

    while y_of_first_tile <= y_of_last_tile-1:
        start = (screen_width//2,y_of_first_tile)
        frontier.append(start)
        while frontier:
            current = frontier.popleft()
        
            for neighbor in neighbors(current):
                if neighbor not in visited:
                    frontier.append(neighbor)
                    visited.append(neighbor)
        tile_numbers.append(len(visited))
        y_of_first_tile += 1
        visited.clear()

    start = (screen_width//2,tile_numbers.index(max(tile_numbers)))
    frontier.append(start)
    while frontier:
        current = frontier.popleft()
        cX = current[0]*16*resizing_factor
        cY = current[1]*16*resizing_factor
        for sprite in walkable_group:
            x = sprite.rect.x
            y = sprite.rect.y
            if cX == x and cY == y:
                probable_goal_tile_group.add(sprite)
    
        for neighbor in neighbors(current):
            if neighbor not in visited:
                frontier.append(neighbor)
                visited.append(neighbor)


def shield_spawner():
    """Manages the random spawning of the shield upgrade."""

    shield_spawn_chance = random.randint(1,average_shield_spawn_time)
    winning_number = 13
    if shield_spawn_chance == winning_number:
        location = pg.sprite.Group()
        for tile in probable_goal_tile_group:
            if ((player_group.sprite.rect.centerx-tile.rect.centerx)**2+
                    (player_group.sprite.rect.centery-tile.rect.centery)**2 <=
                    maximum_shield_spawn_radius**2):
                location.add(tile)
        rolled_location = random.choice(location.sprites())
        location.empty()
        shield_group.add(ShieldPowerUp(rolled_location.rect.centerx,
            rolled_location.rect.centery))
        

def enemy_spawn_manager():
    """Manages the enemy spawning."""

    global last_spawn_time
    global next_spawn_time
    global spawned_enemy_numbers
    global enemy_types_to_be_spawned
    global enemies_to_be_spawned

    if not len(enemies_group) < maximum_number_of_enemies:
        return
    # for index in [index for index in range(0,5)]:
    enemies_to_be_spawned = [0,0,0,0,0]
    enemy_types_to_be_spawned = []
    for index in [index for index in range(0,5)]:
        enemies_to_be_spawned[index] = (enemy_numbers_current_map[index]
                                        - spawned_enemy_numbers[index])
        if enemies_to_be_spawned[index] != 0:
            enemy_types_to_be_spawned.append(index+1)

    # we need < instead of <= if we want the first 70% of them spawned in 800 
    # intervals then randomly the rest (with <= the first 70% AND the one after
    # will be spawned in 800)
    if (len(enemies_group) < int(maximum_number_of_enemies*0.7) and
        global_time_ms-last_spawn_time > 800):
        next_spawn_time = 0
        last_spawn_time = global_time_ms
        rolled_tank_type = random.choice(enemy_types_to_be_spawned)
        spawn_location = random.choice(
            map_loader_instance.enemy_spawn_locations)
        spawn_animation_group.add(SpawnAnimation(
            rolled_tank_type,enemy_infos[rolled_tank_type-1],spawn_location))
        spawned_enemy_numbers[rolled_tank_type-1] += 1

    elif (int(maximum_number_of_enemies*0.7) <= len(enemies_group) 
                                            < maximum_number_of_enemies):
        if global_time_ms-last_spawn_time > next_spawn_time:
            if next_spawn_time == 0:
                next_spawn_time = abs(int(random.gauss(mu=8.0,sigma=2.5)*1000))
                return
            next_spawn_time = abs(int(random.gauss(mu=8.0,sigma=2.0)*1000))
            last_spawn_time = global_time_ms
            rolled_tank_type = random.choice(enemy_types_to_be_spawned)
            spawn_location = random.choice(
                map_loader_instance.enemy_spawn_locations)
            spawn_animation_group.add(
                SpawnAnimation(rolled_tank_type,
                                enemy_infos[rolled_tank_type-1],
                                spawn_location))
            spawned_enemy_numbers[rolled_tank_type-1] += 1
    

def bullet_collide(first,second):
    """Checks if two hitboxes of two bullets collide."""
    return first.hitbox.colliderect(second.hitbox) 


def player_obstacle_collision(player,obstacle):
    """Checks if the player's hitbox collided with an obstacle rectangle."""
    return player.hitbox.colliderect(obstacle.rect)


def stage_5_switcheroo():
    """"Switches a number of dirt tiles to walls after one of the comm stations
    has been destroyed on stage 5.
    """

    global stage_5_switch_flag
    global stage_5_one_building_down

    if not stage_5_one_building_down:
        return 
    image = pg.image.load('stages/wall.png').convert_alpha()
    for sprite in probable_goal_tile_group:
        if sprite.rect.y == 9*16*resizing_factor:
            if (sprite.rect.x == 27*16*resizing_factor or
                    sprite.rect.x == 28*16*resizing_factor or
                    sprite.rect.x == 29*16*resizing_factor):
                
                # the class will upscale the tiles so we have to divide
                # the coordinates
                x = int(sprite.rect.x/(16*resizing_factor))
                y = int(sprite.rect.y/(16*resizing_factor))
                map_loader_instance.tile_grid.remove((x,y))
                wall_group.add(RectanglesFromTiles(x,y,image))
                probable_goal_tile_group.remove(sprite)
                walkable_group.remove(sprite)

    # to avoid bugs with the pathfinding we set a new goal tile for every enemy
    # and get a new path for it
    for enemy in enemies_group:
        enemy.pathfinding_reset()
    stage_5_switch_flag = True
    stage_5_one_building_down = False


def stage_9_switcheroo():
    """"Switches a number of wall tiles to dirt after all of the comm stations
    get destroyed on stage 9.
    """
   
    image = pg.image.load('stages/dirt.png').convert_alpha()
    for sprite in wall_group:
        if sprite.rect.x == 29*16*resizing_factor:
            if (sprite.rect.y == 0*16*resizing_factor or
                    sprite.rect.y == 1*16*resizing_factor or
                    sprite.rect.y == 18*16*resizing_factor or
                    sprite.rect.y == 19*16*resizing_factor):
                
                # the class will upscale the tiles so we have to divide
                # the coordinates
                x = int(sprite.rect.x/(16*resizing_factor))
                y = int(sprite.rect.y/(16*resizing_factor))
                map_loader_instance.tile_grid.append((x,y))
                wall_group.remove(sprite)
                probable_goal_tile_group.add(RectanglesFromTiles(x,y,image))
                walkable_group.add(RectanglesFromTiles(x,y,image))

    # to avoid bugs with the pathfinding we set a new goal tile for every enemy
    # and get a new path for it
    for enemy in enemies_group:
        enemy.pathfinding_reset()


def stage_9_tile_correcton():
    """To make the boss fight easier the enemies won't move onto the tiles
    beyond the long wall on the right side of the stage.
    """

    for tile in probable_goal_tile_group:
        if ((tile.rect.x//(16*resizing_factor) in range(30,33)) and
                (tile.rect.y//(16*resizing_factor) in range(0,20))):
            probable_goal_tile_group.remove(tile)


def side_panel():
    """Draws and maanges the side panel on every stage."""

    global back_to_menu_pressed
    global game_state

    # first we have to create/draw the whole (black) background of the side
    # panel because the projectiles that leave on right side of the stage can
    # be seen for a while before they get destroyed
    side_panel_background = pg.Rect(
        528*resizing_factor,0,112*resizing_factor,320*resizing_factor)
    pg.draw.rect(screen,'Black',side_panel_background)

    # drawing the logo at the top
    game_font = pg.font.Font('font/data-latin.ttf', 80*int(resizing_factor/2))
    game_logo = game_font.render('SIEGE',False,'White')
    game_logo_rect = game_logo.get_rect(
        topleft = (1071*int(resizing_factor/2),50*int(resizing_factor/2)))
    pg.draw.rect(screen,'White',game_logo_rect,2*int(resizing_factor/2))
    screen.blit(game_logo,
                (1069*int(resizing_factor/2),50*int(resizing_factor/2)))

    # drawing the horizontal line below the logo
    pg.draw.line(screen,'White',
        (1056*int(resizing_factor/2),190*int(resizing_factor/2)),
        (1280*int(resizing_factor/2),190*int(resizing_factor/2)),
        width=2*int(resizing_factor/2))

    # drawing the stage number below the line
    if index_of_current_map == 8:
        game_font = pg.font.Font(
            'font/data-latin.ttf', 30*int(resizing_factor/2))
        stage_display = game_font.render(
            f'Stage:   {index_of_current_map+1}',False,'Red')
        screen.blit(stage_display,
                    (1088*int(resizing_factor/2),220*int(resizing_factor/2)))
    else:
        game_font = pg.font.Font(
            'font/data-latin.ttf', 30*int(resizing_factor/2))
        stage_display = game_font.render(
            f'Stage:   {index_of_current_map+1}',False,(65,105,225))
        screen.blit(stage_display,
                    (1088*int(resizing_factor/2),220*int(resizing_factor/2)))

    # drawing the remaining lives
    game_font = pg.font.Font('font/data-latin.ttf', 23*int(resizing_factor/2))
    lives_remaining_display = game_font.render('Lives remaining:',False,'White')
    screen.blit(lives_remaining_display,
                (1070*int(resizing_factor/2),290*int(resizing_factor/2)))
    tank_image = pg.image.load(
        'images/player/tank_armoured_up.png').convert_alpha()
    tank_image = pg.transform.scale2x(tank_image)
    if resizing_factor == 4:
        tank_image = pg.transform.scale2x(tank_image)
    i = 1
    x = 1080
    while i <= player_group.sprite.lives:
        screen.blit(tank_image,
                    (x*int(resizing_factor/2),330*int(resizing_factor/2)))
        x += 40
        i += 1

    # drawing the current armour rating
    current_armour_rating = game_font.render(
        f'Current armour: {player_group.sprite.health}',False,'White')
    screen.blit(current_armour_rating,
                (1070*int(resizing_factor/2),380*int(resizing_factor/2)))

    # drawing the boss health
    if index_of_current_map == 8 and (not game_state == 'summary screen'):
        current_armour_rating = game_font.render(
            f'Base health:   {main_base_group.sprite.health}',False,'Yellow')
        screen.blit(current_armour_rating,
                    (1070*int(resizing_factor/2),420*int(resizing_factor/2)))

    # drawing the horizontal line below the armour rating
    pg.draw.line(screen,'White',
        (1056*int(resizing_factor/2),465*int(resizing_factor/2)),
        (1280*int(resizing_factor/2),465*int(resizing_factor/2)),
        width=2*int(resizing_factor/2))

    # drawing the mute button and handling the muting/un-muting
    game_font = pg.font.Font('font/data-latin.ttf', 31*int(resizing_factor/2))
    if not mute_button_state:
        mute_button = game_font.render('Music off: M',False,'Grey')
        screen.blit(mute_button,
                    (1076*int(resizing_factor/2),480*int(resizing_factor/2)))
    else:
        mute_button = game_font.render('Music on: M',False,'Grey')
        screen.blit(mute_button,
                    (1076*int(resizing_factor/2),480*int(resizing_factor/2)))

    # drawing the horizontal line below the mute help
    pg.draw.line(screen,'White',
        (1056*int(resizing_factor/2),530*int(resizing_factor/2)),
        (1280*int(resizing_factor/2),530*int(resizing_factor/2)),
        width=2*int(resizing_factor/2))

    # drawing the back to menu button and handling the mouse presses
    game_font = pg.font.Font('font/data-latin.ttf', 31*int(resizing_factor/2))
    mouse_position = pg.mouse.get_pos()
    if not back_to_menu_pressed:
        back_to_menu_button = game_font.render('Back to menu',False,'Grey')
        back_to_menu_button_rect = back_to_menu_button.get_rect(
            topleft = (1078*int(resizing_factor/2),565*int(resizing_factor/2)))
        screen.blit(back_to_menu_button,
                    (1076*int(resizing_factor/2),565*int(resizing_factor/2)))
        if back_to_menu_button_rect.collidepoint(mouse_position):
            pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
            if left_mouse_button_pressed:
                sound_manager.button_click_sound.play()
                back_to_menu_pressed = True
                pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)
        else:
            pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)
    else:
        are_you_sure_button = game_font.render('Are you sure?',False,'Grey')
        screen.blit(are_you_sure_button,
                    (1068*int(resizing_factor/2),550*int(resizing_factor/2)))
        yes_button = game_font.render('Yes',False,'Grey')
        yes_button_rect = yes_button.get_rect(
            topleft = (1078*int(resizing_factor/2),590*int(resizing_factor/2)))
        screen.blit(yes_button,
                    (1078*int(resizing_factor/2),590*int(resizing_factor/2)))
        no_button = game_font.render('No',False,'Grey')
        no_button_rect = no_button.get_rect(
            topleft = (1218*int(resizing_factor/2),590*int(resizing_factor/2)))
        screen.blit(no_button,
                    (1218*int(resizing_factor/2),590*int(resizing_factor/2)))
        if yes_button_rect.collidepoint(mouse_position):
            pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
            if left_mouse_button_pressed:
                sound_manager.button_click_sound.play()
                back_to_menu_pressed = False
                back_to_menu_or_restart()
                game_state = 'start menu'
                pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)
                return
        elif no_button_rect.collidepoint(mouse_position):
            pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
            if left_mouse_button_pressed:
                sound_manager.button_click_sound.play()
                back_to_menu_pressed = False
                pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)
        else:
            pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)

    if game_state == 'end screen' or game_state == 'sec first':
        screen.fill('Black')


def group_creator():
    """Creates every sprite group we'll use."""

    global player_group
    global main_base_group
    global main_base_center_group
    global wall_group
    global water_group
    global lava_group
    global walkable_group
    global objectives_group
    global player_bullets_group
    global explosions_and_collapse_group
    global enemies_group
    global shield_group
    global tank1234_bullet_group
    global probable_goal_tile_group
    global spawn_animation_group
    

    player_group = pg.sprite.GroupSingle()
    main_base_group = pg.sprite.GroupSingle()
    main_base_center_group = pg.sprite.GroupSingle()

    wall_group = pg.sprite.Group()
    water_group = pg.sprite.Group()
    lava_group = pg.sprite.Group()
    walkable_group = pg.sprite.Group()
    objectives_group = pg.sprite.Group()
    player_group.add(Player())
    player_bullets_group = pg.sprite.Group()
    explosions_and_collapse_group = pg.sprite.Group()
    enemies_group = pg.sprite.Group()
    shield_group = pg.sprite.Group()
    tank1234_bullet_group = pg.sprite.Group()
    probable_goal_tile_group = pg.sprite.Group()
    spawn_animation_group = pg.sprite.Group()


def lose_screen():
    """Draws the lose screen after we lose the game."""

    global game_state

    screen.fill((27,29,29))

    # drawing the defeat message
    game_font = pg.font.Font('font/data-latin.ttf', 45*int(resizing_factor/2))
    defeat_message = game_font.render(
        f"You've been destroyed on stage {index_of_current_map}.",False,'Red')
    screen.blit(defeat_message,
                (280*int(resizing_factor/2),65*int(resizing_factor/2)))

    # drawing the horizontal line below the defeat message
    pg.draw.line(screen,'Red',
                (150*int(resizing_factor/2),130*int(resizing_factor/2)),
                (1130*int(resizing_factor/2),130*int(resizing_factor/2)),
                width=3*int(resizing_factor/2))

    # drawing the enemies destroyed message
    game_font = pg.font.Font('font/data-latin.ttf', 35*int(resizing_factor/2))
    destroyed_message = game_font.render("Enemies terminated:",False,'White')
    screen.blit(destroyed_message,
                (310*int(resizing_factor/2),150*int(resizing_factor/2)))

    # drawing the destroyed enemies columns beside
    i = 0
    y = 160
    sum = 0
    while i < len(destroyed_overall_enemies):
        if destroyed_overall_enemies[i]:
            image = pg.image.load(f'images/score/tank{i+1}.png').convert_alpha()
            image = pg.transform.scale2x(image)
            if resizing_factor == 4:
                image = pg.transform.scale2x(image)
            screen.blit(image,
                        (730*int(resizing_factor/2),y*int(resizing_factor/2)))
            number = game_font.render(
                f'{destroyed_overall_enemies[i]}',False,'Yellow')
            screen.blit(number,
                        (850*int(resizing_factor/2),y*int(resizing_factor/2)))
            sum += destroyed_overall_enemies[i]
            y += 80
        i += 1
    number = game_font.render(f'{sum}',False,'Red')
    screen.blit(number,(850*int(resizing_factor/2),y*int(resizing_factor/2)))        

    # drawing the buttons to the bottom left
    new_game_surf = game_font.render('New game',False,'White')
    new_game_rect = new_game_surf.get_rect(
        topleft = (90*int(resizing_factor/2),440*int(resizing_factor/2)))
    screen.blit(new_game_surf,
                (90*int(resizing_factor/2),440*int(resizing_factor/2)))

    main_menu_surf = game_font.render('Main menu',False,'White')
    main_menu_rect = main_menu_surf.get_rect(
        topleft = (80*int(resizing_factor/2),510*int(resizing_factor/2)))
    screen.blit(main_menu_surf,
                (80*int(resizing_factor/2),510*int(resizing_factor/2)))

    quit_surf = game_font.render('Quit',False,'White')
    quit_rect = quit_surf.get_rect(
        topleft = (120*int(resizing_factor/2),580*int(resizing_factor/2)))
    screen.blit(quit_surf,
                (120*int(resizing_factor/2),580*int(resizing_factor/2)))

    # button interactions
    mouse_position = pg.mouse.get_pos()
    if new_game_rect.collidepoint(mouse_position):
        pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
        if left_mouse_button_pressed:
            sound_manager.button_click_sound.play()
            back_to_menu_or_restart()
            game_state = 'intro first'
            pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)
            return
    elif main_menu_rect.collidepoint(mouse_position):
        pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
        if left_mouse_button_pressed:
            sound_manager.button_click_sound.play()
            back_to_menu_or_restart()
            game_state = 'start menu'
            pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)
            return
    elif quit_rect.collidepoint(mouse_position):
        pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
        if left_mouse_button_pressed:
            pg.mixer.quit()
            pg.quit()
            exit()
    else:
        pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)


def summary_screen():
    """Draws the summary screen after we win a stage."""

    global is_c_pressed
    global game_state

    screen.fill((27,29,29))
    # drawing the stage cleared message
    game_font = pg.font.Font('font/data-latin.ttf', 45*int(resizing_factor/2))
    clear_message = game_font.render(
        f"Stage {index_of_current_map} cleared.",False,(65,105,225))
    screen.blit(clear_message,
                (485*int(resizing_factor/2),45*int(resizing_factor/2)))

    # drawing the line below the cleared message
    pg.draw.line(screen,(65,105,225),(150*int(resizing_factor/2),
                130*int(resizing_factor/2)),(1130*int(resizing_factor/2),
                130*int(resizing_factor/2)),width=3*int(resizing_factor/2))

    # drawing the remainig lives message and images
    game_font = pg.font.Font('font/data-latin.ttf', 35*int(resizing_factor/2))
    destroyed_message = game_font.render("Lives remaining:",False,'White')
    screen.blit(destroyed_message,
                (100*int(resizing_factor/2),150*int(resizing_factor/2)))

    tank_image = pg.image.load(
        'images/player/tank_armoured_up.png').convert_alpha()
    tank_image = pg.transform.scale2x(tank_image)
    if resizing_factor == 4:
        tank_image = pg.transform.scale2x(tank_image)
    i = 1
    x = 100
    while i <= player_group.sprite.lives:
        screen.blit(tank_image,
                    (x*int(resizing_factor/2),200*int(resizing_factor/2)))
        x += 40
        i += 1

    # drawing the current armour rating
    current_armour_rating = game_font.render(
        f'Current armour: {player_group.sprite.health}',False,'White')
    screen.blit(current_armour_rating,
                (100*int(resizing_factor/2),260*int(resizing_factor/2)))

    # drawing the enemies destroyed message
    game_font = pg.font.Font('font/data-latin.ttf', 35*int(resizing_factor/2))
    destroyed_message = game_font.render("Enemies terminated:",False,'White')
    screen.blit(destroyed_message,
                (620*int(resizing_factor/2),150*int(resizing_factor/2)))

    # drawing the destroyed enemies columns beside
    i = 0
    y = 160
    sum = 0
    while i < len(destroyed_overall_enemies):
        if destroyed_overall_enemies[i]:
            image = pg.image.load(f'images/score/tank{i+1}.png').convert_alpha()
            image = pg.transform.scale2x(image)
            if resizing_factor == 4:
                image = pg.transform.scale2x(image)
            screen.blit(image,
                        (1010*int(resizing_factor/2),y*int(resizing_factor/2)))
            number = game_font.render(
                f'{destroyed_overall_enemies[i]}',False,'Yellow')
            screen.blit(number,
                        (1130*int(resizing_factor/2),y*int(resizing_factor/2)))
            sum += destroyed_overall_enemies[i]
            y += 80
        i += 1
    number = game_font.render(f'{sum}',False,'Red')
    screen.blit(number,(1130*int(resizing_factor/2),y*int(resizing_factor/2))) 

    # drawing the buttons to the bottom left
    new_game_surf = game_font.render('New game',False,'White')
    new_game_rect = new_game_surf.get_rect(
        topleft = (140*int(resizing_factor/2),440*int(resizing_factor/2)))
    screen.blit(new_game_surf,
                (140*int(resizing_factor/2),440*int(resizing_factor/2)))

    main_menu_surf = game_font.render('Main menu',False,'White')
    main_menu_rect = main_menu_surf.get_rect(
        topleft = (130*int(resizing_factor/2),510*int(resizing_factor/2)))
    screen.blit(main_menu_surf,
                (130*int(resizing_factor/2),510*int(resizing_factor/2)))

    quit_surf = game_font.render('Quit',False,'White')
    quit_rect = quit_surf.get_rect(
        topleft = (170*int(resizing_factor/2),580*int(resizing_factor/2)))
    screen.blit(quit_surf,
                (170*int(resizing_factor/2),580*int(resizing_factor/2)))

    # button interactions
    mouse_position = pg.mouse.get_pos()
    if new_game_rect.collidepoint(mouse_position):
        pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
        if left_mouse_button_pressed:
            sound_manager.button_click_sound.play()
            back_to_menu_or_restart()
            game_state = 'intro first'
            pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)
            return
    elif main_menu_rect.collidepoint(mouse_position):
        pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
        if left_mouse_button_pressed:
            sound_manager.button_click_sound.play()
            back_to_menu_or_restart()
            game_state = 'start menu'
            pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)
            return
    elif quit_rect.collidepoint(mouse_position):
        pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
        if left_mouse_button_pressed:
            pg.mixer.quit()
            pg.quit()
            exit()
    else:
        pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)

    # drawing the press c button
    displayed_line = game_font.render(
        '(Press the C key to continue)',False,'White')
    screen.blit(displayed_line,
                (400*int(resizing_factor/2),570*int(resizing_factor/2)))

    if is_c_pressed:
            if index_of_current_map == 1:
                screen.fill('Black')
                game_state = 'after first stage'
                is_c_pressed = False
                return
            elif index_of_current_map == 8:
                screen.fill('Black')
                game_state = 'after 8'
                is_c_pressed = False
                return
            else:
                game_state = which_map_is_next[index_of_current_map]
                is_c_pressed = False
                return


def back_to_menu_or_restart():
    """If we restart the game or go back to the main menu this takes care of
    resetting of the values of variables and emptying groups for a new game.
    """

    global maximum_number_of_enemies
    global objectives_destroyed
    global destroyed_overall_enemies
    global enemies_to_be_spawned
    global spawned_enemy_numbers
    global enemy_types_to_be_spawned
    global enemy_numbers_current_map
    global last_spawn_time
    global next_spawn_time
    global is_c_pressed
    global stage_5_one_building_down
    global stage_5_switch_flag
    global stage_9_buildings_down
    global map_loaded
    global back_to_menu_pressed
    global left_mouse_button_pressed
    global index_of_current_map
    global extra_life_counter
    global credits_screen_cleaner
    global credits_timer
    global credits_timer_switch

    screen.fill('Black')

    walkable_group.empty()
    probable_goal_tile_group.empty()
    wall_group.empty()
    water_group.empty()
    lava_group.empty()
    objectives_group.empty()
    player_bullets_group.empty()
    explosions_and_collapse_group.empty()
    enemies_group.empty()
    shield_group.empty()
    tank1234_bullet_group.empty()
    spawn_animation_group.empty()
    main_base_group.empty()
    main_base_center_group.empty()

    maximum_number_of_enemies = 0
    objectives_destroyed = 0
    destroyed_overall_enemies = [0,0,0,0,0]
    enemies_to_be_spawned = []
    spawned_enemy_numbers = [0, 0, 0, 0, 0]
    enemy_types_to_be_spawned = []
    enemy_numbers_current_map = []
    last_spawn_time = 0
    next_spawn_time = 0
    is_c_pressed = False
    stage_5_one_building_down = False
    stage_5_switch_flag = False
    stage_9_buildings_down = False
    map_loaded = False
    back_to_menu_pressed = False
    credits_screen_cleaner = False
    left_mouse_button_pressed = None
    credits_timer_switch = False
    index_of_current_map = 0
    extra_life_counter = 0
    credits_timer = 0

    map_loader_instance.reset()
    player_group.sprite.reset()
    sound_manager.whole_reset()
    text_displayer.reset()

   
def win_wait():
    """After we destroy the main base we can move until the explosion finishes
    but the enemy can't. For story reasons.
    """

    walkable_group.draw(screen)
    water_group.draw(screen)
    lava_group.draw(screen)
    
    objectives_group.draw(screen)
    main_base_center_group.draw(screen)
    enemies_group.draw(screen)
    player_group.draw(screen)
    main_base_group.sprite.soundwave_group.draw(screen)
    main_base_group.sprite.bullet_group.draw(screen)
    for sprite in enemies_group:
        if sprite.type == 5:
            sprite.laser_group.draw(screen)
    wall_group.draw(screen)
    shield_group.draw(screen)
    tank1234_bullet_group.draw(screen)
    main_base_group.draw(screen)
    player_bullets_group.draw(screen)
    explosions_and_collapse_group.draw(screen)

    player_group.sprite.update()
    player_bullets_group.update()
    main_base_group.sprite.update()
    tank1234_bullet_group.update()
    explosions_and_collapse_group.update()
    water_group.update()
    lava_group.update()
    for sprite in enemies_group:
        if sprite.type == 5:
            sprite.win_wait_update()


def extra_life():
    """Manages the extra life system. We get a life after 100 kills (the enemy
    vs enemy kills also count towards it).
    """

    global extra_life_counter

    if extra_life_counter > 99:
        player_group.sprite.lives += 1
        sound_manager.extra_life_channel.play(sound_manager.extra_life_sound)
        extra_life_counter = 0
    

def credits():
    """Takes care of the displayment of the whole credits sequence."""

    global credits_screen_cleaner
    global credits_timer_switch
    global credits_timer
    global game_state

    if credits_timer_switch == False:
        credits_timer = global_time_ms
        credits_timer_switch = True

    if global_time_ms-credits_timer < 4000:
        if credits_screen_cleaner == False:
            screen.fill('Black')
            credits_screen_cleaner = True
        game_font = pg.font.Font(
            'font/data-latin.ttf', 150*int(resizing_factor/2))
        game_logo = game_font.render('SIEGE',False,'White')
        game_logo_rect = game_logo.get_rect(
            topleft = (464*int(resizing_factor/2),120*int(resizing_factor/2)))
        pg.draw.rect(screen,'White',game_logo_rect,3*int(resizing_factor/2))
        screen.blit(game_logo,
                    (460*int(resizing_factor/2),120*int(resizing_factor/2)))

    elif 4000 < global_time_ms-credits_timer < 11000:
        if credits_screen_cleaner == True:
            screen.fill('Black')
            credits_screen_cleaner = False
        game_font = pg.font.Font(
            'font/data-latin.ttf', 150*int(resizing_factor/2))
        game_logo = game_font.render('SIEGE',False,'White')
        game_logo_rect = game_logo.get_rect(
            topleft = (464*int(resizing_factor/2),120*int(resizing_factor/2)))
        pg.draw.rect(screen,'White',game_logo_rect,3*int(resizing_factor/2))
        screen.blit(game_logo,
                    (460*int(resizing_factor/2),120*int(resizing_factor/2)))
        game_font = pg.font.Font(
            'font/data-latin.ttf', 40*int(resizing_factor/2))
        text = game_font.render('A game made with Pygame.',False,'Yellow')
        screen.blit(text,
                    (420*int(resizing_factor/2),450*int(resizing_factor/2)))

    elif 11000 < global_time_ms-credits_timer < 18000:
        if credits_screen_cleaner == False:
            screen.fill('Black')
            credits_screen_cleaner = True
        game_font = pg.font.Font(
            'font/data-latin.ttf', 150*int(resizing_factor/2))
        game_logo = game_font.render('SIEGE',False,'White')
        game_logo_rect = game_logo.get_rect(
            topleft = (464*int(resizing_factor/2),120*int(resizing_factor/2)))
        pg.draw.rect(screen,'White',game_logo_rect,3*int(resizing_factor/2))
        screen.blit(game_logo,
                    (460*int(resizing_factor/2),120*int(resizing_factor/2)))
        game_font = pg.font.Font(
            'font/data-latin.ttf', 50*int(resizing_factor/2))
        text = game_font.render('Music:',False,'Red')
        screen.blit(text,
                    (575*int(resizing_factor/2),360*int(resizing_factor/2)))
        game_font = pg.font.Font(
            'font/data-latin.ttf', 40*int(resizing_factor/2))
        text = game_font.render('Cuir - Maniac',False,'Yellow')
        screen.blit(text,
                    (510*int(resizing_factor/2),470*int(resizing_factor/2)))

    elif 18000 < global_time_ms-credits_timer < 25000:
        if credits_screen_cleaner == True:
            screen.fill('Black')
            credits_screen_cleaner = False
        game_font = pg.font.Font(
            'font/data-latin.ttf', 150*int(resizing_factor/2))
        game_logo = game_font.render('SIEGE',False,'White')
        game_logo_rect = game_logo.get_rect(
            topleft = (464*int(resizing_factor/2),120*int(resizing_factor/2)))
        pg.draw.rect(screen,'White',game_logo_rect,3*int(resizing_factor/2))
        screen.blit(game_logo,
                    (460*int(resizing_factor/2),120*int(resizing_factor/2)))
        game_font = pg.font.Font(
            'font/data-latin.ttf', 50*int(resizing_factor/2))
        text = game_font.render('Music:',False,'Red')
        screen.blit(text,(575*int(resizing_factor/2),360*int(resizing_factor/2)))
        game_font = pg.font.Font(
            'font/data-latin.ttf', 40*int(resizing_factor/2))
        text = game_font.render('Judas Priest - The hellion',False,'Yellow')
        screen.blit(text,(395*int(resizing_factor/2),470*int(resizing_factor/2)))

    elif 25000 < global_time_ms-credits_timer < 32000:
        if credits_screen_cleaner == False:
            screen.fill('Black')
            credits_screen_cleaner = True
        game_font = pg.font.Font(
            'font/data-latin.ttf', 150*int(resizing_factor/2))
        game_logo = game_font.render('SIEGE',False,'White')
        game_logo_rect = game_logo.get_rect(
            topleft = (464*int(resizing_factor/2),120*int(resizing_factor/2)))
        pg.draw.rect(screen,'White',game_logo_rect,3*int(resizing_factor/2))
        screen.blit(game_logo,
                    (460*int(resizing_factor/2),120*int(resizing_factor/2)))
        game_font = pg.font.Font(
            'font/data-latin.ttf', 50*int(resizing_factor/2))
        text = game_font.render('Music:',False,'Red')
        screen.blit(text,(575*int(resizing_factor/2),360*int(resizing_factor/2)))
        game_font = pg.font.Font(
            'font/data-latin.ttf', 40*int(resizing_factor/2))
        text = game_font.render(
            "Perturbator - Perturbator's theme",False,'Yellow')
        screen.blit(text,(325*int(resizing_factor/2),470*int(resizing_factor/2)))

    elif 32000 < global_time_ms-credits_timer < 39000:
        if credits_screen_cleaner == True:
            screen.fill('Black')
            credits_screen_cleaner = False
        game_font = pg.font.Font(
            'font/data-latin.ttf', 150*int(resizing_factor/2))
        game_logo = game_font.render('SIEGE',False,'White')
        game_logo_rect = game_logo.get_rect(
            topleft = (464*int(resizing_factor/2),120*int(resizing_factor/2)))
        pg.draw.rect(screen,'White',game_logo_rect,3*int(resizing_factor/2))
        screen.blit(game_logo,
                    (460*int(resizing_factor/2),120*int(resizing_factor/2)))
        game_font = pg.font.Font(
            'font/data-latin.ttf', 50*int(resizing_factor/2))
        text = game_font.render('Music:',False,'Red')
        screen.blit(text,(575*int(resizing_factor/2),360*int(resizing_factor/2)))
        game_font = pg.font.Font(
            'font/data-latin.ttf', 40*int(resizing_factor/2))
        text = game_font.render(
            "Perturbator - She is young, she is beautiful, she is next",
            False,'Yellow')
        screen.blit(text,(80*int(resizing_factor/2),470*int(resizing_factor/2)))

    elif 39000 < global_time_ms-credits_timer < 46000:
        if credits_screen_cleaner == False:
            screen.fill('Black')
            credits_screen_cleaner = True
        game_font = pg.font.Font(
            'font/data-latin.ttf', 150*int(resizing_factor/2))
        game_logo = game_font.render('SIEGE',False,'White')
        game_logo_rect = game_logo.get_rect(
            topleft = (464*int(resizing_factor/2),120*int(resizing_factor/2)))
        pg.draw.rect(screen,'White',game_logo_rect,3*int(resizing_factor/2))
        screen.blit(game_logo,
                    (460*int(resizing_factor/2),120*int(resizing_factor/2)))
        game_font = pg.font.Font(
            'font/data-latin.ttf', 50*int(resizing_factor/2))
        text = game_font.render('Music:',False,'Red')
        screen.blit(text,(575*int(resizing_factor/2),360*int(resizing_factor/2)))
        game_font = pg.font.Font(
            'font/data-latin.ttf', 40*int(resizing_factor/2))
        text = game_font.render("Carpenter Brut - Turbo killer",False,'Yellow')
        screen.blit(text,
                    (370*int(resizing_factor/2),470*int(resizing_factor/2)))

    elif 46000 < global_time_ms-credits_timer < 53000:
        if credits_screen_cleaner == True:
            screen.fill('Black')
            credits_screen_cleaner = False
        game_font = pg.font.Font(
            'font/data-latin.ttf', 150*int(resizing_factor/2))
        game_logo = game_font.render('SIEGE',False,'White')
        game_logo_rect = game_logo.get_rect(
            topleft = (464*int(resizing_factor/2),120*int(resizing_factor/2)))
        pg.draw.rect(screen,'White',game_logo_rect,3*int(resizing_factor/2))
        screen.blit(game_logo,
                    (460*int(resizing_factor/2),120*int(resizing_factor/2)))
        game_font = pg.font.Font(
            'font/data-latin.ttf', 50*int(resizing_factor/2))
        text = game_font.render('Music:',False,'Red')
        screen.blit(text,(575*int(resizing_factor/2),360*int(resizing_factor/2)))
        game_font = pg.font.Font(
            'font/data-latin.ttf', 40*int(resizing_factor/2))
        text = game_font.render("Candlemass - Mythos",False,'Yellow')
        screen.blit(text,(458*int(resizing_factor/2),470*int(resizing_factor/2)))

    elif 53000 < global_time_ms-credits_timer < 60000:
        if credits_screen_cleaner == False:
            screen.fill('Black')
            credits_screen_cleaner = True
        game_font = pg.font.Font(
            'font/data-latin.ttf', 150*int(resizing_factor/2))
        game_logo = game_font.render('SIEGE',False,'White')
        game_logo_rect = game_logo.get_rect(
            topleft = (464*int(resizing_factor/2),120*int(resizing_factor/2)))
        pg.draw.rect(screen,'White',game_logo_rect,3*int(resizing_factor/2))
        screen.blit(game_logo,
                    (460*int(resizing_factor/2),120*int(resizing_factor/2)))
        game_font = pg.font.Font(
            'font/data-latin.ttf', 50*int(resizing_factor/2))
        text = game_font.render('Sound effects:',False,'Red')
        screen.blit(text,(480*int(resizing_factor/2),360*int(resizing_factor/2)))
        game_font = pg.font.Font(
            'font/data-latin.ttf', 40*int(resizing_factor/2))
        text = game_font.render("pixabay.com",False,'Yellow')
        screen.blit(text,(535*int(resizing_factor/2),470*int(resizing_factor/2)))

    elif 60000 < global_time_ms-credits_timer < 66000:
        if credits_screen_cleaner == True:
            screen.fill('Black')
            credits_screen_cleaner = False
        game_font = pg.font.Font(
            'font/data-latin.ttf', 150*int(resizing_factor/2))
        game_logo = game_font.render('SIEGE',False,'White')
        game_logo_rect = game_logo.get_rect(
            topleft = (464*int(resizing_factor/2),120*int(resizing_factor/2)))
        pg.draw.rect(screen,'White',game_logo_rect,3*int(resizing_factor/2))
        screen.blit(game_logo,
                    (460*int(resizing_factor/2),120*int(resizing_factor/2)))
        game_font = pg.font.Font(
            'font/data-latin.ttf', 50*int(resizing_factor/2))
        text = game_font.render('Font:',False,'Red')
        screen.blit(text,(595*int(resizing_factor/2),360*int(resizing_factor/2)))
        game_font = pg.font.Font(
            'font/data-latin.ttf', 40*int(resizing_factor/2))
        text = game_font.render("1001freefonts.com",False,'Yellow')
        screen.blit(text,(483*int(resizing_factor/2),470*int(resizing_factor/2)))
        
    elif 66000 < global_time_ms-credits_timer < 72000:
        if credits_screen_cleaner == False:
            screen.fill('Black')
            credits_screen_cleaner = True
        game_font = pg.font.Font(
            'font/data-latin.ttf', 70*int(resizing_factor/2))
        text = game_font.render('Thanks for playing!',False,'White')
        screen.blit(text,(310*int(resizing_factor/2),280*int(resizing_factor/2)))
    elif 72000 < global_time_ms-credits_timer:
        if credits_screen_cleaner == True:
            screen.fill('Black')
            credits_screen_cleaner = False
        game_font = pg.font.Font(
            'font/data-latin.ttf', 70*int(resizing_factor/2))
        text = game_font.render('Thanks for playing!',False,'White')
        screen.blit(text,(310*int(resizing_factor/2),280*int(resizing_factor/2)))

        # drawing the buttons to the bottom left
        game_font = pg.font.Font('font/data-latin.ttf', 35*int(resizing_factor/2))
        new_game_surf = game_font.render('New game',False,'White')
        new_game_rect = new_game_surf.get_rect(
            topleft = (90*int(resizing_factor/2),440*int(resizing_factor/2)))
        screen.blit(new_game_surf,
                    (90*int(resizing_factor/2),440*int(resizing_factor/2)))

        main_menu_surf = game_font.render('Main menu',False,'White')
        main_menu_rect = main_menu_surf.get_rect(
            topleft = (80*int(resizing_factor/2),510*int(resizing_factor/2)))
        screen.blit(main_menu_surf,
                    (80*int(resizing_factor/2),510*int(resizing_factor/2)))

        quit_surf = game_font.render('Quit',False,'White')
        quit_rect = quit_surf.get_rect(
            topleft = (120*int(resizing_factor/2),580*int(resizing_factor/2)))
        screen.blit(quit_surf,
                    (120*int(resizing_factor/2),580*int(resizing_factor/2)))

        # button interactions
        mouse_position = pg.mouse.get_pos()
        if new_game_rect.collidepoint(mouse_position):
            pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
            if left_mouse_button_pressed:
                sound_manager.button_click_sound.play()
                back_to_menu_or_restart()
                game_state = 'intro first'
                pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)
                return
        elif main_menu_rect.collidepoint(mouse_position):
            pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
            if left_mouse_button_pressed:
                sound_manager.button_click_sound.play()
                back_to_menu_or_restart()
                game_state = 'start menu'
                pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)
                return
        elif quit_rect.collidepoint(mouse_position):
            pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
            if left_mouse_button_pressed:
                pg.mixer.quit()
                pg.quit()
                exit()
        else:
            pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)
    

#-------------------------------CLASSES-----------------------------------

class StoryScreensDisplayer():
    """Class for the handling of the story screens."""

    def __init__(self):
        self.reset()
    
    def text_reader(self):
        """Reads in the text in each text screen and sets the color of the
        text.
        """
        if game_state == 'intro first':
            story_file_path = Path('text/intro_first.txt')
            story_text = story_file_path.read_text()
            self.text_colour = 'Yellow'
        elif game_state == 'intro second':
            story_file_path = Path('text/intro_second.txt')
            story_text = story_file_path.read_text()
            self.text_colour = 'White'
        elif game_state == 'after first stage':
            story_file_path = Path('text/after_first_stage.txt')
            story_text = story_file_path.read_text()
            self.text_colour = 'White'
        elif game_state == 'after 8':
            story_file_path = Path('text/after_eighth_stage.txt')
            story_text = story_file_path.read_text()
            self.text_colour = 'White'
        elif game_state == 'end screen':
            story_file_path = Path('text/end_screen.txt')
            story_text = story_file_path.read_text()
            self.text_colour = 'White'
        elif game_state == 'sec first':
            story_file_path = Path('text/sec_first.txt')
            story_text = story_file_path.read_text()
            self.text_colour = 'White'
        elif game_state == 'sec second':
            story_file_path = Path('text/sec_second.txt')
            story_text = story_file_path.read_text()
            self.text_colour = 'White'
        elif game_state == 'sec third':
            story_file_path = Path('text/sec_third.txt')
            story_text = story_file_path.read_text()
            self.text_colour = 'Blue'

        self.story_text_lines = story_text.splitlines()
        self.story_text_lines.append('')
        self.story_text_lines.reverse()
        self.text_read_in = True

    def text_skip_checker(self):
        """Chooses the proper method for the story screens to display text."""

        if self.text_screen_finished:
            self.waiting_for_c_key()
        elif self.textscreen_c_pressed:
            self.fast_displayment()
        else:
            self.regular_displayment()
        
    def waiting_for_c_key(self):
        """At the end of the story screens makes sure the player has to
        press the C key to proceed.
        Upon the key press changes the game state.
        """

        global game_state
        global index_of_current_map
        
        if self.textscreen_c_pressed:
            self.text_read_in = False
            self.text_screen_finished = False
            self.textscreen_c_pressed = False
            self.sound_switch = True
            if game_state == 'intro first':
                screen.fill('Black')
                self.y = 30
                game_state = 'intro second'
                self.sound_switch = 2
            elif game_state == 'intro second':
                screen.fill('Black')
                self.y = 30
                game_state = which_map_is_next[index_of_current_map]
            elif game_state == 'after first stage':
                screen.fill('Black')
                self.y = 30
                game_state = which_map_is_next[index_of_current_map]
            elif game_state == 'after 8':
                screen.fill('Black')
                self.y = 30
                game_state = which_map_is_next[index_of_current_map]
            elif game_state == 'end screen':
                screen.fill('Black')
                game_state = 'credits'
            elif game_state == 'sec first':
                screen.fill('Black')
                self.y = 30
                game_state = 'sec second'
            elif game_state == 'sec second':
                screen.fill('Black')
                self.y = 30
                game_state = 'sec third'
                self.sound_switch = 3
            elif game_state == 'sec third':
                screen.fill('Black')
                game_state = 'credits'
        else:
            if game_state == 'sec third':
                displayed_line = self.game_font.render(
                    "Congratulations! You've found the secret ending!",
                    False,self.text_colour)
                screen.blit(displayed_line,
                            (305*int(resizing_factor/2),
                            530*int(resizing_factor/2)))
            self.text_colour = 'White'
            displayed_line = self.game_font.render(
                '(Press C to continue)',False,self.text_colour)
            screen.blit(displayed_line,
                        (480*int(resizing_factor/2),
                        570*int(resizing_factor/2)))

    def fast_displayment(self):
        """Dumps the text onto the screen as fast as possible and
        without sounds.
        """

        current_line = self.story_text_lines.pop()
        self.previous_line_length = len(current_line)
        if not current_line:
            self.text_screen_finished = True
            self.textscreen_c_pressed = False
            return
        
        displayed_line = self.game_font.render(
            current_line,False,self.text_colour)
        screen.blit(displayed_line,
                    (self.x*int(resizing_factor/2),
                    self.y*int(resizing_factor/2)))
        self.y += 40

    def regular_displayment(self):
        """Displays the text screen with sounds and slowly."""

        # we display every word that's 8 letters maximum in 0.8 seconds and for
        # the rest we scale the time (1 letter = +120 ms)
        if (self.previous_line_length <= 8 and
            global_time_ms-self.time_of_last_frame < 800):
            return
        elif global_time_ms-self.time_of_last_frame < self.previous_line_length*120:
            return
        current_line = self.story_text_lines.pop()
        self.previous_line_length = len(current_line)

        # we know a story screen has finished when the current line is empty
        if not current_line:
            self.text_screen_finished = True
            return

        displayed_line = self.game_font.render(current_line,False,self.text_colour)
        if self.sound_switch == 1:
            sound_manager.enemy_comp_sound.play()
        elif self.sound_switch == 2:
            sound_manager.player_comp_sound.play()
        elif self.sound_switch == 3:
            sound_manager.sec_comp_sound.play()
        screen.blit(displayed_line,(self.x*int(resizing_factor/2),self.y*int(resizing_factor/2)))
        self.y += 40
        self.time_of_last_frame = global_time_ms

    def reset(self):
        """Resets every value to the initial values."""

        self.game_font = pg.font.Font('font/data-latin.ttf', 30*int(resizing_factor/2))
        self.which_text_screen = 'first in intro'
        self.which_text_screen_index = 0
        self.x = 10*resizing_factor
        self.y = 30
        self.textscreen_c_pressed = False
        self.text_screen_finished = False
        self.time_of_last_frame = 0
        self.previous_line_length = 10
        self.sound_switch = 1
        self.text_read_in = False


class MapLoader():
    """Reads in the tilemap data (tiles, spawn locations etc.) 
    and creates the stages from them. Determines the maximum number of
    enemies to be spawned and resets the number of spawned enemies to zero.
    """

    def __init__(self):
        self.background_tile_layer = None
        self.tile_grid = []
        self.enemy_spawn_locations = []
        self.map_loaded = False

    def map_loader_instance(self):
        """Creates the next map for us."""

        global maximum_number_of_enemies
        global spawned_enemy_numbers
        global enemy_numbers_current_map
        global first_stage_to_be_loaded

        if first_stage_to_be_loaded:
            group_creator()
            first_stage_to_be_loaded = False

        enemy_numbers_current_map = enemy_numbers[index_of_current_map]
        spawned_enemy_numbers = [0, 0, 0, 0, 0]

        for number in enemy_numbers[index_of_current_map]:
                maximum_number_of_enemies += number

        if not self.map_loaded:
            # we read in and store all the information about the next map in
            # this variable
            map_data = load_pygame(
                f'stages/{which_map_is_next[index_of_current_map]}.tmx')
            self.background_tile_layer = map_data.get_layer_by_name('tiles')

            for x,y,surf in self.background_tile_layer.tiles():
                tile_type = map_data.get_tile_properties(x,y,0)
                if tile_type['type'] == 'wall':
                    wall_group.add(RectanglesFromTiles(x,y,surf))
                elif tile_type['type'] == 'water':
                    water_group.add(
                        RectanglesFromTiles(x,y,surf,tile_type['type']))
                elif tile_type['type'] == 'lava':
                    lava_group.add(
                        RectanglesFromTiles(x,y,surf,tile_type['type']))
                elif tile_type['type'] == 'dirt' or tile_type['type'] == 'grass':
                    self.tile_grid.append((x,y))
                    walkable_group.add(RectanglesFromTiles(x,y,surf))

            inaccesible_tile_separator(self.background_tile_layer.width,
                self.background_tile_layer.height)

            if index_of_current_map == 8:
                stage_9_tile_correcton()
            layer = map_data.get_layer_by_name('objects')

            # now we switch the layer to read in the player and enemy spawn
            # locations and also the coordinates of the objectives
            for obj in layer:
                if obj.name == 'player_start':
                    for player in player_group:
                        player.current_spawn_x = obj.x*resizing_factor
                        player.current_spawn_y = obj.y*resizing_factor
                        player.rect.centerx = obj.x*resizing_factor
                        player.rect.centery = obj.y*resizing_factor
                elif obj.name == 'spawn':
                    self.enemy_spawn_locations.append(
                        (obj.x*resizing_factor,obj.y*resizing_factor))
                elif obj.name == 'station_place':
                    objectives_group.add(
                        ObjectiveSprite(obj.x//16*16,obj.y//16*16))

            if index_of_current_map == 8:
                main_base_group.add(MainBase())
                main_base_center_group.add(MainBaseCenter())

            self.map_loaded = True

    def reset(self):
        """Resets the attributes of the MapLoader to the defaults. Should be
        used after each stage.
        """

        self.background_tile_layer = None
        self.tile_grid = []
        self.enemy_spawn_locations = []
        self.map_loaded = False


class RectanglesFromTiles(pg.sprite.Sprite):
    """Creates a rectangle for the tile surface we pass in."""

    def __init__(self,x,y,surf,*arg):
        super().__init__()
        # we set the radius for the heat damage for the lava tiles
        if not len(arg) == 0 and arg[0] == 'lava':
            self.radius = 13*resizing_factor
            self.images = []
            self.image = surf
            self.image = pg.transform.scale2x(self.image)
            if resizing_factor == 4:
                self.image = pg.transform.scale2x(self.image)
            self.images.append(self.image)
            im = pg.image.load('stages/lava2.png').convert_alpha()
            self.image = pg.transform.scale2x(im)
            if resizing_factor == 4:
                self.image = pg.transform.scale2x(self.image)
            self.images.append(self.image)
            self.type = 'lava'
            self.timer = 0
            self.animation_help = False

        elif not len(arg) == 0 and arg[0] == 'water':
            self.images = []
            self.image = surf
            self.image = pg.transform.scale2x(self.image)
            if resizing_factor == 4:
                self.image = pg.transform.scale2x(self.image)
            self.images.append(self.image)
            im = pg.image.load('stages/water2.png').convert_alpha()
            self.image = pg.transform.scale2x(im)
            if resizing_factor == 4:
                self.image = pg.transform.scale2x(self.image)
            self.images.append(self.image)
            self.type = 'water'
            self.timer = 0
            self.animation_help = False
        else:
            self.type = None
            self.image = surf
            self.image = pg.transform.scale2x(self.image)
            if resizing_factor == 4:
                self.image = pg.transform.scale2x(self.image)
        # we multiply by 16 (size of the tiles) because the x,y here are
        # the grid numbers (0,1,2...) NOT the coordinates
        self.rect = self.image.get_rect(
            topleft = (x*16*resizing_factor,y*16*resizing_factor))

    def update(self):
        """Animates the lava and water tiles."""

        if (self.type == 'lava' or self.type == 'water'):
            if global_time_ms-self.timer > 1200:
                if self.animation_help:
                    self.image = self.images[0]
                    self.animation_help = not self.animation_help
                    self.timer = global_time_ms
                else:
                    self.image = self.images[1]
                    self.animation_help = not self.animation_help
                    self.timer = global_time_ms


class ObjectiveSprite(pg.sprite.Sprite):
    """Class for the handling of the objective buildings."""
    
    def __init__(self,x,y):
        """Creates the objective sprites at the given coordinates."""

        super().__init__()
        self.image = pg.image.load(
            'images/other/communications_station.png').convert_alpha()
        self.image = pg.transform.scale2x(self.image)
        self.destroyed_image = pg.image.load(
            'images/other/comm_station_debris.png').convert_alpha()
        self.destroyed_image = pg.transform.scale2x(self.destroyed_image)
        if resizing_factor == 4:
            self.image = pg.transform.scale2x(self.image)
            self.destroyed_image = pg.transform.scale2x(self.destroyed_image)
        self.rect = self.image.get_rect(
            topleft = (x*resizing_factor,y*resizing_factor))
        self.health = COMM_BUILDINGS_HITPOINTS
        self.destroyed = False

    def objective_manager(self):
        """Checks if the obejctive is destroyed and changes its image
        if necessary. Also manages its health (checks for collisions with 
        player the bullets).
        """

        global stage_5_one_building_down
        global stage_5_switch_flag
        global objectives_destroyed

        if self.destroyed == True:
            return

        if self.health < 1:
            objectives_destroyed += 1
            self.image = self.destroyed_image
            self.destroyed = True
            explosions_and_collapse_group.add(
                ExplosionsAndCollapseAnimations(
                    self.rect.centerx,self.rect.centery,'collapse'))

            if index_of_current_map == 4 and stage_5_switch_flag == False:
                stage_5_one_building_down = True

        for sprite in player_bullets_group:
            if self.rect.colliderect(sprite.rect):
                sound_manager.building_hit_sound.play()
                self.health -=1
                sprite.kill()

    def update(self):
        """Keeps track of the states of the objective sprites."""

        self.objective_manager()


class Player(pg.sprite.Sprite):
    """Class managing the player.
    Be aware that we use two rectangles for collisions: self.rect and the smaller
    self.hitbox. Pay attention which one we use in a situation. We also need
    to update both of them every frame.
    """

    def __init__(self):
        super().__init__()
        self.images = []
        self.default_images = []
        self.grey_armour_images = []
        self.black_armour_images = []
        self.directions = ['right','up','left','down','right','up']
        for i in self.directions:
            #default images
            self.image = pg.image.load(
                f'images/player/tank_default_{i}.png').convert_alpha()
            self.image = pg.transform.scale2x(self.image)
            if resizing_factor == 4:
                self.image = pg.transform.scale2x(self.image)
            self.default_images.append(self.image)
            #black armour images
            self.image = pg.image.load(
                f'images/player/tank_upgraded_{i}.png').convert_alpha()
            self.image = pg.transform.scale2x(self.image)
            if resizing_factor == 4:
                self.image = pg.transform.scale2x(self.image)
            self.black_armour_images.append(self.image)
            #grey armour images
            self.image = pg.image.load(
                f'images/player/tank_armoured_{i}.png').convert_alpha()
            self.image = pg.transform.scale2x(self.image)
            if resizing_factor == 4:
                self.image = pg.transform.scale2x(self.image)
            self.grey_armour_images.append(self.image)
        self.images = self.grey_armour_images
        self.rect = self.image.get_rect()

        self.direction = 'up'
        # these are needed for the movement and adjusting the proper images to it
        self.direction_keys = [
            pg.K_RIGHT, pg.K_UP, pg.K_LEFT, pg.K_DOWN,
            pg.K_RIGHT, pg.K_UP, pg.K_LEFT
            ]
        self.index_and_speed = [
            [PLAYER_SPEED,0],
            [0,PLAYER_SPEED*(-1)],
            [PLAYER_SPEED*(-1),0],
            [0,PLAYER_SPEED],
            [PLAYER_SPEED,0],
            [0,PLAYER_SPEED*(-1)],
            [PLAYER_SPEED*(-1),0]
        ]
        self.primary_player_direction = None
        self.last_shooting_time = 0

        self.lives = PLAYER_LIVES
        self.health = STARTING_PLAYER_HEALTH

        self.temporary_invincibility = False
        self.invincibility_time = INVINCIBILITY_TIME
        self.invincibility_flag = False
        self.lava_sound_controller = False
        self.timer = 0
        self.heat_bar_width = DEFAULT_HEAT_BAR_WIDTH
        self.accepting_damage = True

        self.current_spawn_x = 0
        self.current_spawn_y = 0
        self.animation_active = False
        self.spawn_animation_cicle = 1
        self.spawn_circle_radius = 200

        self.hitbox = pg.Rect(0,0,10*resizing_factor,10*resizing_factor)
        self.hitbox.centerx = self.rect.centerx
        self.hitbox.centery = self.rect.centery

    def player_controls(self):
        """Includes the spatial movement and shooting functionality."""

        # it was quite easy to achieve the controls I imagined; the code is
        # pretty straight forward (especially after trying out the game...)
        # IMO it turned out to be pretty good, it feels good and is responsive

        keys = pg.key.get_pressed()
        # first we set the value of the primary direction when it gets pressed
        if not self.primary_player_direction:
            for key in self.direction_keys[1:5]:
                if keys[key]:
                    self.primary_player_direction = key
        # we check if we let go of the primary key and if yes we change its value
        elif not keys[self.primary_player_direction]:
            self.primary_player_direction = None
        # rest of the movement
        else:
            if keys[self.primary_player_direction]:
                index = self.direction_keys.index(
                    self.primary_player_direction,1,5)
                if keys[self.direction_keys[index+1]]:
                    goal_sublist = self.index_and_speed[index+1]
                    self.rect.centerx += goal_sublist[0]
                    self.rect.centery += goal_sublist[1]
                    self.image = self.images[index+1]
                    self.direction = self.directions[index+1]
                elif keys[self.direction_keys[index-1]]:
                    goal_sublist = self.index_and_speed[index-1]
                    self.rect.centerx += goal_sublist[0]
                    self.rect.centery += goal_sublist[1]
                    self.image = self.images[index-1]
                    self.direction = self.directions[index-1]
                # if we press the key for the opposite direction we stop moving
                elif keys[self.direction_keys[index+2]]:
                    pass
                else:
                    goal_sublist = self.index_and_speed[index]
                    self.rect.centerx += goal_sublist[0]
                    self.rect.centery += goal_sublist[1]
                    self.image = self.images[index]
                    self.direction = self.directions[index]
            self.rect = self.image.get_rect(
                center=(self.rect.centerx,self.rect.centery))
        # DO NOT forget to update the hitbox too after the rect!
        self.hitbox.centerx = self.rect.centerx
        self.hitbox.centery = self.rect.centery

        # now we check if we shoot
        # we can only have maximum 2 bullets on the screen at the same time
        # also we want some minimal interval between the shots
        if keys[pg.K_SPACE]:
            if (len(player_bullets_group) < MAX_PLAYER_BULLETS and
                PLAYER_SHOOTING_SPEED < global_time_ms-self.last_shooting_time):
                player_bullets_group.add(
                    PlayerBullet(self.rect.x,self.rect.y,self.direction))
                self.last_shooting_time = global_time_ms

    def collision_detection(self):
        """Handles the player sprite's collisions."""

        global game_state
        collision_tolerance = 3*resizing_factor

        # collision with the walls
        for sprite in wall_group:
            if player_obstacle_collision(self,sprite):
                if abs(self.hitbox.top-sprite.rect.bottom) < collision_tolerance:
                    self.hitbox.top = sprite.rect.bottom
                if abs(self.hitbox.bottom-sprite.rect.top) < collision_tolerance:
                    self.hitbox.bottom = sprite.rect.top
                if abs(self.hitbox.right-sprite.rect.left) < collision_tolerance:
                    self.hitbox.right = sprite.rect.left
                if abs(self.hitbox.left-sprite.rect.right) < collision_tolerance:
                    self.hitbox.left = sprite.rect.right
            self.rect.centerx = self.hitbox.centerx
            self.rect.centery = self.hitbox.centery

        # collision with water
        for sprite in water_group:
            if player_obstacle_collision(self,sprite):
                if abs(self.hitbox.top-sprite.rect.bottom) < collision_tolerance:
                    self.hitbox.top = sprite.rect.bottom
                if abs(self.hitbox.bottom-sprite.rect.top) < collision_tolerance:
                    self.hitbox.bottom = sprite.rect.top
                if abs(self.hitbox.right-sprite.rect.left) < collision_tolerance:
                    self.hitbox.right = sprite.rect.left
                if abs(self.hitbox.left-sprite.rect.right) < collision_tolerance:
                    self.hitbox.left = sprite.rect.right
            self.rect.centerx = self.hitbox.centerx
            self.rect.centery = self.hitbox.centery

        # collision with lava
        for sprite in lava_group:
            if player_obstacle_collision(self,sprite):
                if abs(self.hitbox.top-sprite.rect.bottom) < collision_tolerance:
                    self.hitbox.top = sprite.rect.bottom
                if abs(self.hitbox.bottom-sprite.rect.top) < collision_tolerance:
                    self.hitbox.bottom = sprite.rect.top
                if abs(self.hitbox.right-sprite.rect.left) < collision_tolerance:
                    self.hitbox.right = sprite.rect.left
                if abs(self.hitbox.left-sprite.rect.right) < collision_tolerance:
                    self.hitbox.left = sprite.rect.right
            self.rect.centerx = self.hitbox.centerx
            self.rect.centery = self.hitbox.centery

        # collision with the comm buildings
        for sprite in objectives_group:
            if player_obstacle_collision(self,sprite):
                if abs(self.hitbox.top-sprite.rect.bottom) < collision_tolerance:
                    self.hitbox.top = sprite.rect.bottom
                if abs(self.hitbox.bottom-sprite.rect.top) < collision_tolerance:
                    self.hitbox.bottom = sprite.rect.top
                if abs(self.hitbox.right-sprite.rect.left) < collision_tolerance:
                    self.hitbox.right = sprite.rect.left
                if abs(self.hitbox.left-sprite.rect.right) < collision_tolerance:
                    self.hitbox.left = sprite.rect.right
            self.rect.centerx = self.hitbox.centerx
            self.rect.centery = self.hitbox.centery

        # collision with the screen borders
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > 320*resizing_factor:
            self.rect.bottom = 320*resizing_factor
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > 528*resizing_factor:
            self.rect.right = 528*resizing_factor

        # collision with the shield upgrade
        for sprite in shield_group:
            if self.rect.colliderect(sprite.rect):
                sound_manager.shield_upgrade_channel.play(
                    sound_manager.shield_upgrade_sound)
                self.health += SHIELD_PLUS_ARMOUR
                if not self.accepting_damage:
                    for image in self.images:
                        image.set_alpha(120)
                sprite.kill()

        # collision with the projectiles
        for sprite in tank1234_bullet_group:
            if self.rect.colliderect(sprite.rect):
                if sprite.type == 3:
                    self.damage_checker(type=sprite.type,
                        x=sprite.rect.centerx,y=sprite.rect.centery)
                elif self.accepting_damage:
                    self.damage_checker(type=sprite.type)
                    sprite.kill()

        if index_of_current_map == 8:        
            if self.rect.colliderect(main_base_center_group.sprite.rect):
                screen.fill('Black')
                game_state = 'sec first'

    def lava_damage(self):
        """Determines if we are under heat damage or not. Displays the heat bar 
        and calculates when we die when we are under heat damage.
        """

        # if we are under invincibility (e.g. just lost a life to lava damage)
        # we reset the heat bar to max length
        if self.temporary_invincibility:
            if self.heat_bar_width < DEFAULT_HEAT_BAR_WIDTH:
                self.heat_bar_width = DEFAULT_HEAT_BAR_WIDTH
            return

        lava_tiles_damaging_us =pg.sprite.spritecollide(
            self,lava_group,False,pg.sprite.collide_circle)
        if lava_tiles_damaging_us:
            if self.lava_sound_controller == False:
                sound_manager.lava_damage_start = True
                self.lava_sound_controller = True
            if not self.accepting_damage:
                self.accepting_damage = True
            if (global_time_ms-self.timer > HEAT_DAMAGE_RESISTANCE/60 
                    and self.heat_bar_width > 0):
                self.heat_bar_width -= 1
                self.timer = global_time_ms
                if self.heat_bar_width < 1:
                    sound_manager.lava_damage_end = True
                    self.damage_checker(type='lava')

            # drawing the heat bar
            pg.draw.rect(screen,'Black', (
                self.rect.centerx-17*resizing_factor,
                self.rect.centery-17*resizing_factor,
                34*resizing_factor,
                8*resizing_factor))
            pg.draw.rect(screen,'White', (
                self.rect.centerx-16*resizing_factor,
                self.rect.centery-16*resizing_factor,
                32*resizing_factor,
                6*resizing_factor))
            pg.draw.rect(screen,'Red', (
                self.rect.centerx-15*resizing_factor,
                self.rect.centery-15*resizing_factor,
                self.heat_bar_width,
                4*resizing_factor))
        
        else:
            if (global_time_ms-self.timer > HEAT_DAMAGE_RESISTANCE/60 
                    and self.heat_bar_width < DEFAULT_HEAT_BAR_WIDTH):
                # we want the heat bar to refill twice as fast as it drains
                self.heat_bar_width += 2
                self.timer = global_time_ms
            if self.lava_sound_controller:
                sound_manager.lava_damage_end = True
                self.lava_sound_controller = False

    def image_handler(self):
        """Changes the images according to the player's health."""

        if self.health > 2:
            image_index = self.images.index(self.image)
            self.images = self.black_armour_images
            self.image = self.images[image_index]
        elif self.health == 2:
            image_index = self.images.index(self.image)
            self.images = self.grey_armour_images
            self.image = self.images[image_index]
        elif self.health < 2:
            image_index = self.images.index(self.image)
            self.images = self.default_images
            self.image = self.images[image_index]

    def invincibility(self):
        """Handles the player's invincibility after health reduction."""

        if not self.temporary_invincibility:
            return

        if self.invincibility_flag == False:
            self.accepting_damage = False
            self.timer = global_time_ms
            for image in self.images:
                image.set_alpha(120)
            self.invincibility_flag = True

        if global_time_ms-self.timer > INVINCIBILITY_TIME:
            for image in self.images:
                image.set_alpha(255)
            self.temporary_invincibility = False
            self.invincibility_flag = False
            self.accepting_damage = True
            
    def damage_checker(self, **kwargs):
        """Handles the player's health reduction."""

        if self.accepting_damage:
            sound_manager.player_hit_sound.play()
            if kwargs['type'] == 'beam':
                self.health -= LASER_BEAM_DAMAGE
                self.temporary_invincibility = True
            elif kwargs['type'] == 'grenade explosion':
                self.health -= GRENADE_DAMAGE
                self.temporary_invincibility = True
            elif kwargs['type'] == 1 or kwargs['type'] == 2:
                self.health -= ENEMY_BULLET_DAMAGE
                self.temporary_invincibility = True
            elif kwargs['type'] == 3:
                explosions_and_collapse_group.add(
                        ExplosionsAndCollapseAnimations(kwargs['x'],
                            kwargs['y'],'grenade explosion'))
            elif kwargs['type'] == 4:
                self.health -= SOUNDWAVE_DAMAGE
                self.temporary_invincibility = True
            elif kwargs['type'] == 'lava':
                self.health -= LAVA_DAMAGE
                self.temporary_invincibility = True

    def death_checker(self):
        """If we lose a life but still have to this will respawn us at our
        current spawn point (where we begant he stage).
        """
        
        if self.health < 1:
            self.temporary_invincibility = True
            self.lives -= 1
            sound_manager.player_respawn_channel.play(
                sound_manager.player_respawn_sound)
            self.rect.x = self.current_spawn_x
            self.rect.y = self.current_spawn_y
            if not (self.lives < 1):
                self.animation_active = True
                self.health = STARTING_PLAYER_HEALTH

    def spawn_animation(self):
        """Handles the respawn animation: draws a bunch of big red circles
        that close in on us. Helps the player know immediately where the tank is
        after death.
        """

        if not self.animation_active:
            return
        pg.draw.circle(screen,'Red',
                        (self.rect.centerx,self.rect.centery),
                        self.spawn_circle_radius,width=4)
        self.spawn_circle_radius -= 20
        if self.spawn_circle_radius < 0:
            self.spawn_circle_radius = 200
            self.spawn_animation_cicle += 1
        if self.spawn_animation_cicle > 3:
            self.animation_active = False
            self.spawn_animation_cicle = 1

    def reset(self):
        """Resets the player instance's attributes."""

        self.lives = PLAYER_LIVES
        self.health = STARTING_PLAYER_HEALTH
        self.primary_player_direction = None
        self.last_shooting_time = 0
        self.temporary_invincibility = False
        self.invincibility_time = INVINCIBILITY_TIME
        self.invincibility_flag = False
        self.timer = 0
        self.heat_bar_width = DEFAULT_HEAT_BAR_WIDTH
        self.accepting_damage = True
        self.lava_sound_controller = False
        self.current_spawn_x = 0
        self.current_spawn_y = 0
        self.animation_active = False

    def update(self):
        """Updates the player instance."""

        self.death_checker()
        self.spawn_animation()
        self.image_handler()
        self.player_controls()
        self.invincibility()
        self.lava_damage()
        self.collision_detection()
  

class PlayerBullet(pg.sprite.Sprite):
    """Class handling the player's bullets."""

    def __init__(self,x,y,direction):
        super().__init__()
        self.image = pg.image.load(
            'images/player/player_bullet.png').convert_alpha()
        self.image = pg.transform.scale2x(self.image)
        if resizing_factor == 4:
            self.image = pg.transform.scale2x(self.image)
        if direction == 'up': 
            self.rect = self.image.get_rect(topleft = (x+4*resizing_factor,y))
        elif direction == 'left':
            self.rect = self.image.get_rect(topleft = (x,y+4*resizing_factor))
        elif direction == 'down':
            self.rect = self.image.get_rect(
                topleft = (x+4*resizing_factor,y+14*resizing_factor))
        elif direction == 'right':
            self.rect = self.image.get_rect(
                topleft = (x+14*resizing_factor,y+4*resizing_factor))
        self.direction = direction
        self.hitbox = self.rect.inflate(PROJECTILE_HITBOX,PROJECTILE_HITBOX)
        sound_manager.player_shooting_sound.play()
    
    def destroy(self):
        """Checks for collisions and if the bullet has left the screen.
        We also deduct from the enemy's health if there was a collision.
        """

        # checkingi f the bullet has left the screen
        if not  -10 < self.rect.centerx < 10+528*resizing_factor: self.kill()
        elif not -10 < self.rect.centery < 10+320*resizing_factor: self.kill()

        # collision with the walls
        for sprite in wall_group:
            if self.rect.colliderect(sprite.rect):
                self.kill()  

        # collision with other bullets
        for sprite in tank1234_bullet_group:
            if sprite.type == 4 and self.rect.colliderect(sprite.rect):
                self.kill()
            elif sprite.type == 3 and bullet_collide(self,sprite):
                explosions_and_collapse_group.add(
                        ExplosionsAndCollapseAnimations(sprite.rect.centerx,
                            sprite.rect.centery,'grenade explosion'))
                self.kill()
            elif ((sprite.type == 1 or sprite.type == 2) and
                    bullet_collide(self,sprite)):
                    self.kill()
                    sprite.kill()

    def update(self):
        """Moves the bullet and checks if it has to be destroyed."""

        if self.direction == 'up': self.rect.y -= PLAYER_BULLET_SPEED
        elif self.direction == 'down': self.rect.y += PLAYER_BULLET_SPEED
        elif self.direction == 'left': self.rect.x -= PLAYER_BULLET_SPEED
        elif self.direction == 'right': self.rect.x += PLAYER_BULLET_SPEED
        self.hitbox.center = self.rect.center
        self.destroy()


class TankBullet1234(pg.sprite.Sprite):
    """Manages the projectiles of the first four tanks (every one of them except
    the laser shooter).
    """

    def __init__(self,x,y,type,direction,bullet_speed,*args):
        super().__init__()

        # directions are [up,left,down,right] -> [0,1,2,3]
        self.direction = direction
        self.type = type
        
        if self.type == 1 or self.type == 2:
            self.image = pg.image.load(
                f'images/enemies/tank{self.type}'
                f'/tank{self.type}_bullet.png').convert_alpha()
            self.image = pg.transform.scale2x(self.image)
            if resizing_factor == 4:
                self.image = pg.transform.scale2x(self.image)

        # grenades and sound waves have more than 1 images (they are not squares)
        if self.type == 3:
            if self.direction == 0: self.image = pg.image.load(
                'images/enemies/tank3/grenade_up.png').convert_alpha()
            elif self.direction == 1: self.image = pg.image.load(
                'images/enemies/tank3/grenade_left.png').convert_alpha()
            elif self.direction == 2: self.image = pg.image.load(
                'images/enemies/tank3/grenade_down.png').convert_alpha()
            elif self.direction == 3: self.image = pg.image.load(
                'images/enemies/tank3/grenade_right.png').convert_alpha()
            self.image = pg.transform.scale2x(self.image)
            if resizing_factor == 4:
                self.image = pg.transform.scale2x(self.image)
        if self.type == 4:
            if self.direction == 0: self.image = pg.image.load(
                'images/enemies/tank4/soundwave_up.png').convert_alpha()
            elif self.direction == 1: self.image = pg.image.load(
                'images/enemies/tank4/soundwave_left.png').convert_alpha()
            elif self.direction == 2: self.image = pg.image.load(
                'images/enemies/tank4/soundwave_down.png').convert_alpha()
            elif self.direction == 3: self.image = pg.image.load(
                'images/enemies/tank4/soundwave_right.png').convert_alpha()
            self.image = pg.transform.scale2x(self.image)
            if resizing_factor == 4:
                self.image = pg.transform.scale2x(self.image)
        
        # next we set the rects, we have to properly align them so it looks like
        # the tanks are actually shooting them
        if self.type == 1:
            self.speed = bullet_speed
            if self.direction == 0: self.rect = self.image.get_rect(
                topleft = (x+4*resizing_factor,y+4*resizing_factor))
            elif self.direction == 1: self.rect = self.image.get_rect(
                topleft = (x+4*resizing_factor,y+4*resizing_factor))
            elif self.direction == 2: self.rect = self.image.get_rect(
                topleft = (x+4*resizing_factor,y+7*resizing_factor))
            elif self.direction == 3: self.rect = self.image.get_rect(
                topleft = (x+7*resizing_factor,y+4*resizing_factor))
            self.hitbox = self.rect.inflate(PROJECTILE_HITBOX,PROJECTILE_HITBOX)
        if self.type == 2:
            self.speed = bullet_speed
            if self.direction == 0: self.rect = self.image.get_rect(
                topleft = (x+6*resizing_factor,y))
            elif self.direction == 1: self.rect = self.image.get_rect(
                topleft = (x,y+6*resizing_factor))
            elif self.direction == 2: self.rect = self.image.get_rect(
                topleft = (x+6*resizing_factor,y+14*resizing_factor))
            elif self.direction == 3: self.rect = self.image.get_rect(
                topleft = (x+14*resizing_factor,y+6*resizing_factor))
            self.hitbox = self.rect.inflate(PROJECTILE_HITBOX,PROJECTILE_HITBOX)
        if self.type == 3:
            self.speed = bullet_speed
            if self.direction == 0: self.rect = self.image.get_rect(
                topleft = (x+4*resizing_factor,y-6*resizing_factor))
            elif self.direction == 1: self.rect = self.image.get_rect(
                topleft = (x-6*resizing_factor,y+4*resizing_factor))
            elif self.direction == 2: self.rect = self.image.get_rect(
                topleft = (x+4*resizing_factor,y+16*resizing_factor))
            elif self.direction == 3: self.rect = self.image.get_rect(
                topleft = (x+16*resizing_factor,y+4*resizing_factor))
            self.hitbox = self.rect.inflate(PROJECTILE_HITBOX,PROJECTILE_HITBOX)
        if self.type == 4:
            self.speed = bullet_speed
            if self.direction == 0: self.rect = self.image.get_rect(
                topleft = (x,y-6*resizing_factor))
            elif self.direction == 1: self.rect = self.image.get_rect(
                topleft = (x-6*resizing_factor,y))
            elif self.direction == 2: self.rect = self.image.get_rect(
                topleft = (x,y+13*resizing_factor))
            elif self.direction == 3: self.rect = self.image.get_rect(
                topleft = (x+13*resizing_factor,y))
            # with the music this sound is too annoying so we only play it when
            # the music is muted
            if not args and mute_button_state:
                sound_manager.play_soundwave_sound = True

    def movement(self):
        """Moves the projectile in the proper direction.""" 

        if self.direction == 0: self.rect.y -= self.speed
        elif self.direction == 1: self.rect.x -= self.speed
        elif self.direction == 2: self.rect.y += self.speed
        elif self.direction == 3: self.rect.x += self.speed
        if not self.type == 4:
            self.hitbox.center = self.rect.center

    def collision(self):
        """Checks if the projectile has collided or left the screen and also
        destroys it if necessary.
        """

        if not  -10 < self.rect.centerx < 10+528*resizing_factor: self.kill()
        elif not -10 < self.rect.centery < 10+320*resizing_factor: self.kill()

        for sprite in wall_group:
            if self.rect.colliderect(sprite.rect):
                if self.type == 3:
                    explosions_and_collapse_group.add(
                        ExplosionsAndCollapseAnimations(self.rect.centerx,
                            self.rect.centery,'grenade explosion'))
                self.kill()

        for sprite in objectives_group:
            if self.rect.colliderect(sprite.rect):
                self.kill()

    def update(self):
        """Updates the projectile instances."""

        self.collision()
        self.movement()


class ExplosionsAndCollapseAnimations(pg.sprite.Sprite):
    """Handles the animation of the explosion of enemy tanks and grenades
    and the collapse of the objective buildings.
    """

    def __init__(self,x,y,string,*size):
        super().__init__()
        self.images = []

        if string == 'explosion':
            sound_manager.enemy_explosion_sound.play()
            self.type = 'explosion'
            for i in [i for i in range(1,7)]:
                self.image = pg.image.load(
                    'images/enemies/enemy_explosion'
                    f'/enemy_explosion{i}.png').convert_alpha()
                self.image = pg.transform.scale2x(self.image)
                self.image = pg.transform.scale2x(self.image)
                if resizing_factor == 4:
                    self.image = pg.transform.scale2x(self.image)
                if size and size[0] == 'big':
                    self.image = pg.transform.scale2x(self.image)
                elif size and size[0] == 'huge':
                    self.image = pg.transform.scale2x(self.image)
                    self.image = pg.transform.scale2x(self.image)
                self.images.append(self.image)

        elif string == 'collapse':
            sound_manager.building_collapse_sound.play()
            self.type = 'collapse'
            for i in [i for i in range(1,6)]:
                self.image = pg.image.load(
                    'images/other'
                    f'/comm_station_collapse_animation{i}.png').convert_alpha()
                self.image = pg.transform.scale2x(self.image)
                self.image = pg.transform.scale2x(self.image)
                if resizing_factor == 4:
                    self.image = pg.transform.scale2x(self.image)
                self.images.append(self.image)

        elif string == 'grenade explosion':
            sound_manager.play_grenade_sound = True
            self.type = 'grenade explosion'
            for i in [i for i in range(1,5)]:
                self.image = pg.image.load(
                    'images/enemies/tank3'
                    f'/grenade_explosion{i}.png').convert_alpha()
                self.image = pg.transform.scale2x(self.image)
                if resizing_factor == 4:
                    self.image = pg.transform.scale2x(self.image)
                self.images.append(self.image)
        self.image = self.images[0]
        self.rect = self.image.get_rect(center=(x,y))
        self.timer = 0
        self.animation_index = 1

    def update(self):
        """Animates the explosions and collapse and also checks if there is
        anything inside the grenade blast radius.
        Type 1, 2 tanks and the player getting caught in the blast radius
        takes damage. It also explodes any other grenades that are inside of it.
        """

        if self.type == 'grenade explosion':
            tank_inside_blast_radius = pg.sprite.spritecollide(
                self,enemies_group,False,pg.sprite.collide_circle)
            if tank_inside_blast_radius:
                for sprite in tank_inside_blast_radius:
                    if sprite.type == 1 or sprite.type == 2:
                        sprite.health -= 1
            player_inside_blast_radius = pg.sprite.spritecollide(
                self,player_group,False,pg.sprite.collide_circle)
            if player_inside_blast_radius:
                player_group.sprite.damage_checker(type='grenade explosion')
            projectile_inside_blast_radius = pg.sprite.spritecollide(
                self,tank1234_bullet_group,False,pg.sprite.collide_circle)
            if projectile_inside_blast_radius:
                for sprite in projectile_inside_blast_radius:
                    if sprite.type == 3:
                        explosions_and_collapse_group.add(
                            ExplosionsAndCollapseAnimations(self.rect.centerx,
                                self.rect.centery,'grenade explosion'))
                        sprite.kill()

        if global_time_ms-self.timer > 100:
            if self.animation_index == len(self.images):
                self.kill()
            if self.animation_index < len(self.images):
                self.image = self.images[self.animation_index]
                self.animation_index += 1
                self.timer = global_time_ms


class Tank(pg.sprite.Sprite):
    """Handles the initialization, pathfinding, shooting and movement
    of the enemies. It is used for all 5 kinds of enemies.
    """

    def __init__(self,type,stat_info_dict,spawn_location):
        """Initializes the enemy: puts it onto the randomized spawn point and
        gives it a goal location.
        """

        super().__init__()
        self.type = type
        self.images = []
        directions = ['up','left','down','right']

        # we have a lot more images for the type 5 tank than the rest
        if self.type == 5:
            self.charge1_images = []
            self.charge2_images = []
            self.shoot_images = []
            self.default_images = []
            for direction in directions:
                self.image = pg.image.load(
                    f'images/enemies/tank{type}'
                    f'/tank{type}_shoot_{direction}.png').convert_alpha()
                self.image = pg.transform.scale2x(self.image)
                if resizing_factor == 4:
                    self.image = pg.transform.scale2x(self.image)
                self.shoot_images.append(self.image)

                self.image = pg.image.load(
                    f'images/enemies/tank{type}'
                    f'/tank{type}_charge2_{direction}.png').convert_alpha()
                self.image = pg.transform.scale2x(self.image)
                if resizing_factor == 4:
                    self.image = pg.transform.scale2x(self.image)
                self.charge2_images.append(self.image)

                self.image = pg.image.load(
                    f'images/enemies/tank{type}'
                    f'/tank{type}_charge1_{direction}.png').convert_alpha()
                self.image = pg.transform.scale2x(self.image)
                if resizing_factor == 4:
                    self.image = pg.transform.scale2x(self.image)
                self.charge1_images.append(self.image)

                self.image = pg.image.load(
                    f'images/enemies/tank{type}'
                    f'/tank{type}_default_{direction}.png').convert_alpha()
                self.image = pg.transform.scale2x(self.image)
                if resizing_factor == 4:
                    self.image = pg.transform.scale2x(self.image)
                self.default_images.append(self.image)
            self.images = self.default_images

        # for the other 4 we only have 4 images
        else:
            for direction in directions:
                self.image = pg.image.load(
                    'images/enemies'
                    f'/tank{type}/tank{type}_{direction}.png').convert_alpha()
                self.image = pg.transform.scale2x(self.image)
                if resizing_factor == 4:
                    self.image = pg.transform.scale2x(self.image)
                self.images.append(self.image)

        # we also want to move the type 4 and 5 tanks with less than 1 speed so
        # we need a timer for that
        if self.type == 4 or self.type == 5:
            self.speed_timer = 0
        
        self.spawn_location = spawn_location
        self.rect = self.image.get_rect(
            center=(self.spawn_location[0],self.spawn_location[1]))
        self.current_position = (self.rect.centerx,self.rect.centery)
        
        self.near_player_tiles = pg.sprite.Group()
        self.restricted_probable_tiles = pg.sprite.Group()
        self.goal = (0,0)
        self.goal_tile = None
        self.current = (self.rect.centerx,self.rect.centery)
        self.path = deque()
        self.new_goal_finder()
        self.next_destination = self.path.popleft()

        self.health = stat_info_dict['health']
        self.speed = stat_info_dict['speed']
        self.bullet_speed = stat_info_dict['bullet speed']
        self.last_shoot_time = global_time_ms
        if self.type == 1:
            self.next_shoot_time = TYPE_1_SHOOTING
        elif self.type == 2:
            self.next_shoot_time = TYPE_2_SHOOTING
        elif self.type == 3:
            self.next_shoot_time = TYPE_3_SHOOTING
        elif self.type == 4:
            self.next_shoot_time = TYPE_4_SHOOTING
        elif self.type == 5:
            self.next_shoot_time = TYPE_5_SHOOTING

        # the indices are: 0 - up, 1 - left, 2 - down, 3 - right
        self.direction_index = 0

    def destroy(self):
        """Removes the sprite from the group when destroyed and instantiates an
        explosion animation.
        """

        global spawned_enemy_numbers
        global destroyed_overall_enemies
        global extra_life_counter

        if self.health < 1:
            explosions_and_collapse_group.add(
                ExplosionsAndCollapseAnimations(
                    self.rect.centerx,self.rect.centery,'explosion'))
            self.kill()
            spawned_enemy_numbers[self.type-1] -= 1
            destroyed_overall_enemies[self.type-1] += 1
            extra_life_counter += 1

    def new_goal_finder(self):
        """Determines the probably goal tiles for each tank. These calculations
        depend on the type of said tank and the stage we are on.
        """
        # first we remove the tile the enemy is currently standing on
        # (it would raise an IndexError later because of the empty path)
        self.restricted_probable_tiles = probable_goal_tile_group.copy()
        for tile in self.restricted_probable_tiles:
            if (tile.rect.x//(16*resizing_factor) == self.rect.centerx//(16*resizing_factor) and
                tile.rect.y//(16*resizing_factor) == self.rect.centery//(16*resizing_factor)):
                self.restricted_probable_tiles.remove(tile)
        
        # on the last stage for the type 1-3 tanks we want the goal to be in a
        # 18 tile radius circle around the player's current position
        if (self.type == 1 or self.type == 2 or self.type == 3) and index_of_current_map == 8:
            self.near_player_tiles.empty()
            for sprite in self.restricted_probable_tiles:
                if ((player_group.sprite.rect.centerx-sprite.rect.centerx)**2
                        + (player_group.sprite.rect.centery-sprite.rect.centery)**2
                        < (18*16*resizing_factor)**2):
                    self.near_player_tiles.add(sprite)
            self.goal_tile = random.choice(self.near_player_tiles.sprites())

        # on the other stages for the type 1-3 tanks we want the goal to be in a
        # 8 tile radius circle around the player's current position
        # this will make them seem liek they are following us not just randomly
        # wandering but also not straight up hunting us knowing our exact 
        # position, that would be too hard; this way the type 1 tank will always
        # pester us (because they are the fastest) and it will be harder to camp
        elif (self.type == 1 or self.type == 2 or self.type == 3) and (not index_of_current_map == 8):
            self.near_player_tiles.empty()
            for sprite in self.restricted_probable_tiles:
                if ((player_group.sprite.rect.centerx-sprite.rect.centerx)**2
                        + (player_group.sprite.rect.centery-sprite.rect.centery)**2
                        < (8*16*resizing_factor)**2):
                    self.near_player_tiles.add(sprite)
            self.goal_tile = random.choice(self.near_player_tiles.sprites())
        
        # for the big tanks we just let them wander around, their projectiles are
        # way more dangerous than some of the weaker enemies (mainly because we
        # can't destroy them)
        else:
            self.goal_tile = random.choice(self.restricted_probable_tiles.sprites())
        
        # with the goal set we calculate the path
        self.goal = (
            self.goal_tile.rect.x+8*resizing_factor,self.goal_tile.rect.y+8*resizing_factor)
        self.current = (self.rect.centerx,self.rect.centery)
        self.path = pathfinding(self.current,self.goal)

    def movement(self):
        """Takes care of the movement of the enemies."""

        # if they've reached the goal we set a new one and calculate the new path
        if (distance > (self.goal[0]-self.rect.centerx)**2
                        + (self.goal[1]-self.rect.centery)**2):
            self.new_goal_finder()
            self.next_destination = self.path.popleft()
            
        # if they haven't reached the goal but have reached the next destination
        # (tile) we set the next tile in the path as the new destination
        elif (distance > (self.next_destination[0]-self.rect.centerx)**2
                            + (self.next_destination[1]-self.rect.centery)**2):
            self.next_destination = self.path.popleft()

        #otherwise we calculate the direction we have to move along and then move
        else:
            direction = (self.next_destination[0]-self.rect.centerx,
                        self.next_destination[1]-self.rect.centery)
            # we set it to < 17 (milliseconds) so the big tanks only move every
            # two frames (0.5 speed)
            if ((self.type == 4 or self.type == 5)
                    and global_time_ms-self.speed_timer < 17):
                return

            if direction[0] > 0 and direction[1] >= 0:
                self.rect.centerx += self.speed
                self.direction_index = 3
                self.image = self.images[self.direction_index]
            elif direction[0] <= 0 and direction[1] > 0:
                self.rect.centery += self.speed
                self.direction_index = 2
                self.image = self.images[self.direction_index]
            elif direction[0] < 0 and direction[1] <= 0:
                self.rect.centerx -= self.speed
                self.direction_index = 1
                self.image = self.images[self.direction_index]
            elif direction[0] >= 0 and direction[1] < 0:
                self.rect.centery -= self.speed
                self.direction_index = 0
                self.image = self.images[self.direction_index]
            if self.type == 4 or self.type == 5:
                self.speed_timer = global_time_ms
        
        # not every tank's image is a square so their rect's orientation matters
        self.rect = self.image.get_rect(
            center=(self.rect.centerx,self.rect.centery))

    def bullet_collision(self):
        """Checks if one of the player's bullets has hit the tank or not. If yes
        then it also reduces the tank's health and destroy's the bullet sprite.
        """

        for sprite in player_bullets_group:
            if self.rect.colliderect(sprite.rect):
                sound_manager.enemy_hit_channel.play(sound_manager.enemy_hit_sound)
                sprite.kill()
                self.health -= 1

    def shooting(self):
        """Responsible for the management of the enemy shooting of the type 1-4
        enemies.
        """

        if global_time_ms-self.last_shoot_time > self.next_shoot_time:
            tank1234_bullet_group.add(
                TankBullet1234(self.rect.x,self.rect.y,self.type,
                self.images.index(self.image),self.bullet_speed))
            self.last_shoot_time = global_time_ms
            if self.type == 1:
                self.next_shoot_time = TYPE_1_SHOOTING
            elif self.type == 2:
                self.next_shoot_time = TYPE_2_SHOOTING
            elif self.type == 3:
                self.next_shoot_time = TYPE_3_SHOOTING
            elif self.type == 4:
                self.next_shoot_time = TYPE_4_SHOOTING
        
    def pathfinding_reset(self):
        """Gets a new goal and path for a tank."""

        self.new_goal_finder()
        self.next_destination = self.path.popleft()

    def update(self):
        """Updates the tank sprite instance."""

        self.shooting()
        self.bullet_collision()
        self.destroy()
        self.movement()
        

class LaserTank(Tank):
    """A subclass of Tank for the mroe specialized laser tanks."""

    def __init__(self,type,stat_info_dict,spawn_location):
        super().__init__(type,stat_info_dict,spawn_location)
        self.laser_group = pg.sprite.Group()
        self.shooting_flag = False
        self.stand_still = False
        self.beam_fade = False
        self.charge_duration = 0
        self.beam_alpha = 255
        self.signal_to_sound_sent = False

    def laser_shooting(self):
        """After the tank stops it charges the laser then begins to advance
        the beam. If the first laser sprite already collides with a wall it
        terminates the advancement.
        """

        # we start the charging of the laser
        if not self.shooting_flag:
            if self.charge_duration > LASER_CHARGE_TIME:
                self.shooting_flag = True
            if self.charge_duration <= int(LASER_CHARGE_TIME/4):
                self.charge_duration += 17
            elif self.charge_duration <= int(LASER_CHARGE_TIME/2):
                self.charge_duration += 17
                self.image = self.charge1_images[self.direction_index]
            elif self.charge_duration <= int(3*LASER_CHARGE_TIME/4):
                self.charge_duration += 17
                self.image = self.charge2_images[self.direction_index]
            elif self.charge_duration <= LASER_CHARGE_TIME:
                self.charge_duration += 17
                self.image = self.shoot_images[self.direction_index]
        # if charged, we begin the shooting of the laser beam
        elif self.shooting_flag:
            self.charge_duration = 0
            self.beam_alpha = 255
            self.beam_fade = True
            self.image = self.images[self.direction_index]
            self.next_shoot_time = abs(int(random.gauss(mu=9,sigma=1.5))*1000)
            self.last_shoot_time = global_time_ms
            # we add a starting laser sprite
            self.laser_group.add(
                LaserStart(self.rect.centerx,
                            self.rect.centery,
                            self.images.index(self.image)))
            beam_sprite_list = self.laser_group.sprites()
            latest_beam_sprite = beam_sprite_list[0]
            # we check if it has already collided with a wall or not; if yes
            # then we stop the advancement of the laser beam
            reached_wall = pg.sprite.spritecollide(
                    latest_beam_sprite,wall_group,False,pg.sprite.collide_rect)
            if reached_wall:
                self.shooting_flag = False
                return
            self.beam_adder()
                 
    def beam_adder(self):
        """Advances the laser beam. At each new sprite it check if the beam has
        collided with a wall or left the screen or not. If yes then it
        terminates the advancement of the beam.
        """

        # it's long because we can advance in 4 different directions:
        # as usual 0 -> 3 is analoguous to going counter clockwise starting
        # from north
        beam_advancing = True
        direction = self.images.index(self.image)
        # beam advancing towards north
        if direction == 0:
            x = self.rect.centerx
            y = self.rect.centery - (16*resizing_factor)*2
            beam_index = 1
            while beam_advancing:
                self.laser_group.add(LaserBeam(x,y,self.images.index(self.image)))
                beam_sprite_list = self.laser_group.sprites()
                latest_beam_sprite = beam_sprite_list[beam_index]
                reached_wall = pg.sprite.spritecollide(
                    latest_beam_sprite,wall_group,False,pg.sprite.collide_rect)
                if reached_wall:
                    beam_advancing = False
                    return
                if latest_beam_sprite.rect.y < (-16*resizing_factor):
                    beam_advancing = False
                    return
                y -= 16*resizing_factor
                beam_index += 1

        # beam advancing towards west        
        elif direction == 1:
            x = self.rect.centerx - (16*resizing_factor)*2
            y = self.rect.centery
            beam_index = 1
            while beam_advancing:
                self.laser_group.add(LaserBeam(x,y,self.images.index(self.image)))
                beam_sprite_list = self.laser_group.sprites()
                latest_beam_sprite = beam_sprite_list[beam_index]
                reached_wall = pg.sprite.spritecollide(
                    latest_beam_sprite,wall_group,False,pg.sprite.collide_rect)
                if reached_wall:
                    beam_advancing = False
                    return
                if latest_beam_sprite.rect.x < (-16*resizing_factor):
                    beam_advancing = False
                    return
                x -= 16*resizing_factor
                beam_index += 1

        # beam advancing towards south
        elif direction == 2:
            x = self.rect.centerx
            y = self.rect.centery + (16*resizing_factor)*2
            beam_index = 1
            while beam_advancing:
                self.laser_group.add(LaserBeam(x,y,self.images.index(self.image)))
                beam_sprite_list = self.laser_group.sprites()
                latest_beam_sprite = beam_sprite_list[beam_index]
                reached_wall = pg.sprite.spritecollide(
                    latest_beam_sprite,wall_group,False,pg.sprite.collide_rect)
                if reached_wall:
                    beam_advancing = False
                    return
                if latest_beam_sprite.rect.y > (320+16)*resizing_factor:
                    beam_advancing = False
                    return
                y += 16*resizing_factor
                beam_index += 1

        # beam advancing towards east
        elif direction == 3:
            x = self.rect.centerx + (16*resizing_factor)*2
            y = self.rect.centery
            beam_index = 1
            while beam_advancing:
                self.laser_group.add(LaserBeam(x,y,self.images.index(self.image)))
                beam_sprite_list = self.laser_group.sprites()
                latest_beam_sprite = beam_sprite_list[beam_index]
                reached_wall = pg.sprite.spritecollide(
                    latest_beam_sprite,wall_group,False,pg.sprite.collide_rect)
                if reached_wall:
                    beam_advancing = False
                    return
                if latest_beam_sprite.rect.x > (528+16)*resizing_factor:
                    beam_advancing = False
                    return
                x += 16*resizing_factor
                beam_index += 1
        
    def duration_checker(self):
        """Checks if a tank should start charging and shooting."""

        if (self.last_shoot_time+self.next_shoot_time-global_time_ms <
            LASER_CHARGE_TIME):
            self.stand_still = True
            if not self.signal_to_sound_sent:
                sound_manager.play_laser_sound = True
                self.signal_to_sound_sent = True

    def beam_fading(self):
        """After a laser beam collides or leaves the screen this method gradually
        fades it.
        """

        if self.beam_alpha <= 0:
            self.laser_group.empty()
            self.shooting_flag = False
            self.stand_still = False
            self.beam_fade = False
            self.signal_to_sound_sent = False
            
        for sprite in self.laser_group:
            sprite.image.set_alpha(self.beam_alpha)
        self.beam_alpha -= int((255*17)/LASER_BEAM_FADE_TIME)

    def beam_collision(self):
        """Checks if the laser beam is colliding with the following or not:
        player, player's bullets, projectiles of type 1-4 tanks. Every type 1-4
        tank projectile and the player's bullets that collide with the beam 
        get destroyed (the grenades explode).
        """

        for beam in self.laser_group:
            for bullet in tank1234_bullet_group:
                if beam.rect.colliderect(bullet.rect):
                    if bullet.type == 3:
                        explosions_and_collapse_group.add(
                            ExplosionsAndCollapseAnimations(bullet.rect.centerx,
                                bullet.rect.centery,'grenade explosion'))
                    bullet.kill()
            for bullet in player_bullets_group:
                if beam.rect.colliderect(bullet.rect): bullet.kill()
            if beam.rect.colliderect(player_group.sprite.rect):
                if player_group.sprite.accepting_damage:
                    player_group.sprite.damage_checker(type='beam')

    def win_wait_update(self):
        """During the main building explosion makes sure the fired laser beams
        still advance or fade.
        """

        self.beam_collision()
        self.beam_fading()

    def update(self):
        """Manages the updating of the laser tank instance and the laser
        beam.
        """

        self.destroy()
        self.bullet_collision()
        self.duration_checker()
        if self.stand_still:
            if not self.beam_fade:
                self.laser_shooting()
                self.beam_collision()
            else:
                self.beam_collision()
                self.beam_fading()
        elif not self.stand_still:
            self.movement()


class LaserStart(pg.sprite.Sprite):
    """A class for the very first sprite of a laser beam."""

    def __init__(self,x,y,direction):
        super().__init__()

        # 4 diferent directions to shoot -> 4 different images
        if direction == 0:
            self.image = pg.image.load(
                'images/enemies/tank5/laser_start_up.png').convert_alpha()
            self.image = pg.transform.scale2x(self.image)
            if resizing_factor == 4:
                self.image = pg.transform.scale2x(self.image)
            self.rect = self.image.get_rect(
                center = (x,y-16*resizing_factor))

        elif direction == 1:
            self.image = pg.image.load(
                'images/enemies/tank5/laser_start_left.png').convert_alpha()
            self.image = pg.transform.scale2x(self.image)
            if resizing_factor == 4:
                self.image = pg.transform.scale2x(self.image)
            self.rect = self.image.get_rect(
                center = (x-16*resizing_factor,y))

        elif direction == 2:
            self.image = pg.image.load(
                'images/enemies/tank5/laser_start_down.png').convert_alpha()
            self.image = pg.transform.scale2x(self.image)
            if resizing_factor == 4:
                self.image = pg.transform.scale2x(self.image)
            self.rect = self.image.get_rect(
                center = (x,y+16*resizing_factor))

        elif direction == 3:
            self.image = pg.image.load(
                'images/enemies/tank5/laser_start_right.png').convert_alpha()
            self.image = pg.transform.scale2x(self.image)
            if resizing_factor == 4:
                self.image = pg.transform.scale2x(self.image)
            self.rect = self.image.get_rect(
                center = (x+16*resizing_factor,y))
        

class LaserBeam(pg.sprite.Sprite):
    """Outside the very first laser beam sprite every other part of the beam
    wil be an instance of this class. These only have two orientations.
    """

    def __init__(self,x,y,direction):
        super().__init__()

        # vertical
        if direction == 0 or direction == 2:
            self.image = pg.image.load(
                'images/enemies/tank5/laser_vertical.png').convert_alpha()
            self.image = pg.transform.scale2x(self.image)
            if resizing_factor == 4:
                self.image = pg.transform.scale2x(self.image)

        # horizontal
        elif direction == 1 or direction == 3:
            self.image = pg.image.load(
                'images/enemies/tank5/laser_horizontal.png').convert_alpha()
            self.image = pg.transform.scale2x(self.image)
            if resizing_factor == 4:
                self.image = pg.transform.scale2x(self.image)

        self.rect = self.image.get_rect(center = (x,y))


class ShieldPowerUp(pg.sprite.Sprite):
    """A class for the shield power up."""

    def __init__(self,x,y):
        super().__init__()
        self.image = pg.image.load(
            'images/player/shield_upgrade.png').convert_alpha()
        self.image = pg.transform.scale2x(self.image)
        if resizing_factor == 4:
            self.image = pg.transform.scale2x(self.image)
        self.rect = self.image.get_rect(center=(x,y))
        self.timer = global_time_ms

    def update(self):
        """Checks if the power up should be despawned and destroys the sprite
        if yes.
        """

        if global_time_ms-self.timer > SHIELD_DESPAWN_TIME:
            self.kill()


class SpawnAnimation(pg.sprite.Sprite):
    """Class for the spawn animations of the enemies. I could probably
    have made it more easily like the player's spawn animation but whatever.
    """

    def __init__(self,tank_type,tank_stat_info_dict,spawn_location):
        super().__init__()
        self.tank_type = tank_type
        self.tank_stat_info_dict = tank_stat_info_dict
        self.spawn_location = spawn_location
        self.timer = 0
        self.duration = 0
        self.animation_index = 0
        self.images = []
        for index in [x for x in range(1,4)]:
            self.image = pg.image.load(
                'images/other'
                f'/spawn_location_animation{index}.png').convert_alpha()
            self.image = pg.transform.scale2x(self.image)
            if resizing_factor == 4:
                    self.image = pg.transform.scale2x(self.image)
            self.images.append(self.image)
        self.image = self.images[0]
        self.images.reverse()
        self.rect = self.image.get_rect(
            center=(self.spawn_location[0],self.spawn_location[1]))

    def update(self):
        """Plays the animation and when it ends spawns the appropriate enemy in
        its position.
        """

        if not global_time_ms-self.timer > 100:
            return
        if self.duration > 900:
            if self.tank_type == 5:
                enemies_group.add(LaserTank(
                    self.tank_type,self.tank_stat_info_dict,self.spawn_location))
                self.kill()
            else:
                enemies_group.add(Tank(
                    self.tank_type,self.tank_stat_info_dict,self.spawn_location))
                self.kill()
        else:
            if self.animation_index >= 2:
                self.animation_index = 0
                self.image = self.images[self.animation_index]
                self.timer = global_time_ms
                self.duration += 100
            else:
                self.image = self.images[self.animation_index]
                self.animation_index += 1
                self.timer = global_time_ms
                self.duration += 100


class MainBase(pg.sprite.Sprite):
    """Class for the main building on the last stage."""

    def __init__(self):
        super().__init__()
        self.image = pg.image.load('images/other/mainbase.png').convert_alpha()
        self.image = pg.transform.scale2x(self.image)
        if resizing_factor == 4:
            self.image = pg.transform.scale2x(self.image)
        self.rect = self.image.get_rect(
            topleft=(30*16*resizing_factor,9*16*resizing_factor))
        self.last_shoot_time = global_time_ms
        self.secondary_shoot_timer = 0
        self.soundwave_group = pg.sprite.Group()
        self.bullet_group = pg.sprite.Group()
        self.projectile_speed = MAIN_BASE_PROJECTILE_SPEED
        self.shooting_wave_phase = 1
        self.health = MAIN_BASE_HEALTH
        self.explosion_timer = 0
        self.first_explosion_done = False
        self.second_explosion_done = False
        self.third_explosion_done = False
        self.fourth_explosion_done = False
        self.final_explosion_done = False

    def shooting(self):
        """Manages the shooting of the building."""

        if global_time_ms-self.last_shoot_time < MAIN_BASE_WAVE_SHOOT_TIMER:
            return
        # pattern from left to right: soundwave - soundwave - bullet
        if self.shooting_wave_phase == 1:
            # top row
            self.soundwave_group.add(TankBullet1234(30*16*resizing_factor,
                9*16*resizing_factor,4,0,self.projectile_speed,'base'))
            self.soundwave_group.add(TankBullet1234(31*16*resizing_factor,
                9*16*resizing_factor,4,0,self.projectile_speed,'base'))
            self.bullet_group.add(TankBullet1234((32*16+3)*resizing_factor,
                (9*16-5)*resizing_factor,1,0,self.projectile_speed))
            # bottom row
            self.soundwave_group.add(TankBullet1234(30*16*resizing_factor,
                11*16*resizing_factor,4,2,self.projectile_speed,'base'))
            self.soundwave_group.add(TankBullet1234(31*16*resizing_factor,
                11*16*resizing_factor,4,2,self.projectile_speed,'base'))
            self.bullet_group.add(TankBullet1234((32*16+3)*resizing_factor,
                (11*16+7)*resizing_factor,1,2,self.projectile_speed))
            self.last_shoot_time = global_time_ms
            self.shooting_wave_phase = 2

        # pattern from left to right: bullet - soundwave - soundwave
        elif self.shooting_wave_phase == 2:
            # top row
            self.bullet_group.add(TankBullet1234((30*16+3)*resizing_factor,
                (9*16-5)*resizing_factor,1,0,self.projectile_speed))
            self.soundwave_group.add(TankBullet1234(31*16*resizing_factor,
                11*16*resizing_factor,4,2,self.projectile_speed,'base'))
            self.soundwave_group.add(TankBullet1234(32*16*resizing_factor,
                11*16*resizing_factor,4,2,self.projectile_speed,'base'))
            # bottom row
            self.bullet_group.add(TankBullet1234((30*16+3)*resizing_factor,
                (11*16+7)*resizing_factor,1,2,self.projectile_speed))
            self.soundwave_group.add(TankBullet1234(31*16*resizing_factor,
                9*16*resizing_factor,4,0,self.projectile_speed,'base'))
            self.soundwave_group.add(TankBullet1234(32*16*resizing_factor,
                9*16*resizing_factor,4,0,self.projectile_speed,'base'))
            self.last_shoot_time = global_time_ms
            self.shooting_wave_phase = 3
        
        # here we only shoot soundwave projectiles
        elif self.shooting_wave_phase == 3:
            self.soundwave_group.add(TankBullet1234(30*16*resizing_factor,
                11*16*resizing_factor,4,2,self.projectile_speed,'base'))
            self.soundwave_group.add(TankBullet1234(31*16*resizing_factor,
                11*16*resizing_factor,4,2,self.projectile_speed,'base'))
            self.soundwave_group.add(TankBullet1234(32*16*resizing_factor,
                11*16*resizing_factor,4,2,self.projectile_speed,'base'))
            self.soundwave_group.add(TankBullet1234(30*16*resizing_factor,
                9*16*resizing_factor,4,0,self.projectile_speed,'base'))
            self.soundwave_group.add(TankBullet1234(31*16*resizing_factor,
                9*16*resizing_factor,4,0,self.projectile_speed,'base'))
            self.soundwave_group.add(TankBullet1234(32*16*resizing_factor,
                9*16*resizing_factor,4,0,self.projectile_speed,'base'))
            self.last_shoot_time = global_time_ms
            self.shooting_wave_phase = 1

    def moving_the_projectiles(self):
        """Manages the movement of the building's projectiles."""

        for projectile in self.soundwave_group:
            if projectile.direction == 2:
                projectile.rect.y += self.projectile_speed
            elif projectile.direction == 0:
                projectile.rect.y -= self.projectile_speed
        for projectile in self.bullet_group:
            if projectile.direction == 2:
                projectile.rect.y += self.projectile_speed
                projectile.hitbox.center = projectile.rect.center
            elif projectile.direction == 0:
                projectile.rect.y -= self.projectile_speed
                projectile.hitbox.center = projectile.rect.center

    def collision(self):
        """Checks if the projectiles of the building have collided with the
        player or the player projectiles.
        Destroys the building's projectiles if they leave the screen.
        Also checks if the player's bullets have managed to hit the building.
        """

        for sprite in self.soundwave_group:
            if not -10 < sprite.rect.y < 10+320*resizing_factor: sprite.kill()
            for bullet in player_bullets_group:
                if sprite.rect.colliderect(bullet.rect): bullet.kill()
            if sprite.rect.colliderect(player_group.sprite.rect):
                player_group.sprite.damage_checker(type=4)
        
        for sprite in self.bullet_group:
            if not -10 < sprite.rect.y < 10+320*resizing_factor: sprite.kill()
            for bullet in player_bullets_group:
                if bullet_collide(bullet,sprite):
                    sprite.kill()
                    bullet.kill()
            if sprite.rect.colliderect(player_group.sprite.rect):
                player_group.sprite.damage_checker(type=1)
                sprite.kill()

        for sprite in player_bullets_group:
            if sprite.rect.colliderect(self.rect):
                sprite.kill()
                self.health -= 1
                sound_manager.base_hit_sound.play()
                if self.health < 1:
                    self.explosion_timer = global_time_ms

    def explosion(self):
        """After reduced to 0 health manages the explosion of the building."""

        global game_state

        if not self.first_explosion_done:
            explosions_and_collapse_group.add(
                ExplosionsAndCollapseAnimations(31*16*resizing_factor,
                                                10*16*resizing_factor,
                                                'explosion','big'))
            game_state = 'win wait'
            self.first_explosion_done = True

        elif (global_time_ms-self.explosion_timer > 600
                and self.second_explosion_done == False):
            explosions_and_collapse_group.add(
                ExplosionsAndCollapseAnimations(32*16*resizing_factor,
                                                11*16*resizing_factor,
                                                'explosion','big'))
            self.second_explosion_done = True

        elif (global_time_ms-self.explosion_timer > 1200
                and self.third_explosion_done == False):
            explosions_and_collapse_group.add(
                ExplosionsAndCollapseAnimations(32*16*resizing_factor,
                                                10*16*resizing_factor,
                                                'explosion','big'))
            self.third_explosion_done = True

        elif (global_time_ms-self.explosion_timer > 1800
                and self.fourth_explosion_done == False):
            explosions_and_collapse_group.add(
                ExplosionsAndCollapseAnimations(31*16*resizing_factor,
                                                11*16*resizing_factor,
                                                'explosion','big'))
            self.fourth_explosion_done = True

        elif (global_time_ms-self.explosion_timer > 2400
                and self.final_explosion_done == False):
            explosions_and_collapse_group.add(
                ExplosionsAndCollapseAnimations((31+0.5)*16*resizing_factor,
                                                (10+0.5)*16*resizing_factor,
                                                'explosion','huge'))
            sound_manager.base_big_channel.play(
                sound_manager.base_big_explosion)
            self.final_explosion_done = True

        elif global_time_ms-self.explosion_timer > 2800:
            game_state = 'end screen'
            screen.fill('Black')

    def update(self):
        """Updates the main building's instance."""

        if self.health > 0:
            self.shooting()
            self.moving_the_projectiles()
            self.collision()
        elif self.health < 1:
            self.explosion()
            self.moving_the_projectiles()


class MainBaseCenter(pg.sprite.Sprite):
    """Class for the centerpiece of the main ("boss") building."""
    
    def __init__(self):
        super().__init__()
        self.image = pg.image.load(
            'images/other/mainbase_middle.png').convert_alpha()
        self.image = pg.transform.scale2x(self.image)
        if resizing_factor == 4:
            self.image = pg.transform.scale2x(self.image)
        self.rect = self.image.get_rect(
            topleft=(31*16*resizing_factor,10*16*resizing_factor))


class SoundManager():
    """Handles eevry sound and piece of music in the game."""

    def __init__(self):
        # I've set up a few dedicated channels for the more important sounds
        self.laser_sound = pg.mixer.Sound('sound/sound_effects/laser_sound.mp3')
        self.laser_sound.set_volume(0.65)
        self.laser_channel_0 = pg.mixer.Channel(0)
        self.laser_channel_1 = pg.mixer.Channel(1)
        self.laser_channel_2 = pg.mixer.Channel(2)
        self.play_laser_sound = False
        self.laser_sound_index = 0

        self.soundwave_sound = pg.mixer.Sound(
            'sound/sound_effects/soundwave_shoot.mp3')
        self.soundwave_sound.set_volume(0.4)
        self.soundwave_channel_0 = pg.mixer.Channel(3)
        self.soundwave_channel_1 = pg.mixer.Channel(4)
        self.play_soundwave_sound = False
        self.soundwave_sound_index = 0

        self.grenade_sound = pg.mixer.Sound(
            'sound/sound_effects/grenade_explosion.mp3')
        self.grenade_sound.set_volume(0.35)
        self.grenade_channel_0 = pg.mixer.Channel(5)
        self.grenade_channel_1 = pg.mixer.Channel(6)
        self.play_grenade_sound = False
        self.grenade_sound_index = 0

        self.shield_upgrade_sound = pg.mixer.Sound(
            'sound/sound_effects/shield_upgrade.mp3')
        self.shield_upgrade_sound.set_volume(0.45)
        self.shield_upgrade_channel = pg.mixer.Channel(7)

        self.enemy_hit_sound = pg.mixer.Sound(
            'sound/sound_effects/enemy_hit.mp3')
        self.enemy_hit_sound.set_volume(0.35)
        self.enemy_hit_channel = pg.mixer.Channel(8)

        self.player_respawn_sound = pg.mixer.Sound(
            'sound/sound_effects/player_respawn.mp3')
        self.player_respawn_sound.set_volume(1.0)
        self.player_respawn_channel = pg.mixer.Channel(9)

        self.lava_damage_sound = pg.mixer.Sound(
            'sound/sound_effects/lava_damage.mp3')
        self.lava_damage_sound.set_volume(0.55)
        self.lava_damage_channel = pg.mixer.Channel(10)
        self.lava_damage_start = False
        self.lava_damage_end = False

        self.base_big_explosion = pg.mixer.Sound(
            'sound/sound_effects/base_big_explosion.mp3')
        self.base_big_explosion.set_volume(0.8)
        self.base_big_channel = pg.mixer.Channel(11)

        self.extra_life_sound = pg.mixer.Sound(
            'sound/sound_effects/extra_life.mp3')
        self.extra_life_sound.set_volume(1.0)
        self.extra_life_channel = pg.mixer.Channel(12)

        # below are the sounds without dedicated  channels
        self.player_hit_sound = pg.mixer.Sound(
            'sound/sound_effects/player_hit.mp3')
        self.player_hit_sound.set_volume(1.0)

        self.enemy_explosion_sound = pg.mixer.Sound(
            'sound/sound_effects/enemy_explosion.mp3')
        self.enemy_explosion_sound.set_volume(0.4)

        # comp - computer
        self.player_comp_sound = pg.mixer.Sound(
            'sound/sound_effects/player_comp.mp3')
        self.player_comp_sound.set_volume(1.0)

        self.enemy_comp_sound = pg.mixer.Sound(
            'sound/sound_effects/enemy_comp.mp3')
        self.enemy_comp_sound.set_volume(1.0)

        self.sec_comp_sound = pg.mixer.Sound(
            'sound/sound_effects/sec_comp.mp3')
        self.sec_comp_sound.set_volume(1.0)

        self.building_hit_sound = pg.mixer.Sound(
            'sound/sound_effects/building_hit.mp3')
        self.building_hit_sound.set_volume(0.85)

        self.building_collapse_sound = pg.mixer.Sound(
            'sound/sound_effects/building_collapse.mp3')
        self.building_collapse_sound.set_volume(0.65)

        self.player_shooting_sound = pg.mixer.Sound(
            'sound/sound_effects/player_shooting.mp3')
        self.player_shooting_sound.set_volume(0.4)

        self.button_click_sound = pg.mixer.Sound(
            'sound/sound_effects/button_click.mp3')
        self.button_click_sound.set_volume(1.0)

        # main base being damaged by player
        self.base_hit_sound = pg.mixer.Sound(
            'sound/sound_effects/base_hit.mp3')
        self.base_hit_sound.set_volume(0.25)

        self.intro_scope = ['start menu', 'manual']
        self.middle_music_scope = ([f'map_{x}' for x in range(2,9)]
                                    + ['summary screen'])
        self.silence_scope = which_text_screen + ['lose screen']

        self.intro_is_playing = False
        self.stage_1_music_is_playing = False
        self.middle_music_is_playing = False
        self.boss_music_is_playing = False
        self.credits_music_is_playing = False
        
    def dedicated_sound_channels(self):
        """Handles the playback of the sounds that have multiple dedicated
        channels.
        """

        if self.play_laser_sound:
            if self.laser_sound_index == 0:
                self.laser_channel_0.play(self.laser_sound)
                self.laser_sound_index +=1
                self.play_laser_sound = False
            elif self.laser_sound_index == 1:
                self.laser_channel_1.play(self.laser_sound)
                self.laser_sound_index +=1
                self.play_laser_sound = False
            elif self.laser_sound_index == 2:
                self.laser_channel_2.play(self.laser_sound)
                self.laser_sound_index +=1
                self.play_laser_sound = False
            if self.laser_sound_index > 2: self.laser_sound_index = 0

        if self.play_soundwave_sound:
            if self.soundwave_sound_index == 0:
                self.soundwave_channel_0.play(self.soundwave_sound)
                self.soundwave_sound_index +=1
                self.play_soundwave_sound = False
            elif self.soundwave_sound_index == 1:
                self.soundwave_channel_1.play(self.soundwave_sound)
                self.soundwave_sound_index +=1
                self.play_soundwave_sound = False
            if self.soundwave_sound_index > 1: self.soundwave_sound_index = 0

        if self.play_grenade_sound:
            if self.grenade_sound_index == 0:
                self.grenade_channel_0.play(self.grenade_sound)
                self.grenade_sound_index +=1
                self.play_grenade_sound = False
            elif self.grenade_sound_index == 1:
                self.grenade_channel_1.play(self.grenade_sound)
                self.grenade_sound_index +=1
                self.play_grenade_sound = False
            if self.grenade_sound_index > 1: self.grenade_sound_index = 0


        if self.lava_damage_start:
            self.lava_damage_channel.play(self.lava_damage_sound)
            self.lava_damage_start = False
        elif self.lava_damage_end:
            self.lava_damage_channel.fadeout(300)
            self.lava_damage_end = False

    def muting_music(self):
        """Handles the muting of the music tracks."""

        if self.intro_is_playing:
            pg.mixer.music.fadeout(150)
            self.intro_is_playing = False
        elif self.stage_1_music_is_playing:
            pg.mixer.music.fadeout(150)
            self.stage_1_music_is_playing = False
        elif self.middle_music_is_playing:
            pg.mixer.music.fadeout(150)
            self.middle_music_is_playing = False
        elif self.boss_music_is_playing:
            pg.mixer.music.fadeout(150)
            self.boss_music_is_playing = False

    def music(self):
        """Makes sure we hear the intended music at the intended times."""

        if game_state == 'credits' and self.credits_music_is_playing == False:
            pg.mixer.music.load('sound/music/Credits.mp3')
            pg.mixer.music.set_volume(0.45)
            pg.mixer.music.play()
            self.credits_music_is_playing = True

        if mute_button_state: return

        if game_state in self.silence_scope:
            pg.mixer.music.fadeout(150)
            self.intro_is_playing = False
            self.stage_1_music_is_playing = False
            self.middle_music_is_playing = False
            self.boss_music_is_playing = False

        if game_state in self.intro_scope and self.intro_is_playing == False:
            pg.mixer.music.load('sound/music/Intro.mp3')
            pg.mixer.music.set_volume(0.45)
            pg.mixer.music.play()
            self.intro_is_playing = True

        elif game_state == 'map_1' and self.stage_1_music_is_playing == False:
            pg.mixer.music.load('sound/music/Stage1.mp3')
            pg.mixer.music.set_volume(0.4)
            pg.mixer.music.play()
            self.stage_1_music_is_playing = True

        elif game_state == 'map_9' and self.boss_music_is_playing == False:
            pg.mixer.music.load('sound/music/Boss.mp3')
            pg.mixer.music.set_volume(0.25)
            pg.mixer.music.play(-1)
            self.boss_music_is_playing = True

        elif ((game_state in self.middle_music_scope)
                and (self.middle_music_is_playing == False)):
            if game_state == 'summary screen' and index_of_current_map == 1:
                return
            pg.mixer.music.load('sound/music/Middle.mp3')
            pg.mixer.music.set_volume(0.25)
            pg.mixer.music.play(-1) 
            self.middle_music_is_playing = True

    def after_stage_reset(self):
        """Used after a stage is completed."""

        self.play_laser_sound = False
        self.laser_sound_index = 0
        self.play_soundwave_sound = False
        self.soundwave_sound_index = 0
        self.play_grenade_sound = False
        self.grenade_sound_index = 0
        self.lava_damage_start = False
        self.lava_damage_end = False
        self.intro_is_playing = False

        if self.stage_1_music_is_playing or self.boss_music_is_playing:
            self.stage_1_music_is_playing = False
            self.boss_music_is_playing = False

    def whole_reset(self):
        """Used upon restarting the game."""

        self.play_laser_sound = False
        self.laser_sound_index = 0
        self.play_soundwave_sound = False
        self.soundwave_sound_index = 0
        self.play_grenade_sound = False
        self.grenade_sound_index = 0
        self.lava_damage_start = False
        self.lava_damage_end = False
        
        self.intro_is_playing = False
        self.stage_1_music_is_playing = False
        self.middle_music_is_playing = False
        self.boss_music_is_playing = False
        self.credits_music_is_playing = False

    def update(self):
        """Updates the music player."""

        self.dedicated_sound_channels()
        self.music()

#-----------------------------MAIN GAME LOOP-------------------------------


pg.init()
pg.mixer.pre_init(44100,-16,2,216)
pg.mixer.init()
pg.mixer.set_num_channels(20)
    
screen = pg.display.set_mode((game_window_width, game_window_height))
pg.display.set_caption('Siege')
clock = pg.time.Clock()
global_time_ms = pg.time.get_ticks()

map_loader_instance = MapLoader()
sound_manager = SoundManager()
 
while True:

    # testing if there is sound, if there isn't we print a message to the top left
    if not pg.mixer.get_init():
        game_font = pg.font.Font(None, 30*int(resizing_factor/2))
        mixer_error_message = game_font.render(
            'Pygame.mixer has failed to be initialized. No sound.',False,'Red')
        screen.blit(mixer_error_message,(0,0))

    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.mixer.quit()
            pg.quit()
            exit()
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            left_mouse_button_pressed = True
        if game_state in which_text_screen:
            if event.type == pg.KEYDOWN and event.key == pg.K_c:
                text_displayer.textscreen_c_pressed = True
        if game_state == 'summary screen':
            if event.type == pg.KEYDOWN and event.key == pg.K_c:
                sound_manager.button_click_sound.play()
                is_c_pressed = True
        if game_state in which_map_is_next and map_loader_instance.map_loaded:
            if event.type == pg.KEYDOWN and event.key == pg.K_m:
                sound_manager.button_click_sound.play()
                mute_button_state = not mute_button_state
                sound_manager.muting_music()
    
    extra_life()
    state_manager()
    pg.display.update()
    sound_manager.update()
    left_mouse_button_pressed = False
    global_time_ms = pg.time.get_ticks()
    clock.tick(60)