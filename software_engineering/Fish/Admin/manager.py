import sys
import importlib
from pathlib import Path
from typing import List, Tuple, Set

from websockets.asyncio.server import ServerConnection

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Fish.Common.gameboard import GameBoard
from Fish.Common.state import GameState, Player as EnginePlayer, replace
from Fish.Common.game_tree import GameTree, GameTreeNode
from Fish.Player.player import LocalPlayer

player_interface_module = importlib.import_module('Fish.Common.player-interface')
PlayerInterface = player_interface_module.PlayerInterface

from Fish.Admin.referee import Referee
from PyQt5.QtWidgets import QApplication

from Fish.Admin.abstract_observer import Observer
from Fish.Remote.remote_observer import RemoteBoardWidget

""" Once all players for a tournament are "signed up", they are handed to the tournament manager.

The purpose of the manager is to run a single game tournament until a winner or several winners emerge.
Its first task is to inform the players that the tournament has begun.

The tournament uses a knock-out elimination system. 
The top finisher(s) of every game of round n move on to round n+1. 
The tournament ends when two tournament rounds of games in a row produce the exact same winners, 
when there are too few players for a single game, or when the number of participants has become 
small enough to run a single final game (and yes this game is run). In both cases, the surviving 
players share the billion bitcoin FishHacker Award.

The allocation of players to games works as follows. 
The manager starts by assigning them to games with the 
maximal number of participants permitted in ascending order of age. 
Once the number of remaining players drops below the maximal number and can’t form a game,
the manager backtracks by one game and tries games of size one less than the maximal number 
and so on until all players are assigned.

When the tournament is over, the manager informs all remaining 
active players whether they won or lost. Winners that fail to accept this message become losers.
"""

