#By Mihai Nica
#Dec 17th 2011
#
#A game set in a maze-like dungeon where you must try and collect as many keys as possible without touching the numerous zombies in the maze
#
#Controls:
#Arrow keys to move around
#Enter key to restart the game when you die
#Esc to quit


import pygame
import random
from pygame.locals import *
import math
import sys

from sets import Set

import os
import platform

pygame.init()

#Naming conventions:
#Constants = ALL CAPS
#Important Global Variables = Capitalized
#
#Controls:
#Arrow keys to move around
#Enter key to restart the game when you die
#Esc to quit

SCREEN_SIZE = 500
DASHBOARD_SIZE = 50
TILE_SIZE = 16
NUM_STARTING_ZOMBIES = 10
NUM_STARTING_KEYS = 5
ZOMBIE_INCREMENT = 4
X_off = 0
Y_off = 0
screen = pygame.display.set_mode((SCREEN_SIZE,SCREEN_SIZE+DASHBOARD_SIZE))

court = ["#############################################",
         "#...........#.......#..........#............#",
         "#.#########.#.#######.########.#.##########.#",
         "#.#.........#.#..............#.#..........#.#",
         "#.#.######.##.#.############.#.##########.#.#",
         "#.#.#.........#......#.......#..........#.#.#",
         "#.#.#.##############...##########.#####.#.#.#",
         "#.#.#.#...#..........#..........#.#...#.#.#.#",
         "#.#...#.#.#.###################.#.#.#.#...#.#",
         "#.###.#.#.#.#.................#.#.#.#.#.###.#",
         "#...#.#.#.#.#.....#.#.........#.#.#.#.#.#...#",
         "###.#.#.#.#.#....#.#.#........#.#.#.#.#.#.###",
         "###.#.#.#.#.#.....#.#.........#.#.#.#.#.#.###",
         "#...#.#.#.#.#......#..........#.#.#.#.#.#...#",
         "#.###.#.#.#.#.................#.#.#.#.#.#.#.#",
         "#.#...#.#.#.#########.#########.#.#.#.#.#.#.#",
         "#.#.#.#.#.#.........#.#.........#.#.#...#.#.#",
         "#.#.#.#.#.#########.#.#.#########.#.#####.#.#",
         "#.#.#...#.........#.#.#.............#.....#.#",
         "#.#.###############.#.#####################.#",
         "#.#.................#.......................#",
         "#.###########################################",
         "#...........................................#",
        "#############################################"] #a sample maze to try out (you should probably set zombies to zero to try this...)

FOV_RADIUS = int(SCREEN_SIZE/32)
FRAMERATE = 30

main_dir = os.path.split(os.path.abspath(''))[0]
data_dir = os.path.join(main_dir, '')

def RandomMaze(sizex=int(35),sizey=int(35),minlen=2,maxlen=20,granularity=4,numwalls=200):
    #Creates a random maze (output looks like 'dungeon' above) by randomly drawing in a bunch of walls
    # of length between minlen and maxlen, and with corridors usually of width "granularity"
    random.seed()
    maxlatticex = int(sizex/granularity)
    maxlatticey = int(sizey/granularity)
    maze = [ ['.' for i in range(sizex) ] for j in range(sizey)]
    for i in range(sizex):
        maze[0][i] = '#'
        maze[sizey-1][i]='#'
    for j in range(sizey):
        maze[j][0] = '#'
        maze[j][sizex-1] = '#'

    for i in range(numwalls):
        corridorlen = random.randint(minlen,maxlen)
        startx = granularity*random.randint(1,maxlatticex)-1
        starty = granularity*random.randint(1,maxlatticey)-1
        if maze[starty][startx] == '.':
            x = startx
            y = starty
            dir = random.randint(0,1)*2 - 1
            which = random.randint(0,1)
            dx = (dir,0)[which]
            dy = (dir,0)[1-which]
            for l in range(corridorlen):
                if x > 0 and y > 0 and x < sizex and y < sizey and maze[y][x]=='.':
                    maze[y][x] = '#'
                    x += dx
                    y += dy
    return maze



