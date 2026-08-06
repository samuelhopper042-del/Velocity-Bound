import pymunk
from players.player import Player
from data.game_data import GAME_CONFIG

p = Player(GAME_CONFIG['players']['p1']['start_x'], GAME_CONFIG['players']['p1']['start_y'], (0,100,255))
space = pymunk.Space()
p.create_body(space)
print('before', p.body.position, p.body.moment)
p.body.moment = float('inf')
print('after', p.body.position, p.body.moment)
for limb_name, limb_body in p.limb_bodies.items():
    print('limb', limb_name, limb_body.position, limb_body.moment)
print('head', p.head_body.position, p.head_body.moment)
