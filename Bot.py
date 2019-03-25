#!/usr/bin/env python3
# Python 3.6

# Import the Halite SDK, which will let you interact with the game.
import hlt

# This library contains constant values.
from hlt import constants

# This library contains direction metadata to better interface with the game.
from hlt.positionals import Direction
from hlt.positionals import Position

# This library allows you to generate random numbers.
import random

import operator
# Logging allows you to save messages for yourself. This is required because the regular STDOUT
#   (print statements) are reserved for the engine-bot communication.
import logging

""" <<<Game Begin>>> """

# This game object contains the initial game state.
game = hlt.Game()
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.
# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("Korczak v3")

# Now that your bot is initialized, save a message to yourself in the log file with some important information.
#   Here, you log here your id, which you can always fetch from the game object by using my_id.
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

""" <<<Game Loop>>> """


direction_order = [Direction.North, Direction.South, Direction.East, Direction.West, Direction.Still]
game_map = game.game_map
map_width = game_map.width
map_height = game_map.height

players = game.players


def get_search_radius(pos, radius):
    """ returns a list of all positions within square radius of a position """
    return [pos+Position(i, j) for i in range(-radius, radius+1) for j in range(-radius, radius+1)]

def get_search_radius_2(pos, radius):
    """ returns a list of all positions within square radius of a position """
    return [pos+Position(i, j) for i in range(0, radius+1) for j in range(0, radius+1)]

def collectHalite(ship, me, game_map):
    closest_dropoff = [0,0]
    closest_dropoff_dist = 9999
    for dropoff in me.get_dropoffs():
        distance = game_map.calculate_distance(ship.position, dropoff.position)
        if closest_dropoff_dist > distance:
            closest_dropoff = dropoff.position
            closest_dropoff_dist = distance


    distance = game_map.calculate_distance(ship.position, me.shipyard.position)
    if closest_dropoff_dist > distance:
        closest_dropoff = me.shipyard.position
        closest_dropoff_dist = distance

    return game_map.get_unsafe_moves(ship.position, closest_dropoff)


def calcDistanceBetweenShipAndDropoff(ship, me, game_map):
    closest_dropoff_dist = 9999
    for dropoff in me.get_dropoffs():
        distance = game_map.calculate_distance(ship.position, dropoff.position)
        if closest_dropoff_dist > distance:
            closest_dropoff_dist = distance


    distance = game_map.calculate_distance(ship.position, me.shipyard.position)
    if closest_dropoff_dist > distance:
        closest_dropoff_dist = distance

    return closest_dropoff_dist

def getPositionDict(ship):
    position_dict = {}
    position_options = ship.position.get_surrounding_cardinals() + [ship.position]


    for n, direction in enumerate(direction_order):
        pos = {}
        pos = getPositionOfCell(position_options[n])

        position_dict[direction] = pos

    return position_dict

def getPositionOfCell(cell_position):
    pos = [0, 0]
    pos[0] = cell_position.x
    pos[1] = cell_position.y

    if pos[0] >= map_width:
        pos[0] = pos[0] - map_width
    elif pos[0] <= -1:
        pos[0] = map_width + pos[0]

    if pos[1] >= map_height:
        pos[1] = pos[1] - map_height
    elif pos[1] <= -1:
        pos[1] = map_height + pos[1]

    return Direction.convertToPosition(pos)

