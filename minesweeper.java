import java.util.ArrayList;

import tester.*;
import javalib.impworld.*;

import java.awt.Color;
import java.util.Random;

import javalib.worldimages.*;



// represents one grid space on the game board
class Tile {

    // list of all Tiles adjacent to this Tile
    ArrayList<Tile> neighbors;

    // 0 = undiscovered; unflagged
    // 1 = discovered
    // 2 = undiscovered; flagged
    int status;

    //true means there is a mine at this grid square
    //false means there is not a mine under this grid square
    boolean mine;

    //constructor
    Tile() {
        this.neighbors = new ArrayList<>();
        this.status = 0;
        this.mine = false;
    }

    /*
    TEMPLATE:
        Fields:
            this.neighbors -> ArrayList<Tile>
            this.status -> int
            this.mine -> boolean
        Methods:
            flagIt() -> void
            unFlagIt() -> void
            discoverIt() -> void
            draw() -> WorldImage
            drawFinal() -> WorldImage
            numOfNeighbors() -> int
            cascade() -> void
     */

    //makes this tile appear with a flag on it
    public void flagIt() {
        this.status = 2;
    }

    //removes the flag from the tile
    public void unFlagIt() {
        this.status = 0;
    }

    //makes this tile discovered
    public void discoverIt() {
        this.status = 1;
    }

    //creates the image for this tile depending on status
    public WorldImage draw() {
        if (this.status == 0) {
            return new OverlayImage(
                    new RectangleImage(20, 20, OutlineMode.SOLID, Color.LIGHT_GRAY),
                    new RectangleImage(20, 20, OutlineMode.OUTLINE, Color.BLACK));
        } else if (this.status == 1) {
            if (this.neighborsWithMine() > 0) {
                WorldImage base = new OverlayImage(
                        new RectangleImage(20, 20, OutlineMode.SOLID, Color.DARK_GRAY),
                        new RectangleImage(20, 20, OutlineMode.OUTLINE, Color.BLACK));

                return new OverlayImage(
                        new TextImage(Integer.toString(this.neighborsWithMine()), 14, Color.CYAN),
                        base);
            } else {
                return new OverlayImage(
                        new RectangleImage(20, 20, OutlineMode.SOLID, Color.DARK_GRAY),
                        new RectangleImage(20, 20, OutlineMode.OUTLINE, Color.BLACK));
            }

        } else {
            WorldImage base = new OverlayImage(
                    new RectangleImage(20, 20, OutlineMode.SOLID, Color.LIGHT_GRAY),
                    new RectangleImage(20, 20, OutlineMode.OUTLINE, Color.BLACK));

            return new OverlayImage(new EquilateralTriangleImage(9, OutlineMode.SOLID, Color.RED), base);
        }
    }

    //creates image for this tile when the game is complete
    public WorldImage drawFinal() {
        if (this.mine) {
            WorldImage b = new OverlayImage(
                    new RectangleImage(20, 20, OutlineMode.SOLID, Color.RED),
                    new RectangleImage(20, 20, OutlineMode.OUTLINE, Color.BLACK));
            return new OverlayImage(
                    new CircleImage(7, OutlineMode.SOLID, Color.BLACK), b);
        } else if (this.status == 0) {
            return new OverlayImage(
                    new RectangleImage(20, 20, OutlineMode.SOLID, Color.LIGHT_GRAY),
                    new RectangleImage(20, 20, OutlineMode.OUTLINE, Color.BLACK));
        } else if (this.status == 1) {
            if (this.neighborsWithMine() > 0) {
                WorldImage base = new OverlayImage(
                        new RectangleImage(20, 20, OutlineMode.SOLID, Color.DARK_GRAY),
                        new RectangleImage(20, 20, OutlineMode.OUTLINE, Color.BLACK));

                return new OverlayImage(
                        new TextImage(Integer.toString(this.neighborsWithMine()), 14, Color.CYAN),
                        base);
            } else {
                return new OverlayImage(
                        new RectangleImage(20, 20, OutlineMode.SOLID, Color.DARK_GRAY),
                        new RectangleImage(20, 20, OutlineMode.OUTLINE, Color.BLACK));
            }

        } else {
            WorldImage base = new OverlayImage(
                    new RectangleImage(20, 20, OutlineMode.SOLID, Color.LIGHT_GRAY),
                    new RectangleImage(20, 20, OutlineMode.OUTLINE, Color.BLACK));

            return new OverlayImage(new EquilateralTriangleImage(9, OutlineMode.SOLID, Color.RED), base);
        }
    }


