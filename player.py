## =================================================================================================
## Python 3.6+
## =================================================================================================
import json
import random

import constants

## =================================================================================================
## Possible player colors
COLORS = ['#C62828', '#AD1457', '#6A1B9A', '#4527A0', '#283593', '#1565C0', '#0277BD',
          '#00838F', '#00695C', '#2E7D32', '#558B2F', '#9E9D24', '#F9A825', '#FF8F00',
          '#EF6C00', '#D84315', '#4E342E', '#616161', '#546E7A', '#000000']

## =================================================================================================
def get_color(n):
    '''
    Picks a color from the pre-defined color array. This function will always return the same
    color for a particular n.

    :param n: int
    :return: color code
    '''
    random.seed(n)
    return COLORS[random.randint(0, len(COLORS) - 1)]


## -------------------------------------------------------------------------------------------------
def player_from_json(json_str):
    '''
    Create player object from JSON string

    :param json_str: string
    :return: Player
    '''
    return player_from_dict(json.loads(json_str))


## -------------------------------------------------------------------------------------------------
def player_from_dict(player_dict):
    '''
    Create player object from dictionary

    :param player_dict: dict
    :return: Player
    '''
    return Player(id=player_dict['id'], x=player_dict['x'], y=player_dict['y'],
        in_game=player_dict['in_game'])


## -------------------------------------------------------------------------------------------------
class Player:
    def __init__(self, id=0, x=None, y=None, in_game=False):
        '''
        Hold player information

        :param id: player number
        :param x: x position
        :param y: y position
        '''
        if x is None:
            self.x = random.randint(constants.DOT_SIZE,
                constants.CANVAS_SIZE_X - constants.DOT_SIZE)
        else:
            self.x = x
        if y is None:
            self.y = random.randint(constants.DOT_SIZE,
                constants.CANVAS_SIZE_Y - constants.DOT_SIZE)
        else:
            self.y = y

        self.id = id
        self.color = get_color(id)
        self.in_game = in_game


    def __repr__(self):
        return (f'Player: ID={self.id}, x={self.x}, y={self.y}, color={self.color}, in_game='
                f'{self.in_game}')


    def as_dict(self):
        '''
        Return class in dictionary format. Color is not included because it is determined by
        player ID (reduces total data sent via TCP).

        :return: dict
        '''
        return {
            'x': self.x,
            'y': self.y,
            'id': self.id,
            'in_game': self.in_game,
        }


    def as_json(self):
        '''
        Dump the dictionary into json string

        :return: string
        '''
        return json.dumps(self.as_dict())