# TournamentManager in charge of delegating matches to referees and tracking players/results
class TournamentManager:
    def __init__(self, players: List[PlayerInterface], 
                 remote: List[ServerConnection] = None, demo=False) -> None:
        self.players = players # active players that are not assigned a match yet
        self.players.reverse()
        self.referees: List[Tuple[int, Referee]] = [] # referees/matches of the current round
        self.bracket: List[List[List[List[str, bool]]]] = []
        self.tournament_observers: List[Observer] = []
        self.remote: List[ServerConnection] = remote
        self.demo = demo
        # players eliminated for non-normal reasons (illegal move, timeout, disconnect, etc.)
        self.failures: Set[str] = set()


    ########## observer methods #############
    def add_observer(self, tournament_observer: Observer):
        self.tournament_observers.append(tournament_observer)
    
    def remove_observer(self, tournament_observer: Observer):
        self.tournament_observers.remove(tournament_observer)

    def notify_observers(self):
        for obs in self.tournament_observers:
            obs.set_state(self.bracket)
            obs.update()
        QApplication.processEvents()

    def update_bracket_winners(self, round: int):
        winner_names = [p.name for p in self.players]
        for match in self.bracket[round]:
            for player in match:
                if player[0] in winner_names:
                    player[1] = True
        self.notify_observers()

    def update_bracket_matches(self, round: int):
        self.bracket.append([])
        for _ , ref in self.referees:
            players = []
            for p in ref.players:
                players.append([p.name, False])
            self.bracket[round].append(players)
        self.notify_observers()
    
            
    
    # Allocate players to games based on age and available spots
    def _allocate_matches(self, round: int) -> None:
        board = GameBoard(rows=7, columns=8)
        if self.demo:
            board = GameBoard(rows=5, columns=5, 
                              board_data=[[2,2,2,2,2],
                                          [2,2,2,2,2],
                                          [2,2,2,2,2],
                                          [2,2,2,2,2],
                                          [2,2,2,2,2]])
        
        
        if len(self.players) < 2:
            return # not enough players for a match
        
        # one match of 3 and one match of 2 if remainder 1
        # if not, while loop will allocate without problems
        if len(self.players) % 4 == 1:
            self.referees.append((round, Referee(board, self.players[0:3])))
            self.players = self.players[3:]
            
        # while loop for grouping players into matches of 4
        while len(self.players) >= 4:
            self.referees.append((round, Referee(board, self.players[0:4])))
            self.players = self.players[4:]
        
        # remaining players are allocated to a match if possible
        if len(self.players) > 0 and len(self.players) < 4:
            self.referees.append((round, Referee(board, self.players)))
            self.players = []
        
    # Run matches and return the winners
    def run_matches(self) -> None:
        print(f"number of matches: {len(self.referees)}")
        if self.remote:
            for _, referee in self.referees:
                referee.add_observer(RemoteBoardWidget(self.remote))
        counter = 1
        for round, referee in self.referees:  # could utilize threading later
            counter += 1
            res = referee.run()

            # Record any players eliminated for non-normal reasons
            # Referee.run() returns "eliminated": [{"pid": str, "reason": str}, ...]
            for elim in res.get("eliminated", []):
                pid = elim.get("pid")
                if isinstance(pid, str):
                    self.failures.add(pid)

            winners_ids = res['winners']
            print(f"winners ids: {winners_ids}")
            winners = [p for p in referee.players if p.name in winners_ids]
            print(f"winners: {winners}")
            self.players.extend(winners)
            self.update_bracket_winners(round)

            
    def prompt_winners(self) -> None:
        acknowledged_players = []
        for player in self.players:
            acknowledged = player.notify_tournament_result(won=True)
            if acknowledged:
                acknowledged_players.append(player)
            else:
                print(f"Player {player.name} did not acknowledge winning the match.")

        self.players = acknowledged_players
                
    def tournament_over(self, previous_winners: List[PlayerInterface]) -> bool:
        if len(previous_winners) == len(self.players):
            # check if the same players won twice in a row
            same_winners = all(p1.name == p2.name for p1, p2 in zip(previous_winners, self.players))
            if same_winners:
                return True
        elif len(self.players) < 2: # not enough players for a match
            return True             # either one winner or no winners
        elif len(self.players) <= 4: # small enough for a final match
            self.referees = []
            self._allocate_matches(len(self.bracket)) # assign players to matches
            print(f"Allocated {len(self.referees)} matches.")
            self.update_bracket_matches(len(self.bracket))

            self.run_matches()      # run all matches
            self.prompt_winners()
            # Only add to bracket if there are winners who acknowledged
            if len(self.players) > 0:
                self.bracket.append([[[self.players[0].name, True]]])
                self.notify_observers()
                winners_ids = [p.name for p in self.players]
                print(f"winners ids: {winners_ids}")
            else:
                print("No winners acknowledged - tournament ends with no winners")
            '''
            ref = Referee(GameBoard(rows=5, columns=5), self.players)
            self.referees = []
            self.referees.append((len(self.bracket), ref))
            self.update_bracket_matches(len(self.bracket))
            self.players = []
            #winners_ids = ref.run()['winners'] # run final match
            self.run_matches()
            winners_ids = [p.name for p in self.players]
            self.update_bracket_winners(len(self.bracket) - 1)
            print(f"winners ids: {winners_ids}")
            winners = [p for p in ref.players if p.name in winners_ids]
            self.players = winners
            '''
            return True
        else: # tournament continues
            print("Tournament continues to next round.")
            return False

    def run_tournament(self) -> List[LocalPlayer]:
        # Notify all players that the tournament is starting
        game_over = False
        previous_winners: List[LocalPlayer] = []
        counter = 0
        while not game_over: # tournament rounds loop
            print(f"Round {counter}")
            
            self._allocate_matches(counter) # assign players to matches
            print(f"Allocated {len(self.referees)} matches.")
            self.update_bracket_matches(counter)

            self.run_matches()      # run all matches

            self.prompt_winners()   # notify winners of their status
            game_over = self.tournament_over(previous_winners) # check if tournament is over
            previous_winners = self.players[:] # copy current winners
            self.referees = [] # reset referees for next round
            counter += 1
            
        if len(self.players) == 0:
            print("Tournament over with no winners.")
            return []
        else:
            print("Tournament over with winners:", [p.name for p in self.players])
            return self.players
        
def main():
    test_players = [LocalPlayer(name='hello'), LocalPlayer(name='world'), 
                    LocalPlayer(name='collin'), LocalPlayer(name='joseph'), 
                    LocalPlayer(name='marco'), LocalPlayer(name='jason')]
    manager = TournamentManager(test_players)
    winners = manager.run_tournament()
    print("Final winners:", [p.name for p in winners])
    
if __name__ == "__main__":
    main()