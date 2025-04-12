# Physics-Based Tetris Game

GENERATED WITH CLAUDE AI

This project is a physics-enhanced version of the classic Tetris game, implemented using Python with `pygame` and `pymunk` libraries. It introduces unique gameplay mechanics by incorporating physics-based interactions and shaking controls.

## Features

- **Physics-Enhanced Gameplay**: 
  - Blocks become physical entities with realistic properties such as mass, friction, and elasticity.
  - Blocks can topple over or lose balance if placed on edges.
  - Stacking results in dynamic physics interactions.

- **Window Shaking Mechanics**:
  - Rapid mouse movements apply force to blocks, simulating an earthquake effect.

- **Classic Tetris Features**:
  - Standard tetromino shapes (I, J, L, O, S, T, Z).
  - Score tracking, levels, and line-clearing mechanics.
  - Preview of the next tetromino piece.

## Requirements

To run this project, you need:

- Python 3.x
- `pygame` library (Install using `pip install pygame`)
- `pymunk` library (Install using `pip install pymunk`)

## Controls

- **Arrow Keys**: Move pieces.
- **Up Arrow**: Rotate piece.
- **Space**: Hard drop.
- **Mouse Movement**: Shake blocks on the playing field.
- **R**: Restart the game.
- **D**: Toggle debug grid (to visualize occupied cells).

## Getting Started

1. Clone the repository.
2. Install the required libraries using pip:
   ```bash
   pip install pygame pymunk