#functions to create our resources

def floodfill_connected(maze):
    #A really slow and stupid algorithm that checks that the maze is all connected (its only called once so its ok!)
    #This makes sure that the player doesnt spend all day looking for a key that is hidden in a room thats impossible to get to
    width = len(maze[0])
    height = len(maze)
    floortiles = Set([(i,j) for i in range(width) for j in range(height) if maze[j][i] == '.'])
    visited = Set([])
    for i in range(len(maze[0])):
        if maze[1][i] == '.':
            visited.add((i,1))
            break
    added_something = True
    while added_something == True:
        added_something = False
        for node in visited:
            if node[0]+1 < width and maze[node[1]][node[0]+1] == '.' and (node[0]+1,node[1]) not in visited:
                visited.add((node[0]+1,node[1]))
                added_something = True
                break
            elif node[0]-1 >= 0 and maze[node[1]][node[0]-1] == '.' and (node[0]-1,node[1]) not in visited:
                visited.add((node[0]-1,node[1]))
                added_something = True
                break
            elif node[1]+1 < height and maze[node[1]+1][node[0]] == '.' and (node[0],node[1]+1) not in visited:
                visited.add((node[0],node[1]+1))
                added_something = True
                break
            elif node[0]-1 >= 0 and maze[node[1]-1][node[0]] == '.' and (node[0],node[1]-1) not in visited:
                visited.add((node[0],node[1]-1))
                added_something = True
                break
    return visited == floortiles