    // returns the number of a tile's neighbors that have a mine
    public int neighborsWithMine() {
        int num = 0;
        for (Tile t : this.neighbors) {
            if (t.mine) {
                num = num + 1;
            }
        }

        return num;
    }

    // discovers adjacent Tiles and discovers their neighbors recursively if they have no adjacent mines
    public void cascade() {
        this.discoverIt();

        for (Tile t : this.neighbors) {
            if ((t.neighborsWithMine() == 0) && (t.status == 0) && (!t.mine)) {
                t.discoverIt();
                t.cascade();
            } else if ((t.neighborsWithMine() != 0) && (t.status == 0) && (!t.mine)) {
                t.discoverIt();
            }
        }
    }


}

// represents the active game being played
class MinesweeperGame extends World {

    // width in number of pixels
    int width;

    // length in number of pixels
    int length;

    // list of all Tiles on the game board
    ArrayList<Tile> tiles;

    // constructor
    MinesweeperGame(int widthInT, int lengthInT) {
        this.width = widthInT * 20;
        this.length = lengthInT * 20;
        this.tiles = this.makeTileList();
    }

    /*
    TEMPLATE:
        Fields:
            this.width -> int
            this.length -> int
            this.tiles -> ArrayList<Tile>
        Methods:
            widthInTiles() -> int
            lengthInTiles() -> int
            makeTileList() -> ArrayList<Tile>
            makeScene() -> WorldScene
            makePlayingScene() -> WorldScene
            makeFinalScene() -> WorldScene
            makeWinScene() -> WorldScene
            onKeyEvent(String s) -> void
            onMouseClicked(Posn mouse, String buttonName) -> void
            numOfDis() -> int
            posnToTile(Posn p) -> int
            onTick() -> void
     */

    //returns width of game board in number of tiles
    public int wdithInTiles() {
        return this.width / 20;
    }

    // returns length of game board in number of tiles
    public int lengthInTiles() {
        return this.length / 20;
    }

