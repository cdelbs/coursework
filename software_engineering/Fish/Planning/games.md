**To**: Our Angel Investors
**From**: CEO’s of start-up, Christopher Bernal, and Joseph Lodge
**Date**: 10/6/2025
**Subject**: Game Representation for Fish Game

Introduction and Purpose:
In this memo, we will discuss our representation of games in Fish Game. A game is a tree of potential moves from a given starting point, which we will assume to be the state of the game in which the first player is allowed to make the first non-placement move of the game. The purpose of game representation is to enable player AIs to plan ahead and for our croupier to determine the validity of actions.

Games Representation:
class Move:
    def \_\_init\_\_(self, player\_id, penguin\_id, start, end, fish\_gained):
        self.player\_id \= player\_id
        self.penguin\_id \= penguin\_id
        self.start \= start
        self.end \= end
        self.fish\_gained \= fish\_gained

class GameTree:
    def \_\_init\_\_(self, state: GameState, parent=None, move=None):
        self.state \= state
        self.parent \= parent
        self.move \= move
        self.children \= \[\]

    def expand(self):
        if self.state.phase \== "GameOver":
            return
        current\_player\_id \= self.state.turn\_order\[self.state.current\_turn\]
        moves \= self.state.board.get\_all\_legal\_moves(current\_player\_id)
        state\_copy \= deepcopy(self.state
        for move in moves:
            new\_state \= deepcopy(state\_copy)
            new\_state.move\_avatar(move.player\_id, move.penguin\_id, move.new\_row, move.new\_col)
            self.children.append(GameTree(new\_state, parent=self, move=move))

External Interface:

def get\_legal\_moves(self, state: GameState) \-\> list\[Move\]:
    Return all legal moves for the player whose turn it is.

def is\_move\_legal(self, state: GameState, move: Move) \-\> bool:
    Determine whether a given move is a legal move.

def apply\_move(self, state: GameState, move: Move) \-\> GameState:
    Return the new GameState after applying a legal move.

def expand\_child(self, child: GameState) \-\> GameTree:
    Return the new GameTree of a given child.

def is\_game\_over(self, child: GameState) \-\> bool:
    Determine if the given GameState is in GameOver.

def get\_winner(self, state: GameState) \-\> list\[int\]:
    Return the list of player\_ids of the winning player, if the state is in GameOver.

Closing:

	By utilizing GameTrees, both our AI players and the croupier will be able to plan moves based on the current GameState and validate moves by making sure they adhere to the rules of the game.