def load_image(name, colorkey=None):
    #Basic script that loads an image and returns the image and its rect
    fullname = os.path.join('', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error:
        print ('Cannot load image:', fullname)
        raise SystemExit(str(geterror()))
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image, image.get_rect()

class tileClass(pygame.sprite.Sprite):
    #an extension of the sprite class that holds either a floor tile or a wall tile
    #used to store/draw the maze
    floortile = load_image('floortile.png')
    walltile = load_image('walltile.png')
    def __init__(self,type,X,Y):
        pygame.sprite.Sprite.__init__(self)
        if type == ".":
            self.image = tileClass.floortile[0]
            self.rect = tileClass.floortile[1].copy()
        elif type == "#":
            self.image = tileClass.walltile[0]
            self.rect = tileClass.walltile[1].copy()
        self.rect.topleft = (map2screen(X,Y))

def load_guy_images(name, colorkey=None):
    #A 'guy' is a standard character in the game (see guyClass below)
    #A guy can face in any of the four cardinal directions, and there are 2 images in each direction which are used for animating them
    #This little function just makes loading the images for such a guy a bit easier
    im_l = [0,0]
    im_r = [0,0]
    im_d = [0,0]
    im_u = [0,0]
    im_l[0], im_rect = load_image(name+'_l_1.png', -1)
    im_r[0] = load_image(name+'_r_1.png', colorkey)[0]
    im_u[0] = load_image(name+'_u_1.png', colorkey)[0]
    im_d[0] = load_image(name+'_d_1.png', colorkey)[0]
    im_l[1] = load_image(name+'_l_2.png', colorkey)[0]
    im_r[1] = load_image(name+'_r_2.png', colorkey)[0]
    im_u[1] = load_image(name+'_u_2.png', colorkey)[0]
    im_d[1] = load_image(name+'_d_2.png', colorkey)[0]
    return im_l, im_r, im_d, im_u, im_rect

class guyClass(pygame.sprite.Sprite):
    #an extension of the Sprite class
    #to be imported by any characters in the game
    #A 'Guy' is a standardized characer in the game e.g a monster or the player's character
    #They walk around the maze etc., and they can face in any four of the cardinal directions.
    #This class does the things common to all guys:
    # -animating their walkin
    # -moving them around
    # -checking for collisions with walls and other 'guys'
    #This class is imported and specialize in the class for each type of guy (see playerClass or zombieClass below)
    #Note that: im_l, im_r, im_d, im_u must be loaded and defined in these classes or the guyClass will fail
    # each im_l, im_r, im_d, im_u are each lists with two pictures, one for each of the frames where the guy is facing left, right, down and up respectivly.
    def __init__(self,x_init,y_init,vx_init=0,vy_init=0):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer to make a guy a spcial type of sprite and set the sprite image and rect
        self.image= self.im_l[0]
        self.rect = self.im_rect.copy()
        self.x = x_init #x,y are the MAP coordinates of the guy
        self.y = y_init
        self.vx = vx_init #velocity of the guy; measured in gridsquares per second
        self.vy = vy_init
        self.calc_screen_coords() #calculate the SCREEN coordinates from the map coordinates

        #Animation stuff:
        self._animationstate = 0 #used for animating!
        self._animationlength = 0.2 #how long each step in the animation is; measured in seconds
        self._timesincelastanimation = 0 #how many calls ago did we change the animation?
    def calc_screen_coords(self):
        self.rect.midbottom = map2screen(self.x,self.y) #move the sprite to the correct screen coordinates based on map coordinates
        self.rect.move_ip(0,2)
    def hit_a_wall(self):
        pass #called when the guy hits a wall (if this is needed, will be specialized)
    def hit_by(self,who):
        pass  #called when the guy is hit by guy (if this is needed, will be specialized)
    def I_hit(self,who):
        pass #called when the guy hits another guy (if this is needed, will be specialized)
    def move(self,vx,vy):
        self.x += vx/FRAMERATE #moves the guy! First map coords, and then screen coords
        self.y += vy/FRAMERATE
        self.calc_screen_coords()
    def update(self):
        dummy_vx = self.vx #move the guy! keep track of how far we moved him in case we need to unmove him later if he bumps into something
        dummy_vy = self.vy
        self.move(dummy_vx,dummy_vy)
        dummy_collision_flag = False

        #check for collisions with the other guys
        AllGuyGroup.remove(self)
        for guy in pygame.sprite.spritecollide(self, AllGuyGroup, False):
            dummy_collision_flag = True
            guy.hit_by(self)
            self.I_hit(guy)
        AllGuyGroup.add(self)

        #check for collisions with walls
        if Map.blocked(int(self.x),int(self.y)):
            dummy_collision_flag = True
            self.hit_a_wall()

        if dummy_collision_flag == True: #if he collided with something, we have to unmove him
            self.move(-dummy_vx,-dummy_vy)

        #Animation Routine:
        # -change his animation state to point in the right direction if he is moving
        # -change animation frame if we've been displaying the old one for long enough
        if self.vx != 0 or self.vy != 0:
            if self.vy < self.vx:
                if self.vy < -self.vx:
                    self.image = self.im_u[self._animationstate]
                else:
                    self.image = self.im_r[self._animationstate]
            else:
                if self.vy < -self.vx:
                    self.image = self.im_l[self._animationstate]
                else:
                    self.image = self.im_d[self._animationstate]
            if self._timesincelastanimation > self._animationlength*FRAMERATE:
                self._animationstate = 1 - self._animationstate
                self._timesincelastanimation = 0
            else:
                self._timesincelastanimation += 1

class zombieClass(guyClass):
    #extends the guyClass!
    #handles the current bad guys
    #has 3 states:
    # 'W' = Wandering - he mills about for a few seconds and then picks a new direction and repeats
    # 'K' = Kill - he runs towards the targetx,targety to try and hurt the player
    # 'L' = Locked - just like 'W' excpet this state is locked so he cant switch into kill mode unless he finishs the action

    im_l, im_r, im_d, im_u, im_rect = load_guy_images('baddie',-1) #load pictures
    def __init__(self, X,Y):
        guyClass.__init__(self,X,Y)
        self.speed = 2  #measured in gridsquares per second
        self._animationlength = 0.4 / self.speed
        self.state = 'W'
        self.hit_a_wall() #initializes his direction
        self.hitwaittimer = 0.5 #Period to wait before the bad guys can hit again in sec
        self.timesincelasthit = 0 #Stores the time since last hit
        self.targetx = -1 #targets for the kill mode
        self.targety = -1
        self._waittime = 0.5 #the time between actions when wandering
        self._timesincelastact = random.random()*self._waittime*FRAMERATE
    def random_turn(self):
        # if he hits a wall point him in a random direction
        dummy_angle = random.random()*2*3.14
        self.vx = self.speed*math.cos(dummy_angle)
        self.vy = self.speed*math.sin(dummy_angle)
    def turn_around(self):
        self.vx = -self.vx*(0.1*random.random()+0.9)
        self.vy = self.vy*(0.1*random.random()+0.9)
    def hit_a_wall(self):
        if self.state == 'K':
            self.state = 'L' #set him in locked, or else they get jammed up near the player
        self.random_turn()
    def I_hit(self,who):
        self.hit_a_wall()
    def update(self):
        guyClass.update(self)
        if self.timesincelasthit <= FRAMERATE*self.hitwaittimer:
        #Update hit timer so to check whether zombie has waited long enough between consecutive hits. If
        #condition to not allow for overflow
            self.timesincelasthit += 1
        if self.state != 'L' and VisibleGuyGroup.has(self) and Player.health > 0 : #if he the guy can see him, switch into kill and record the players coordinates
            self.state = 'K'
            self.targetx = Player.x
            self.targety = Player.y
        if self.state == 'W' or self.state == 'L': #in these modes he just waits until his timer goes off
            self._timesincelastact += 1
            if self._timesincelastact > self._waittime*FRAMERATE:
                self._timesincelastact = 0
                self.random_turn()
                if self.state == 'L':
                    self.state = 'W'
                    self._timesincelastact = 0
        elif self.state == 'K': #in this mode he points toward his target square
            self.vx = self.speed*(self.targetx - self.x)/math.hypot((self.x - self.targetx),(self.y - self.targety))
            self.vy = self.speed*(self.targety - self.y)/math.hypot((self.x - self.targetx),(self.y - self.targety))
            if math.hypot((self.x - self.targetx),(self.y - self.targety)) < 1 or Player.health <= 0: #if he gets to his target square:
                self.state = 'W'

class playerClass(guyClass):
    #extends the guyClass!
    #handles the player
    im_l, im_r, im_d, im_u, im_rect = load_guy_images('wiz',-1)
    skel_im, skel_rect = load_image('skel.png',-1) #used when you die
    def __init__(self, X ,Y):
        guyClass.__init__(self,X,Y)
        self.speed = 8  #measured in gridsquares per second
        self._animationlength = 0.05
        self.health = 25
    def hit_by(self,guy): #if you get hit by someone, it must be a monster, so you lose health
        if(VisibleGuyGroup.has(guy) and guy.timesincelasthit>FRAMERATE*guy.hitwaittimer-1):
            self.health -= 1
            guy.timesincelasthit = 0
            if len(Dashboard.heartlist) > 0: #if there are any hearts in the dashboard, remove one
                Dashboard.heartlist.pop()
                Dashboard.heartgroup = pygame.sprite.RenderPlain(Dashboard.heartlist)
    def update(self):
        keystate = pygame.key.get_pressed()
        self.vx = self.speed*(keystate[K_RIGHT] - keystate[K_LEFT])*1.0
        self.vy = self.speed*(keystate[K_DOWN] - keystate[K_UP])*1.0
        if self.health < 0: #if you're dead:
            self.speed = 0 #set speed to zero so you cant move around anymore
            self.image = playerClass.skel_im #change to the skeletan
            self.rect.size = playerClass.skel_rect.size
        guyClass.update(self)

class mapClass(object):
    #handles the map (but not the map images), and mostly is used to calculate visibility in the map
    #The following array of multipliers allows the code to be written for a single octant only, and then all other octants can be transformed via reflections
    mult = [
                [1,  0,  0, -1, -1,  0,  0,  1],
                [0,  1, -1,  0,  0, -1,  1,  0],
                [0,  1,  1,  0,  0, -1, -1,  0],
                [1,  0,  0,  1, -1,  0,  0, -1]
            ]
    def __init__(self, map_in):
        #Holds a list of lists which tells you in one charater which type of tile is at each coord in the map
        #  . = floor, # = wall
        self.tiletype = map_in
        self.width, self.height = len(map_in[0]), len(map_in)
    def do_FOV(self,n,m,fov_rad,fun):
        #Calls the function 'fun' for every (X,Y) visimble from (n,m)
        for oct in range(8):
        #Recursive visibility casting in each of the 8 orthants, from the starting point
            self._cast_light(n, m, 1, 1.0, 0.0, fov_rad,
                            self.mult[0][oct], self.mult[1][oct],
                            self.mult[2][oct], self.mult[3][oct], 0, fun)
    def blocked(self, n, m):
        #Returns whether or not the square at (n,m) is opaque. Currently is opaque <=> is a '#' wall or offscreen
        return (n < 0 or m < 0
                or n >= self.width or m >= self.height
                or self.tiletype[m][n] == "#")
    def _cast_light(self, cx, cy, row, start, end, radius, xx, xy, yx, yy, id,fun):
        #this is where the heavy duty work for calculating visbility happens
        #This calls "fun(X,Y)" for every X,Y visible from cx, cy where:
        # -X,Y must be within radius of cx,cy
        # -the slope from cx,cy to X,Y is between start and end
        # -the xx,xy,yx,yy are multipliers that contain which orthant we are in
        #The way this works is recursivly, by making new calls with modified slope values when obstacles are encountered
        #Note: even though the variable names are x's and y's instead of n's and m's here, these ones are integers
        if start < end:
            return
        for j in range(row, radius+1):
            dx = -j-1 
            dy = -j
            blocked = False
            while dx <= 0:
                dx += 1
                # Translate the dx, dy coordinates into map coordinates:
                X, Y = cx + dx * xx + dy * xy, cy + dx * yx + dy * yy
                # l_slope and r_slope store the slopes of the left and right
                # extremities of the square we're considering:
                l_slope = (dx-0.5)/(dy+0.5)
                r_slope = (dx+0.5)/(dy-0.5)
                if start < r_slope:
                    continue
                elif end > l_slope:
                    break
                else:
                    # Our light beam is touching this square, so call "fun" here
                    if dx*dx + dy*dy < radius*radius:
                        if 0 <= X < self.width and 0 <= Y < self.height:
                            fun(X,Y)
                    if blocked:
                        # we're scanning a row of blocked squares:
                        if self.blocked(X, Y):
                            new_start = r_slope
                            continue
                        else:
                            blocked = False
                            start = new_start
                    else:
                        if self.blocked(X, Y) and j < radius:
                            # This is a blocking square, start a child scan:
                            blocked = True
                            self._cast_light(cx, cy, j+1, start, l_slope,
                                             radius, xx, xy, yx, yy, id+1, fun)
                            new_start = r_slope
            # Row is scanned; do next row unless last square was blocked:
            if blocked:
                break
    def _calcPOVtilehelper(self,X,Y):
        #see calcPOCtiles
        VisibleTileGroup.add(TileArray[Y][X]) #add the tile at X,Y to the group of visible tiles and then move it to the right location on scren
        TileArray[Y][X].rect.topleft = map2screen(X,Y)
        if self.tiletype[Y][X] == ".":
            VisibleFloorGroup.add(TileArray[Y][X])
    def calcPOVtiles(self,n,m):
        #Set up the VisibleTileGroup and VisibleFloorGroup from the POV of someone at n,m
        VisibleTileGroup.empty()
        VisibleFloorGroup.empty()
        self.do_FOV(n,m,FOV_RADIUS, lambda X,Y: self._calcPOVtilehelper(X,Y))
        self._calcPOVtilehelper(n,m) #adds the tile your standing on,because self.do_FOV doesnt do this one

def map2screen(X,Y):
    #outputs the screen coordinates of the thing at grid coords X,Y
    return -TILE_SIZE*X_off + X*TILE_SIZE + SCREEN_SIZE/2, -TILE_SIZE*Y_off + Y*TILE_SIZE + SCREEN_SIZE/2

class keyClass(pygame.sprite.Sprite):
    #used for the objects floating around the maze..curently just keys
    im_key = load_image('key.png',-1)
    def __init__(self,x_init,y_init):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer to make a guy a spcial type of sprite and set the sprite image and rect
        self.image = dashboardClass.im_key[0]
        self.rect = dashboardClass.im_key[1].copy()
        self.x = x_init
        self.y = y_init
    def update(self):
        self.rect.topleft = map2screen(int(self.x),int(self.y)) #update the screen coordinates of the key from map coordinates
        if math.hypot(Player.x-self.x,Player.y-self.y) < 1: #if the player is near the key, he picks it up!
            Dashboard.addkey()
            addKey()
            self.kill()
            addZombie(ZOMBIE_INCREMENT)

class dashboardClass:
    #the dashboard displays information for the player, currently his health and the keys he's picked up
    im_heart = load_image('heart.png',-1)
    im_key = load_image('key.png',-1)
    def __init__(self):
        self.heartlist = []
        self.heartgroup = pygame.sprite.RenderPlain(self.heartlist) #make a sprite group for all the hearts
        for i in range(Player.health): #add a bunch of hearts to the players dashboard
            self.addheart()

        self.keylist = []  #same procedure for the hearts but now for the keys
        self.keygroup = pygame.sprite.RenderPlain(self.keylist)
    def addheart(self): #adds a heart to the dashboard
        dummy_heart = pygame.sprite.Sprite()
        dummy_heart.image = dashboardClass.im_heart[0]
        dummy_heart.rect = dashboardClass.im_heart[1].copy()
        dummy_heart.rect.topleft = (dummy_heart.rect.width*len(self.heartlist),SCREEN_SIZE+DASHBOARD_SIZE/2)
        self.heartlist.append(dummy_heart)
        self.heartgroup.add(dummy_heart)
    def addkey(self):
        dummy_key = pygame.sprite.Sprite() #adds a key to the dashboard
        dummy_key.image = dashboardClass.im_key[0]
        dummy_key.rect = dashboardClass.im_key[1].copy()
        dummy_key.rect.topleft = (dummy_key.rect.width*(len(self.keylist)),SCREEN_SIZE)
        self.keylist.append(dummy_key)
        self.keygroup.add(dummy_key)
    def draw(self):
        self.heartgroup.draw(screen)
        self.keygroup.draw(screen)

def addZombie(num_to_add = 1): #adds zombies to the maze!
    dummy_current_num_guys = len(AllGuyGroup)
    while len(AllGuyGroup) < dummy_current_num_guys + num_to_add:
        dummy_guy = zombieClass(random.randint(0,Map.width-1),random.randint(0,Map.height-1))
        if math.hypot(dummy_guy.x-Player.x,dummy_guy.y-Player.y)>5 and not pygame.sprite.spritecollideany(dummy_guy, AllGuyGroup) and not Map.blocked(int(dummy_guy.x),int(dummy_guy.y)):
            AllGuyGroup.add(dummy_guy)

def addKey(num_to_add = 1): #adds keys to the maze!
    dummy_current_num_objects = len(AllObjectGroup)
    while len(AllObjectGroup) < dummy_current_num_objects + num_to_add:
        dummy_object = keyClass(random.randint(0,Map.width-1),random.randint(0,Map.height-1))
        if math.hypot(dummy_object.x-Player.x,dummy_object.y-Player.y)>5 and not Map.blocked(int(dummy_object.x),int(dummy_object.y)):
            AllObjectGroup.add(dummy_object)

while True:
    Map = mapClass(RandomMaze()) #creates a random maze
    if floodfill_connected(Map.tiletype): #only exit if the maze is all one connected piece, or else we might accidently place keys that are impossible to place
        break
TileArray = [[  tileClass(Map.tiletype[j][i],i,j) for i in range(Map.width)] for j in range(Map.height)] #array of sprites containing the map tiles

#print Map.tiletype

clock = pygame.time.Clock()
Player = playerClass(int(Map.width/2),int(Map.height/2)) #creates the player

AllGuyGroup = pygame.sprite.RenderPlain([Player]) #group of sprites containg all the guys, starts with just the player
addZombie(NUM_STARTING_ZOMBIES)
AllObjectGroup = pygame.sprite.RenderPlain([]) #group of sprites - holds all the objects (just keys right now)
addKey(NUM_STARTING_KEYS)

VisibleGuyGroup = pygame.sprite.RenderPlain([]) #group of sprites - holds the visible guys (we only draw these guys)
VisibleFloorGroup = pygame.sprite.RenderPlain([]) #group of sprites - holds the visible floor tiles (used to figure out which guys are visible)
VisibleTileGroup = pygame.sprite.RenderPlain([]) #group of sprites - visible floor tiles plus visible walls
VisibleObjectGroup = pygame.sprite.RenderPlain([]) #group of sprites - holds the visible keys!

Dashboard = dashboardClass()

#p = pygame.time.get_ticks() used to time how fast the program is running
while True:
    #print pygame.time.get_ticks() - p
    #print Player.health
    #p = pygame.time.get_ticks()
    for event in pygame.event.get():
        if event.type == QUIT or (event.type==KEYDOWN and event.key==K_ESCAPE):
            pygame.quit()
            sys.exit()


    X_off = Player.x #changes where the game is drawn so the player is always in the center
    Y_off = Player.y
    for guy in AllGuyGroup: #
        guy.calc_screen_coords()
    AllGuyGroup.update()
    AllObjectGroup.update()

    Map.calcPOVtiles(int(Player.x),int(Player.y))

    VisibleGuyGroup.empty() #set the visible guys to the guys who are touching a piece of visible floor
    for guy in pygame.sprite.groupcollide(AllGuyGroup, VisibleFloorGroup,False,False).keys():
        VisibleGuyGroup.add(guy)

    VisibleObjectGroup.empty()
    for object in pygame.sprite.groupcollide(AllObjectGroup, VisibleFloorGroup,False,False).keys():
        VisibleObjectGroup.add(object)



    VisibleTileGroup.draw(screen) #Draw everything!
    VisibleObjectGroup.draw(screen)
    VisibleGuyGroup.draw(screen)
    Dashboard.draw()
    pygame.display.flip()
    clock.tick(FRAMERATE)
    screen.fill( (0,0,0) )

    keystate = pygame.key.get_pressed()
    if Player.health < 0 and keystate[K_RETURN]:
        Player.speed = 8
        Player.image = playerClass.im_l[0]
        Player.health = 10
        while True:
            Map = mapClass(RandomMaze()) #creates a random maze
            if floodfill_connected(Map.tiletype): #only exit if the maze is all one connected piece, or else we might accidently place keys that are impossible to place
                break
        TileArray = [[  tileClass(Map.tiletype[j][i],i,j) for i in range(Map.width)] for j in range(Map.height)] #array of sprites containing the map tiles
        AllGuyGroup = pygame.sprite.RenderPlain([Player])
        addZombie(NUM_STARTING_ZOMBIES)
        AllObjectGroup.empty()# = pygame.sprite.RenderPlain([]) #group of sprites - holds all the objects (just keys right now)
        addKey(NUM_STARTING_KEYS)
        Dashboard = dashboardClass()