    // creates an array list of simple tiles that number the area of the game
    private ArrayList<Tile> makeTileList() {
        ArrayList<Tile> l = new ArrayList<>();

        // counter for index of array list
        int c = 0;

        // adds the prescribed number of tiles to the tiles array list
        for (int i = 0; i < (this.wdithInTiles() * this.lengthInTiles()); i++) {
            l.add(new Tile());
        }

        // assigns bomb positions to the game
        int j = 0;
        while (j < (this.wdithInTiles() * this.lengthInTiles()) / 4) {
            Random r = new Random();

            if (l.get(r.nextInt((this.wdithInTiles() * this.lengthInTiles()) - 1)).mine) {

            } else {
                l.get(r.nextInt((this.wdithInTiles() * this.lengthInTiles()) - 1)).mine = true;
                j = j + 1;
            }

        }


        // assigns neighbors for all tiles
        for (Tile t : l) {

            if ((c % this.wdithInTiles()) == 0) {
                //left edge
                if (c == 0) {
                    t.neighbors.add(l.get(c + 1));
                    t.neighbors.add(l.get(c + this.wdithInTiles()));
                    t.neighbors.add(l.get(c + (this.wdithInTiles() + 1)));
                } else if (c == (this.lengthInTiles() - 1) * this.wdithInTiles()) {
                    t.neighbors.add(l.get(c + 1));
                    t.neighbors.add(l.get(c - this.wdithInTiles()));
                    t.neighbors.add(l.get(c - (this.wdithInTiles() - 1)));

                } else {
                    t.neighbors.add(l.get(c + 1));
                    t.neighbors.add(l.get(c - this.wdithInTiles()));
                    t.neighbors.add(l.get(c - (this.wdithInTiles() - 1)));
                    t.neighbors.add(l.get(c + this.wdithInTiles()));
                    t.neighbors.add(l.get(c + (this.wdithInTiles() + 1)));
                }

            } else if (c < this.wdithInTiles()) {
                //top row
                if (c == 0) {
                    //top left cell already accounted for
                } else if (c == this.wdithInTiles() - 1) {
                    t.neighbors.add(l.get(c - 1));
                    t.neighbors.add(l.get(c + this.wdithInTiles()));
                    t.neighbors.add(l.get(c + (this.wdithInTiles() - 1)));
                } else {
                    t.neighbors.add(l.get(c + 1));
                    t.neighbors.add(l.get(c - 1));
                    t.neighbors.add(l.get(c + this.wdithInTiles()));
                    t.neighbors.add(l.get(c + (this.wdithInTiles() + 1)));
                    t.neighbors.add(l.get(c + (this.wdithInTiles() - 1)));
                }
            } else if (c % this.wdithInTiles() == this.wdithInTiles() - 1) {
                // right edge
                if (c == this.wdithInTiles() - 1) {
                    //top right cell already accounted for
                } else if (c == (this.wdithInTiles() * this.lengthInTiles()) - 1) {
                    t.neighbors.add(l.get(c - 1));
                    t.neighbors.add(l.get(c - this.wdithInTiles()));
                    t.neighbors.add(l.get(c - (this.wdithInTiles() + 1)));
                } else {
                    t.neighbors.add(l.get(c - 1));
                    t.neighbors.add(l.get(c + this.wdithInTiles()));
                    t.neighbors.add(l.get(c - this.wdithInTiles()));
                    t.neighbors.add(l.get(c + (this.wdithInTiles() - 1)));
                    t.neighbors.add(l.get(c - (this.wdithInTiles() + 1)));
                }
            } else if (c > this.wdithInTiles() * (this.lengthInTiles() - 1)) {
                //bottom row
                if (c == (this.wdithInTiles() * this.lengthInTiles()) - 1) {

                } else {
                    t.neighbors.add(l.get(c + 1));
                    t.neighbors.add(l.get(c - 1));
                    t.neighbors.add(l.get(c - this.wdithInTiles()));
                    t.neighbors.add(l.get(c - (this.wdithInTiles() + 1)));
                    t.neighbors.add(l.get(c - (this.wdithInTiles() - 1)));
                }
            } else {
                //anything in middle that is not on an edge
                t.neighbors.add(l.get(c + 1));
                t.neighbors.add(l.get(c - 1));
                t.neighbors.add(l.get(c - this.wdithInTiles()));
                t.neighbors.add(l.get(c - (this.wdithInTiles() + 1)));
                t.neighbors.add(l.get(c - (this.wdithInTiles() - 1)));
                t.neighbors.add(l.get(c + this.wdithInTiles()));
                t.neighbors.add(l.get(c + (this.wdithInTiles() + 1)));
                t.neighbors.add(l.get(c + (this.wdithInTiles() - 1)));
            }

            c = c + 1;

        }

        return l;
    }


    // 0 = still playing
    // 1 = game over/lost
    // 2 = game over/won
    int theGameIsOver = 0;

    //creates WorldScene for game based on the status of the game conveyed by theGameIsOver
    @Override
    public WorldScene makeScene() {
        if (theGameIsOver == 0) {
            return this.makePlayingScene();
        } else if (theGameIsOver == 1) {
            return this.makeFinalScene();
        } else if (theGameIsOver == 2) {
            return this.makeWinScene();
        } else {
            return this.makePlayingScene();
        }
    }

