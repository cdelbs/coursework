# Referee Component Design for Fish Tournament System

## Overview

The **Referee** component is responsible for managing an individual game of Fish. It coordinates the players, ensures the game follows the rules, and determines when the game ends. The referee also interacts with the **Tournament Manager**, reporting game outcomes and providing statistics. This document outlines the key features of the **Referee** component, including its API, interactions, and responsibilities.

## Responsibilities

- **Game Setup**: Initialize the game, set up the board, and assign players.
- **Game Rounds**: Manage the progression of the game by enforcing game rules and facilitating player turns.
- **Game Outcome**: Determine the winner(s), handle player failures or disqualifications, and report the game results.
- **Interaction with Players**: Communicate with players to receive moves and provide feedback.
- **Game Observers**: Notify observers about key game events, such as player actions, state transitions, and the end of the game.

## Components

The **Referee** interacts with several key components in the system:

1. **GameState**: Represents the state of the game (e.g., players, tiles, board configuration).
2. **Player Interface**: The interface through which the **Referee** communicates with the players, receiving moves and sending game updates.
3. **Game Logic**: Implements the core rules of the game and ensures that player moves are legal.
4. **Tournament Manager**: Coordinates multiple games and tracks the progress of the tournament.

### Key Features of the Referee

- **Game Setup**:
  - Initialize the board with a given configuration of tiles and players.
  - Assign players to seats, ensuring they follow the rules (e.g., each player has a penguin).
  - Handle game phases (e.g., Placement, Move).

- **Game Round Management**:
  - Handle player turns in a round-robin fashion.
  - Ensure that players' actions adhere to the rules (e.g., no illegal moves).
  - Track players' actions, including penguin placements and movements.

- **Player Failure**:
  - Detect players who fail to comply with game rules or cheat.
  - Remove failing players from the game, removing their penguins and reporting the failure.

- **Game Outcome**:
  - Determine the winner(s) based on the game's rules (e.g., most fish collected).
  - Report the outcome to the **Tournament Manager**.

- **Notifications**:
  - Provide real-time updates to **Game Observers** (e.g., UI components or broadcast systems).
  - Notify players when the game ends and provide feedback on their performance.

## API Design

The **Referee** component will expose the following methods for interaction with the **Tournament Manager** and other system components:

### `Referee.start_game(players: List[Player], board: GameBoard) -> None`

- **Description**: Starts a new game with the specified players and board.
- **Parameters**:
  - `players`: A list of players participating in the game.
  - `board`: The game board to be used for this game.
- **Returns**: None.

### `Referee.run_turn(player: Player) -> bool`

- **Description**: Runs a single turn for the given player. The referee checks if the player's move is valid and applies it to the game state.
- **Parameters**:
  - `player`: The player whose turn is to be processed.
- **Returns**: `True` if the turn was valid and processed, `False` otherwise.

### `Referee.check_for_winner() -> Optional[Player]`

- **Description**: Checks the game state to determine if a winner has been reached.
- **Returns**: The player who won the game, or `None` if no winner has been determined yet.

### `Referee.end_game() -> None`

- **Description**: Ends the current game, determining the winner and reporting the result.
- **Returns**: None.

### `Referee.report_failure(player: Player) -> None`

- **Description**: Reports a player failure (e.g., a disqualified or cheating player).
- **Parameters**:
  - `player`: The player who failed.
- **Returns**: None.

### `Referee.notify_observers(message: str) -> None`

- **Description**: Sends a message to all observers (e.g., UI or tournament watchers).
- **Parameters**:
  - `message`: The message to be broadcasted.
- **Returns**: None.

## Interaction with Tournament Manager

The **Referee** communicates with the **Tournament Manager** to report game outcomes and receive tournament-level instructions. The **Tournament Manager** is responsible for managing multiple games, organizing rounds, and reporting tournament statistics.

- **Start a New Game**: The **Tournament Manager** calls `Referee.start_game()` with a list of players and a board configuration.
- **Run Turns**: The **Tournament Manager** invokes `Referee.run_turn()` in a round-robin fashion until the game ends.
- **Check for Winner**: The **Tournament Manager** uses `Referee.check_for_winner()` to determine if a winner has been found after each turn.
- **End the Game**: When the game concludes, `Referee.end_game()` is called to report the result.
- **Handle Player Failures**: The **Tournament Manager** can call `Referee.report_failure()` if a player is disqualified.

## Game Flow

1. **Setup**: The **Tournament Manager** assigns players to the game and sets up the board.
2. **Game Rounds**:
   - Players take turns, and the **Referee** ensures each move is legal.
   - The **Referee** reports each player's action and checks for violations.
3. **Game Outcome**: Once the game concludes, the **Referee** reports the winner to the **Tournament Manager**.

## Conclusion

The **Referee** component is crucial for managing individual games within the Fish Tournament System. It ensures that games are played according to the rules, handles player interactions, and communicates game results to the **Tournament Manager**. With this design, the **Referee** is a flexible, extensible component that can be easily integrated into a larger tournament management system.