def getHaliteDict(ship, game_map, position_choices, ship_stay_still_id):
    position_dict = getPositionDict(ship)
    halite_dict = {}


    for direction in position_dict:
        position = position_dict[direction]
        halite_amount = 0
        if direction == (0, 0) and (position_dict[direction] not in position_choices or ship.id in ship_stay_still_id):
            halite_amount += game_map[position].halite_amount * 35
            halite_dict[direction] = halite_amount
        elif position_dict[direction] not in position_choices and not game_map[position_dict[direction]].is_occupied:
            pos1, pos2, pos3 = [], [], []

            pos1.append(position)
            pos2.append(pos1[0] + Direction.convertToPosition(direction))
            pos3.append(pos2[0] + Direction.convertToPosition(direction))
            if direction == Direction.North or direction == Direction.South:
                pos2.append(pos1[0] + Direction.convertToPosition(Direction.West))
                pos2.append(pos1[0] + Direction.convertToPosition(Direction.East))
                pos3.append(pos2[0] + Direction.convertToPosition(Direction.West))
                pos3.append(pos2[0] + Direction.convertToPosition(Direction.East))
                pos3.append(pos2[1] + Direction.convertToPosition(Direction.West))
                pos3.append(pos2[2] + Direction.convertToPosition(Direction.East))
            elif direction == Direction.West or direction == Direction.East:
                pos2.append(pos1[0] + Direction.convertToPosition(Direction.North))
                pos2.append(pos1[0] + Direction.convertToPosition(Direction.South))
                pos3.append(pos2[0] + Direction.convertToPosition(Direction.North))
                pos3.append(pos2[0] + Direction.convertToPosition(Direction.South))
                pos3.append(pos2[1] + Direction.convertToPosition(Direction.North))
                pos3.append(pos2[2] + Direction.convertToPosition(Direction.South))

            pos1[0] = getPositionOfCell(pos1[0])
            for i in range(0, len(pos2)):
                pos2[i] = getPositionOfCell(pos2[i])
            for i in range(0, len(pos3)):
                pos3[i] = getPositionOfCell(pos3[i])


            halite_amount += game_map[pos1[0]].halite_amount * 8
            for pos in pos2:
                halite_amount += game_map[pos].halite_amount * 2
            for pos in pos3:
                halite_amount += game_map[pos].halite_amount * 1


            halite_dict[direction] = halite_amount

    if len(halite_dict) > 0:
        max_halite_direction = max(halite_dict, key=halite_dict.get)
        if ship.halite_amount <= game_map[position_dict[max_halite_direction]].halite_amount * 0.1:
            position_choices.append(ship.position)


    return halite_dict

status = {
    'Collecting':'collecting',
    'Dropoff': 'dropoff',
    'Ending': 'ending'
    }

ship_status = {}


max_turns = constants.MAX_TURNS
position_whitelist = []


cells_to_search = get_search_radius(game.me.shipyard.position, 30)
halite_to_collect_array = [game_map[cell].halite_amount for cell in cells_to_search]
halite_to_collect_on_radius_from_beggining = sum(halite_to_collect_array)

cells_to_search = get_search_radius_2(Direction.convertToPosition((0,0)), map_width)
halite_to_collect_array = [game_map[cell].halite_amount for cell in cells_to_search]
halite_to_collect_all_from_beggining = sum(halite_to_collect_array)