    //makes WorldScene for active games still being played
    public WorldScene makePlayingScene() {
        //keeps track of wht tile is to be drawn
        int c = 0;
        WorldImage stack = new EmptyImage();
        for (int i = 0; i < this.lengthInTiles(); i++) {
            WorldImage row = new EmptyImage();
            for (int j = 0; j < this.wdithInTiles(); j++) {
                row = new BesideImage(row, this.tiles.get(c).draw());
                c = c + 1;
            }
            stack = new AboveImage(stack, row);
        }

        WorldScene scene = new WorldScene(width, length);
        scene.placeImageXY(stack, (width / 2), (length / 2));

        return scene;
    }

    //makes WorldScene for a game that has been lost
    public WorldScene makeFinalScene() {
        //keeps track of what tile is to be drawn
        int c = 0;
        WorldImage stack = new EmptyImage();
        for (int i = 0; i < this.lengthInTiles(); i++) {
            WorldImage row = new EmptyImage();
            for (int j = 0; j < this.wdithInTiles(); j++) {
                row = new BesideImage(row, this.tiles.get(c).drawFinal());
                c = c + 1;
            }
            stack = new AboveImage(stack, row);
        }

        WorldImage gmOvr = new OverlayImage(
                new TextImage("GAME OVER!!!", 40, FontStyle.REGULAR, Color.RED.darker()),
                new TextImage("GAME OVER!!!", 40, FontStyle.BOLD, Color.BLACK));

        WorldImage finalImg = new OverlayImage(gmOvr, stack);

        WorldScene scene = new WorldScene(width, length);
        scene.placeImageXY(finalImg, (width / 2), (length / 2));

        return scene;
    }

    // makes WorldScene for a game that has been won
    public WorldScene makeWinScene() {
        //keeps track of what tile is to be drawn
        int c = 0;
        WorldImage stack = new EmptyImage();
        for (int i = 0; i < this.lengthInTiles(); i++) {
            WorldImage row = new EmptyImage();
            for (int j = 0; j < this.wdithInTiles(); j++) {
                row = new BesideImage(row, this.tiles.get(c).draw());
                c = c + 1;
            }
            stack = new AboveImage(stack, row);
        }

        WorldImage winTxt = new OverlayImage(
                new TextImage("YOU WIN!!!", 40, FontStyle.REGULAR, Color.GREEN.brighter()),
                new TextImage("YOU WIN!!!", 40, FontStyle.BOLD, Color.BLACK));

        WorldImage finalImg = new OverlayImage(winTxt, stack);

        WorldScene scene = new WorldScene(width, length);
        scene.placeImageXY(finalImg, (width / 2), (length / 2));

        return scene;
    }


    //if any key is pressed after a game is completed, a new game will start
    public void onKeyEvent(String s) {
        if ((theGameIsOver == 1) || (theGameIsOver == 2)) {
            World newWorld = new MinesweeperGame(this.wdithInTiles(), this.lengthInTiles());
            newWorld.bigBang(this.width, this.length, (1.0 / 60.0));
        }
    }

    // if 0, user has not left-clicked yet
    // else, user has left-clicked
    int clkd = 0;

    // keeps track of number of flags in play
    // flags are limited to number of mines in the game
    int flags = 0;

    //if right mouse button is clicked on a tile, that tile will either be given a flag or have a flag removed
    //if left mouse button is clicked on a tile, it could be discovered and display a number,
    //  start a cascade, or lose the game
    public void onMouseClicked(Posn mouse, String buttonName) {
        if (theGameIsOver == 0) {
            if (buttonName == "RightButton") {
                if (this.tiles.get(posnToTile(mouse)).status == 1) {
                    // if discovered, do not flag
                } else if (this.tiles.get(posnToTile(mouse)).status == 2) {
                    this.tiles.get(posnToTile(mouse)).unFlagIt();
                    flags = flags - 1;
                } else if (flags < ((this.wdithInTiles() * this.lengthInTiles()) / 4)) {
                    this.tiles.get(posnToTile(mouse)).flagIt();
                    flags = flags + 1;
                }
            } else if (buttonName == "LeftButton") {
                if (this.tiles.get(posnToTile(mouse)).status == 2) {
                    //if flagged, do not discover
                } else if (this.tiles.get(posnToTile(mouse)).status == 1) {
                    // if discovered, cannot be discovered again
                } else if (this.tiles.get(posnToTile(mouse)).status == 0) {
                    if (!this.tiles.get(posnToTile(mouse)).mine) {
                        //always cascade on first click to better the starting the scenario
                        if (clkd == 0) {
                            clkd = 1;
                            this.tiles.get(posnToTile(mouse)).cascade();
                        } else if (this.tiles.get(posnToTile(mouse)).neighborsWithMine() != 0) {
                            this.tiles.get(posnToTile(mouse)).discoverIt();
                        } else {
                            this.tiles.get(posnToTile(mouse)).cascade();
                        }
                    } else {
                        theGameIsOver = 1;
                    }
                }
            }
        }
        // game is won if the number of undiscovered Tiles is equal to the number of mines on the game board
        if (this.numOfDis() == ((this.wdithInTiles() * this.lengthInTiles()) / 4)) {
            theGameIsOver = 2;
        }
    }

