sequenceDiagram
    autonumber

    participant SS as SignUp
    participant TM as TManager
    participant CR as Croupier
    participant PX as PlayerProxy
    participant CL as ClientAgent
    participant PL as Player

    Note over SS,PL: Registration
    PL->>CL: launch(player-config)
    CL->>SS: signup(player-meta)
    SS-->>CL: signup-ack(player-id)
    SS->>TM: register(player-id, conn-handle)

    Note over SS,PL: Tournament start
    TM->>PX: tournament-start(info)
    PX->>CL: tournament-start(info)
    CL->>PL: tournament-start(info)

    Note over SS,PL: Game allocation
    TM->>CR: create-game([PX...])
    CR->>PX: start-game(game-id, view)
    PX->>CL: start-game(game-id, view)
    CL->>PL: start-game(game-id, view)

    loop Placement rounds
        CR->>PX: request-placement(view)
        PX->>CL: request-placement(view)
        CL->>PL: request-placement(view)
        PL-->>CL: placement(coord)
        CL-->>PX: placement(coord)
        PX-->>CR: placement(coord)
        CR->>CR: apply-placement
    end

    loop Turns
        CR->>PX: request-move(view)
        PX->>CL: request-move(view)
        CL->>PL: request-move(view)
        PL-->>CL: move(from,to)
        CL-->>PX: move(from,to)
        PX-->>CR: move(from,to)
        CR->>CR: apply-move
    end

    Note over SS,PL: Game + tournament end
    CR-->>TM: game-result(scores, cheaters)
    TM->>PX: game-over(result)
    PX->>CL: game-over(result)
    CL->>PL: game-over(result)

    TM->>PX: tournament-over(status)
    PX->>CL: tournament-over(status)
    CL->>PL: tournament-over(status)
    CL-->>SS: disconnect(player-id)

### 1. Registration

Goal: create a connection from a remote player to the server and give that player an id and an age. Age is just the order of signup.

1. The human starts their player program.  
   PL starts and gives some configuration to CL.  
   (This is `PL -> CL: launch(player-config)`.)

2. CL connects to SS and sends a signup message with player meta information.  
   For example name or strategy.  
   (This is `CL -> SS: signup(player-meta)`.)

3. SS replies with a signup acknowledgement that contains a player id.  
   (This is `SS -> CL: signup-ack(player-id)`.)

4. SS tells TM about this new player, together with a handle for that connection.  
   TM will later wrap this handle in a PlayerProxy.  
   (This is `SS -> TM: register(player-id, conn-handle)`.)

SS repeats this for each client. The first client to sign up is the oldest. The next one is younger, and so on. When registration closes, TM has a list of players in age order.

---

### 2. Tournament start

Goal: tell each player that a tournament has started.

1. TM calls a tournament start method on PX.  
   (This is `TM -> PX: tournament-start(info)`.)

2. PX forwards that message over the network to CL.  
   (This is `PX -> CL: tournament-start(info)`.)

3. CL calls the local PL with the same information.  
   (This is `CL -> PL: tournament-start(info)`.)

From TM’s point of view this is just a normal method call on a player. PX hides the fact that the real player is remote.

---

### 3. Game allocation and game start

Goal: create a game, connect a croupier to a set of players, and tell each player about the new game.

1. TM asks CR to create a game with a list of player objects.  
   Some of these are PlayerProxy objects.  
   (This is `TM -> CR: create-game([PX...])`.)

2. For each player in the game, CR calls a start method.  
   For a remote player this is `CR -> PX: start-game(game-id, view)`.

3. PX forwards this message to CL.  
   (This is `PX -> CL: start-game(game-id, view)`.)

4. CL passes it on to PL.  
   (This is `CL -> PL: start-game(game-id, view)`.)

The value `view` is what that player is allowed to see about the game, such as the public board.

---

### 4. Placement rounds

Goal: during the placement phase, CR gets a legal placement from each player in turn.

For each placement by a remote player:

1. CR asks PX for a placement.  
   (This is `CR -> PX: request-placement(view)`.)

2. PX sends the same request to CL.  
   (This is `PX -> CL: request-placement(view)`.)

3. CL calls PL.  
   (This is `CL -> PL: request-placement(view)`.)

4. PL chooses a coordinate and returns it to CL.  
   (This is `PL -> CL: placement(coord)`.)

5. CL sends this coordinate back to PX.  
   (This is `CL -> PX: placement(coord)`.)

6. PX returns the coordinate to CR.  
   (This is `PX -> CR: placement(coord)`.)

7. CR applies the placement in its internal game state.  
   (This is `CR -> CR: apply-placement`.)

CR repeats this until every player has placed all their penguins.

---

### 5. Turn taking

Goal: during the move phase, CR gets a legal move from the current player on each turn.

For each move by a remote player:

1. CR asks PX for a move.  
   (This is `CR -> PX: request-move(view)`.)

2. PX sends the request to CL.  
   (This is `PX -> CL: request-move(view)`.)

3. CL calls PL.  
   (This is `CL -> PL: request-move(view)`.)

4. PL chooses a move, from and to, and returns it to CL.  
   (This is `PL -> CL: move(from, to)`.)

5. CL sends the move back to PX.  
   (This is `CL -> PX: move(from, to)`.)

6. PX returns the move to CR.  
   (This is `PX -> CR: move(from, to)`.)

7. CR applies the move to its game state.  
   (This is `CR -> CR: apply-move`.)

CR repeats this loop until the game is over.

---

### 6. Game end and tournament end

Goal: send results up to the manager, then out to players, and clean up the connection.

1. When the game finishes, CR sends the scores and any cheating information to TM.  
   (This is `CR -> TM: game-result(scores, cheaters)`.)

2. TM may send each player a game over message for that game.  
   For a remote player this is  
   `TM -> PX: game-over(result)`  
   `PX -> CL: game-over(result)`  
   `CL -> PL: game-over(result)`.

3. When the entire tournament is done, TM sends each player a tournament summary.  
   For a remote player this is  
   `TM -> PX: tournament-over(status)`  
   `PX -> CL: tournament-over(status)`  
   `CL -> PL: tournament-over(status)`.

4. Finally the client agent closes the connection and tells the signup server that this player is gone.  
   (This is `CL -> SS: disconnect(player-id)`.)