while True:
    game.update_frame()

    num_of_all_ships = 0
    average_num_of_ships_per_player = 0

    me = game.me
    my_id = game.my_id
    game_map = game.game_map


    ship_commands = {}
    structures_commands = []
    command_queue = []


    position_choices = []

    ship_next_move = {}
    ship_actual_position = {}
    ship_stay_still_id = []

    #Aktualna pozycja statkow
    ships_to_command = me.get_ships()
    for ship in ships_to_command:
        ship_actual_position[ship.id] = ship.position

    #Mozliwosc niszczenia statkow w droppoffach w ostatnich turach
    if game.turn_number == max_turns - 30:
        for dropoff in me.get_dropoffs():
            position_whitelist.append(dropoff.position)
        position_whitelist.append(me.shipyard.position)
    
    #Zakonczenie rozgrywki, powrot statkow do bazy
    if game.turn_number > max_turns - 100:
        for ship in me.get_ships():
            if ship_status[ship.id] != status['Ending']:
                dist_to_dropoff = calcDistanceBetweenShipAndDropoff(ship, me, game_map)

                turn_number_to_end = max_turns - game.turn_number
                if dist_to_dropoff >= turn_number_to_end - 20:
                    logging.info('Ship {} moving to end,  dist: {}, turns: {}'.format(ship.id, dist_to_dropoff, turn_number_to_end))

                    ship_status[ship.id] = status['Ending']

    #Sprawdzenie ktore statki zostana w miejscu
    for ship in me.get_ships():

        #Aktualizacja statusow statkow
        if ship.id not in ship_status:
            ship_status[ship.id] = status['Collecting']
        elif ship_status[ship.id] == status['Dropoff'] and ship.halite_amount < constants.MAX_HALITE * 0.15:
            ship_status[ship.id] = status['Collecting']

        if ship.position in position_whitelist:
            ship_status[ship.id] = status['Dropoff']

        
        halite_dict = getHaliteDict(ship, game_map, position_choices, ship_stay_still_id)
        logging.info('Ship {}, halite_dict: {}'.format(ship.id, halite_dict))
        if len(halite_dict) > 0:
            max_halite_direction = max(halite_dict, key=halite_dict.get)
        if max_halite_direction == (0, 0):
            position_choices.append(ship.position)
            ship_stay_still_id.append(ship.id)

    for player_id in range(len(players)):
        if player_id != my_id:
            for ship in players[player_id].get_ships():
                position_choices.append(ship.position)
        num_of_all_ships += len(players[player_id].get_ships())

    average_num_of_ships_per_player = num_of_all_ships / len(players)

    logging.warn(position_choices)

    for ship in me.get_ships():
        position_dict = getPositionDict(ship)


        #Minimalna ilosc surowca aby powrocic do bazy
        distance_to_shipyard = game_map.calculate_distance(ship.position, me.shipyard.position)
        minimum_halite_to_collect = 0.6
        if distance_to_shipyard < 5:
            minimum_halite_to_collect = 0.7
        elif distance_to_shipyard < 10:
            minimum_halite_to_collect = 0.85
        else:
            minimum_halite_to_collect = 0.92
                
        halite_dict = getHaliteDict(ship, game_map, position_choices, ship_stay_still_id)

        if (ship.halite_amount >= constants.MAX_HALITE * minimum_halite_to_collect and game_map[ship.position].halite_amount < 450) \
            or ship.halite_amount >= constants.MAX_HALITE * 0.9:
            ship_status[ship.id] = status['Dropoff']

        if ship_status[ship.id] == status['Dropoff'] or ship_status[ship.id] == status['Ending']:
            possible_directions = collectHalite(ship, me, game_map)
            directional_choice = (0, 0)
            for direction in possible_directions:
                position = position_dict[direction]
                if (position not in position_choices and not game_map[position].is_occupied) or position in position_whitelist:
                    directional_choice = direction 
                    break

            position_choices.append(position_dict[directional_choice])

            #ship_commands[ship.id] = ship.move(directional_choice)
            command_queue.append(ship.move(directional_choice))
        else:
            directional_choice = (0, 0)
            if len(halite_dict) > 0: 
                directional_choice = max(halite_dict, key=halite_dict.get)
            position_choices.append(position_dict[directional_choice])
            

            #ship_commands[ship.id] = ship.move(directional_choice)
            command_queue.append(ship.move(directional_choice))



        ship_next_move[ship.id] = position_dict[directional_choice]

    #features: [turn_number, rest_halite, halite_in_radius, num_of_ships, average_num_of_ships_per_enemies]
    cells_to_search = get_search_radius(me.shipyard.position, 30)
    halite_to_collect_array = [game_map[cell].halite_amount for cell in cells_to_search]
    halite_to_collect = sum(halite_to_collect_array)

    cells_to_search = get_search_radius_2(Direction.convertToPosition((0,0)), map_width)
    halite_to_collect_array = [game_map[cell].halite_amount for cell in cells_to_search]
    halite_to_collect_all = sum(halite_to_collect_array)


    logging.info('Halite to collect: {}'.format(halite_to_collect))

    features = [game.turn_number, halite_to_collect_all/float(halite_to_collect_all_from_beggining), halite_to_collect/float(halite_to_collect_on_radius_from_beggining), len(me.get_ships()), average_num_of_ships_per_player]
    if len(players) <= 2:
        if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied and game_map[me.shipyard].position not in position_choices:
            #structures_commands.append(me.shipyard.spawn())
            command_queue.append(me.shipyard.spawn())
    else:
        if game.turn_number <= 100 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied and game_map[me.shipyard].position not in position_choices:
            #structures_commands.append(me.shipyard.spawn())
            command_queue.append(me.shipyard.spawn())



    logging.info('Commands: {}'.format(command_queue))


    game.end_turn(command_queue)

