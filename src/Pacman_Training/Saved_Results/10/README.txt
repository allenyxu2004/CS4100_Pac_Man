# This is the first run where I don't optimize the model or save to the replaymemory when frame skipping or waiting for pacman to spawn

BATCH_SIZE = 64
GAMMA = 0.99
EPS_START = 1
EPS_END = 0.01
EPS_DECAY = 40000    
TAU = 0.005
LR = 1e-5
REPLAY_MEMORY_CAPACITY = 10000

num_episodes = 1000
# This decides how many episodes until running save_execution() 
save_rate = 100