    // returns the number of undiscovered flagged/unflagged Tiles on the game board
    public int numOfDis() {
        int i = 0;
        for (Tile t : this.tiles) {
            if ((t.status == 0) || (t.status == 2)) {
                i = i + 1;
            }
        }

        return i;
    }

    // calculates what tile has been clicked based on the Posn of the click and the dimensions of both
    //  the game board and a singular Tile
    public int posnToTile(Posn p) {
        int x = Math.floorDiv(p.x, 20);
        int y = Math.floorDiv(p.y, 20);

        int ix = (x + (y * this.wdithInTiles()));
        return ix;
    }


    //repeats procedures on every tick
    @Override
    public void onTick() {
        super.onTick();
    }
}

//Examples class
class ExamplesGame {

    void testBigBang(Tester t) {
        MinesweeperGame world = new MinesweeperGame(20, 20);
        world.bigBang(world.width, world.length, (1.0 / 30.0));
    }

    boolean testNeighbor(Tester t) {
        MinesweeperGame world = new MinesweeperGame(4, 4);
        return t.checkExpect(world.tiles.get(0).neighbors.get(0).neighbors.get(0).neighbors,
                world.tiles.get(2).neighbors);
    }

    boolean testNumOfNeighbors1(Tester t)
    {
        MinesweeperGame world = new MinesweeperGame(4,4);
        Tile t0 = new Tile();
        Tile t1 = new Tile();
        Tile t2 = new Tile();
        Tile t3 = new Tile();
        t0.neighbors = new ArrayList<>();
        t2.mine = true;
        t0.neighbors.add(t1);
        t0.neighbors.add(t2);
        t0.neighbors.add(t3);
        return t.checkExpect(t0.neighborsWithMine(), 1);
    }

    boolean testNumOfNeighbors2(Tester t)
    {
        MinesweeperGame world = new MinesweeperGame(4,4);
        Tile t0 = new Tile();
        Tile t1 = new Tile();
        Tile t2 = new Tile();
        Tile t3 = new Tile();
        t0.neighbors = new ArrayList<>();
        t1.mine = true;
        t2.mine = true;
        t3.mine = true;
        t0.neighbors.add(t1);
        t0.neighbors.add(t2);
        t0.neighbors.add(t3);
        return t.checkExpect(t0.neighborsWithMine(), 3);
    }

    boolean testFlagIt1(Tester t)
    {
        MinesweeperGame world = new MinesweeperGame(4,4);
        Tile t0 = new Tile();
        t0.flagIt();
        return t.checkExpect(t0.status, 2);
    }

    boolean testFlagIt2(Tester t)
    {
        MinesweeperGame world = new MinesweeperGame(4,4);
        Tile t0 = new Tile();
        t0.flagIt();
        t0.unFlagIt();
        return t.checkExpect(t0.status, 0);
    }

    boolean testDiscoverIt(Tester t)
    {
        MinesweeperGame world = new MinesweeperGame(4,4);
        Tile t0 = new Tile();
        t0.discoverIt();
        return t.checkExpect(t0.status, 1);
    }

}






