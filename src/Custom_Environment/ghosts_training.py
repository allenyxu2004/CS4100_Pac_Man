from ghosts_ffn import GhostFNN
import torch
import torch.nn as nn
import torch.optim as optim
import sys
import os 
import numpy as np

sys.path.append(os.path.abspath("../Pacman_Training"))

from Pacman_reload_dqn import load_execution
from pacman_neural_network import DQN
from custom_pacman_env import PacmanEnv 


ghost_nn = GhostFNN()
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(ghost_nn.parameters(), lr=0.01)

device = torch.device(
    "cuda" if torch.cuda.is_available() else
    "mps" if torch.backends.mps.is_available() else
    "cpu"
)

# Create the Pacman environment
env = PacmanEnv()

epsilon = 0.99
epsilon_decay_rate = 0.999999
# Training loop
total_rewards = []
for i_episode in range(1000):
    observation, info = env.reset() 
    total_reward = 0
    step_count = 0
    while True:
        step_count += 1
        blinky_coordinates = env.blinky["coordinates"][0]
        if env.pinky["spawned"]:
            pinky_coordinates = env.pinky["coordinates"][0]
        else:
            pinky_coordinates = [80, 80]

        if env.inky["spawned"]:
            inky_coordinates = env.inky["coordinates"][0]
        else:
            inky_coordinates = [80, 80]

        if env.clyde["spawned"]:
            clyde_coordinates = env.clyde["coordinates"][0]
        else:
            clyde_coordinates = [80, 80]
        pacman_coordinates = env.pacman[0]
        inputs = np.array([
            blinky_coordinates[0] / 160.0, 
            blinky_coordinates[1] / 180.0, 
            pinky_coordinates[0] / 160.0, 
            pinky_coordinates[1] / 180.0, 
            inky_coordinates[0] / 160.0, 
            inky_coordinates[1] / 180.0, 
            clyde_coordinates[0] / 160.0, 
            clyde_coordinates[1] / 180.0, 
            pacman_coordinates[0] / 160.0, 
            pacman_coordinates[1] /180.0])
        inputs = torch.tensor(inputs, dtype=torch.float)


        # Got help from GenAI to figure out how to pass in the target action 
        blinky_distances = []
        blinky_actions = [
        (blinky_coordinates[0] - 1, blinky_coordinates[1]),  # Move up
        (blinky_coordinates[0] + 1, blinky_coordinates[1]),  # Move down
        (blinky_coordinates[0], blinky_coordinates[1] - 1),  # Move left
        (blinky_coordinates[0], blinky_coordinates[1] + 1),  # Move right
        ]
        
        pinky_distances = []
        pinky_actions = [
        (pinky_coordinates[0] - 1, pinky_coordinates[1]),  # Move up
        (pinky_coordinates[0] + 1, pinky_coordinates[1]),  # Move down
        (pinky_coordinates[0], pinky_coordinates[1] - 1),  # Move left
        (pinky_coordinates[0], pinky_coordinates[1] + 1),  # Move right
        ]

        inky_distances = []
        inky_actions = [
        (inky_coordinates[0] - 1, inky_coordinates[1]),  # Move up
        (inky_coordinates[0] + 1, inky_coordinates[1]),  # Move down
        (inky_coordinates[0], inky_coordinates[1] - 1),  # Move left
        (inky_coordinates[0], inky_coordinates[1] + 1),  # Move right
        ]

        clyde_distances = []
        clyde_actions = [
        (clyde_coordinates[0] - 1, clyde_coordinates[1]),  # Move up
        (clyde_coordinates[0] + 1, clyde_coordinates[1]),  # Move down
        (clyde_coordinates[0], clyde_coordinates[1] - 1),  # Move left
        (clyde_coordinates[0], clyde_coordinates[1] + 1),  # Move right
        ]
        

        for action in blinky_actions:
            dist = abs(action[0] - pacman_coordinates[0]) + abs(action[1] - pacman_coordinates[1])
            blinky_distances.append(dist)

        for action in pinky_actions:
            dist = abs(action[0] - pacman_coordinates[0]) + abs(action[1] - pacman_coordinates[1])
            pinky_distances.append(dist)

        for action in inky_actions:
            dist = abs(action[0] - pacman_coordinates[0]) + abs(action[1] - pacman_coordinates[1])
            inky_distances.append(dist)
        
        for action in clyde_actions:
            dist = abs(action[0] - pacman_coordinates[0]) + abs(action[1] - pacman_coordinates[1])
            clyde_distances.append(dist)


        # Forward pass
        outputs = ghost_nn(inputs)

        # Backward pass and optimization
        optimizer.zero_grad()
        
        blinky_target_action = blinky_distances.index(min(blinky_distances))
        pinky_target_action = pinky_distances.index(min(pinky_distances))
        inky_target_action = inky_distances.index(min(inky_distances))
        clyde_target_action = clyde_distances.index(min(clyde_distances))

        #Get the outputs for each ghost (assuming outputs is of shape [batch_size, num_actions])
        # Each ghost has 4 possible actions, so we split the outputs tensor into 4 chunks
        blinky_output = outputs[0:4]  # First 4 values correspond to Blinky's actions
        pinky_output = outputs[4:8]   # Next 4 values correspond to Pinky's actions
        inky_output = outputs[8:12]  # Next 4 values correspond to Inky's actions
        clyde_output = outputs[12:16] # Last 4 values correspond to Clyde's actions

        blinky_loss = criterion(blinky_output.unsqueeze(0), torch.tensor([blinky_target_action], dtype=torch.long))
        pinky_loss = criterion(pinky_output.unsqueeze(0), torch.tensor([pinky_target_action], dtype=torch.long))
        inky_loss = criterion(inky_output.unsqueeze(0), torch.tensor([inky_target_action], dtype=torch.long))
        clyde_loss = criterion(clyde_output.unsqueeze(0), torch.tensor([clyde_target_action], dtype=torch.long))


        loss = blinky_loss + pinky_loss + inky_loss + clyde_loss
        loss.backward()
        optimizer.step()


        # Get the probabilities for each ghost using softmax
        blinky_probs = torch.softmax(outputs[0:4], dim=0)  # Probabilities for Blinky's actions
        pinky_probs = torch.softmax(outputs[4:8], dim=0)   # Probabilities for Pinky's actions
        inky_probs = torch.softmax(outputs[8:12], dim=0)   # Probabilities for Inky's actions
        clyde_probs = torch.softmax(outputs[12:16], dim=0) # Probabilities for Clyde's actions

        # Get the predicted action (the index with the highest probability) for each ghost
        blinky_predicted_action = torch.argmax(blinky_probs).item()
        pinky_predicted_action = torch.argmax(pinky_probs).item()
        inky_predicted_action = torch.argmax(inky_probs).item()
        clyde_predicted_action = torch.argmax(clyde_probs).item()        

        if np.random.rand() < epsilon:
            # Randomly select an action for exploration
            predicted_action1 = np.random.choice([0, 1, 2, 3])
            predicted_action2 = np.random.choice([0, 1, 2, 3])
            predicted_action3 = np.random.choice([0, 1, 2, 3])
            predicted_action4 = np.random.choice([0, 1, 2, 3])

            predicted_actions = (predicted_action1, predicted_action2, predicted_action3, predicted_action4)
        else:
            # Otherwise, use the model's prediction
            predicted_actions = (blinky_predicted_action, pinky_predicted_action, inky_predicted_action, clyde_predicted_action)

        observation, reward, game_over = env.step(predicted_actions)
        total_reward += reward 
        epsilon = epsilon * epsilon_decay_rate
        if game_over:
            break


    print(f"Episode {i_episode},    Step count: {step_count},       Loss: {loss.item()},   Total Reward: {total_reward}     Epsilon: {epsilon}")
    total_rewards.append(total_reward)

print("Training complete!")

