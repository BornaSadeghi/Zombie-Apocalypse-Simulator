from gui import *
import math, random

mixer.pre_init(11025, -16, 2, 512)
mixer.init()

STATE = 0
'''
States
0: home menu
1: simulation
2: summary
'''

saveFile = "zombiesim.txt"

# containers for simulation objects
openCells = []
grid = []
obstacles = []
blood = [] # blood objects on the grid

humans = []  # human, zombie, and item objects
zombies = []
items = []

coloursFile = open("colours.txt").read().split("\n")
colours = []

for i in range (9):
    print(i)
    line = coloursFile[i].split(",")
    colours.append((int(line[0]), int(line[1]), int(line[2])))

BLACK = colours[0]
RED = colours[1]
WHITE = colours[2]
DARKGREEN = colours[3]
NAVAJOWHITE = colours[4]
ENEMYRED = colours[5]
DARKRED = colours[6]
SEAGREEN = colours[7]
GREEN = colours[8]

# variables
gridSize = 20
cellSpacing = 0
cellSize = 10

simSpeed = 1

numHumans = 10
numZombies = 10
numObstacles = 50
numItems = 10
itemRate = 10  # chance that any generation will spawn an item
infectionRate = 30  # chance that a zombie killing a human will create a zombie


# stats
generation = 1
humansAlive = numHumans
zombiesAlive = numZombies
humanDeathsByStarve = 0
zombieDeathsByStarve = 0
numInfections = 0

numItemsOnGrid = 0

soundFile = "sounds\\"

# sprites
imgFile = "sprites\\"
uiFile = imgFile + "ui\\"
humanImg = image.load(imgFile + "human.png")
zombImg = image.load(imgFile + "zombie.png")
foodImg = image.load(imgFile + "food.png")
healImg = image.load(imgFile + "heal.png")
weapImg = image.load(imgFile + "weapon.png")
houseImg = image.load(imgFile + "house.png")
treeImg = image.load(imgFile + "tree.png")
bloodImg = image.load(imgFile + "blood.png")
gridImg = image.load(imgFile + "gridIcon.png")
infRateImg = image.load(imgFile + "infRate.png")
itemRateImg = image.load(imgFile + "itemrate.png")

buzzSound = mixer.Sound(soundFile+"buzz.wav")

# ui sprites
arrowDownImg = image.load(uiFile + "arrowdown.png")
arrowDownHoveredImg = image.load(uiFile + "arrowdownhovered.png")
arrowUpImg = image.load(uiFile + "arrowup.png")
arrowUpHoveredImg = image.load(uiFile + "arrowuphovered.png")
pauseImg = image.load(uiFile + "pause.png")
pauseImgHovered = image.load(uiFile + "pausehovered.png")

# random shade of green for grass
def randGreen():
    g = random.randrange(180, 200)
    return 0, g, 0


# convert between pixels and grid coords
def toGridPos(pixPos):
    return pixPos[0] // cellSize, pixPos[1] // cellSize

# convert grid pos to scree pos
def toPixelPos(gridPos):
    x, y = gridPos[0] * cellSize, gridPos[1] * cellSize
    return x + (gridPos[0]) * cellSpacing, y + (gridPos[1]) * cellSpacing

# dist between two points
def dist(point1, point2):
    diffX = point2[0] - point1[0]
    diffY = point2[1] - point1[1]
    return math.sqrt(diffX ** 2 + diffY ** 2)

# takes in pos(x,y) and finds the closest object in lst (list) relative to it
def closest(pos, lst):
    item = None
    mn = 1000
    for i in lst:
        d = dist(pos, i.pos)
        if d < mn:
            item = i
            mn = d
    return item


class Blood:  # blood stain

    def __init__(self, pos):
        self.pos = pos
        self.pixPos = toPixelPos(pos)
        
        rect = self.pixPos[0], self.pixPos[1], cellSize, cellSize
        self.sprite = Image(rect, bloodImg, 1)

    def draw(self):
        self.sprite.draw()


class Weapon:

    def __init__(self):
        global numItemsOnGrid
        self.pos = random.choice(openCells)
        self.pixPos = toPixelPos(self.pos)
        
        rect = self.pixPos[0], self.pixPos[1], cellSize, cellSize
        self.sprite = Image(rect, weapImg, 1)
        self.damage = random.randrange(3, 5)
        
        numItemsOnGrid += 1

    def draw(self):
        self.sprite.draw()


class Medkit:

    def __init__(self):
        global numItemsOnGrid
        self.pos = random.choice(openCells)
        self.pixPos = toPixelPos(self.pos)
        
        rect = self.pixPos[0], self.pixPos[1], cellSize, cellSize
        self.sprite = Image(rect, healImg, 1)
        self.healAmount = random.randrange(5, 10)
        
        numItemsOnGrid += 1

    def draw(self):
        self.sprite.draw()


class Food:

    def __init__(self):
        global numItemsOnGrid
        self.pos = random.choice(openCells)
        self.pixPos = toPixelPos(self.pos)
        
        rect = self.pixPos[0], self.pixPos[1], cellSize, cellSize
        self.sprite = Image(rect, foodImg, 1)
        self.replenish = random.randrange(5, 10)
        
        numItemsOnGrid += 1

    def draw(self):
        self.sprite.draw()

# spawns a random item by chance (itemRate)
def spawnItem ():
    global numItemsOnGrid, openCells
    if random.random()*100 < itemRate and numItemsOnGrid < len(openCells):
        item = random.choice((Food, Medkit, Weapon))()
        items.append(item)


class Obstacle:

    def __init__(self):
        self.pos = random.choice(openCells)
        self.pixPos = toPixelPos(self.pos)
        
        rect = self.pixPos[0], self.pixPos[1], cellSize, cellSize
        sprite = random.choice((houseImg, treeImg))
        self.sprite = Image(rect, sprite, 1)
        
        openCells.remove(self.pos)

    def draw(self):
        self.sprite.draw()

        
class Human:

    def __init__(self):
        self.pos = random.choice(openCells)
        self.pixPos = toPixelPos(self.pos)
        
        rect = self.pixPos[0], self.pixPos[1], cellSize, cellSize
        self.sprite = Image(rect, humanImg, 1)
        self.health = 20
        self.hunger = 30
        self.strength = random.randrange(4, 10)
        
    def move(self):  # tries to move towards the nearest item
        global humansAlive, humanDeathsByStarve
        if self.hunger == 0:  # first check if it is alive
            self.health -= 1;
            if self.health <= 0:
                humanDeathsByStarve += 1
        else:
            self.hunger -= 1;

        if self.health <= 0:
            humans.remove(self)
            blood.append(Blood(self.pos))
            humansAlive -= 1
            return
        
        adjCells = [  # adjacent squares
            (self.pos[0] - 1, self.pos[1] - 1), (self.pos[0], self.pos[1] - 1), (self.pos[0] + 1, self.pos[1] - 1),
            (self.pos[0] - 1, self.pos[1]), (self.pos[0] + 1, self.pos[1]),
            (self.pos[0] - 1, self.pos[1] + 1), (self.pos[0], self.pos[1] + 1), (self.pos[0] + 1, self.pos[1] + 1),
        ]
        
        closestItem = closest(self.pos, items)
        closestZomb = closest (self.pos, zombies) 
        
        mx = 0
        chosenSquare = None
        for pos in adjCells:  # get best square
            
            if closestItem != None:
                di = dist(pos, closestItem.pos)
            else:
                di = 1000
                
            if closestZomb != None:
                dz = dist(pos, closestZomb.pos)
            else:
                dz = 1000
            
            if closestItem == closestZomb == None:
                chosenSquare = None
                break
            
            if di == 0:
                chosenSquare = pos
                break
            
            if pos in openCells:  # humans make decisions on squares
                value = dz / math.sqrt(di)  # with this formula
                if value > mx:
                    mx = value
                    chosenSquare = pos

        if chosenSquare != None:
            self.pos = chosenSquare
            self.pixPos = toPixelPos(self.pos)
            rect = self.pixPos[0], self.pixPos[1], cellSize, cellSize
            self.sprite.rect = rect
            
        for i in items:
            if self.pos == i.pos:
                items.remove(i)
                if type(i) == Food:
                    self.hunger += i.replenish
                elif type(i) == Medkit:
                    self.health += i.healAmount
                else:  # weapon
                    self.strength += i.damage

    def attack(self):  # attacks a zombie if in range
        for z in zombies:
            if z.pos == self.pos:
                z.health -= self.strength

    def draw(self):
        self.sprite.draw()


class Zombie:

    def __init__(self):
        self.pos = random.choice(openCells)
        self.pixPos = toPixelPos(self.pos)
        
        rect = self.pixPos[0], self.pixPos[1], cellSize, cellSize
        self.sprite = Image(rect, zombImg, 1)
        self.health = 16
        self.hunger = 34
        self.strength = random.randrange(3, 8)
        
    def move(self):  # tries to move towards the nearest human
        global zombiesAlive, zombieDeathsByStarve
        if self.hunger == 0:  # first check if it is still alive
            self.health -= 1;
            if self.health <= 0:
                zombieDeathsByStarve += 1
        else:
            self.hunger -= 1;
            
        if self.health <= 0:
            zombies.remove(self)
            blood.append(Blood(self.pos))
            zombiesAlive -= 1
            return
        
        adjCells = [  # adjacent cells
            (self.pos[0] - 1, self.pos[1] - 1), (self.pos[0], self.pos[1] - 1), (self.pos[0] + 1, self.pos[1] - 1),
            (self.pos[0] - 1, self.pos[1]), (self.pos[0] + 1, self.pos[1]),
            (self.pos[0] - 1, self.pos[1] + 1), (self.pos[0], self.pos[1] + 1), (self.pos[0] + 1, self.pos[1] + 1),
        ]
        
        target = closest(self.pos, humans)
        
        mn = 1000
        chosenSquare = None
        if target != None:
            for pos in adjCells:  # get closest square to the human and move to it
                d = dist(pos, target.pos)
                if pos in openCells:
                    if d < mn:
                        mn = d
                        chosenSquare = pos

        if chosenSquare != None:
            self.pos = chosenSquare
            self.pixPos = toPixelPos(self.pos)
            rect = self.pixPos[0], self.pixPos[1], cellSize, cellSize
            self.sprite.rect = rect
        
    def attack(self):  # attacks a human if in range
        global numInfections, humansAlive, zombiesAlive, numZombies
        for h in humans:
            if h.pos == self.pos:
                h.health -= self.strength
                self.hunger += self.strength
                if h.health <= 0 and random.random()*100 < infectionRate:  # infect the human by chance
                    infected = Zombie()
                    infected.pos = self.pos
                    infected.pixPos = toPixelPos(self.pos)
                    
                    humans.remove(h)
                    zombies.append(infected)
                    humansAlive -= 1
                    zombiesAlive += 1
                    numInfections += 1
                
    def draw(self):
        self.sprite.draw()

        
class Cell:

    def __init__(self, rect):
        x, y, w, h = rect
        self.bg = Rect ((x, y, w, h), randGreen(), 0)
        self.pos = toGridPos((x,y))

    def update(self, colour):
        self.bg.colour = colour

    def draw(self):
        self.bg.draw()

# home menu
# shifts the home menu selections
x,y,w,h = 85,100,SIZE[0]-50, SIZE[1]-300


# selection screen ui elements
gridArrowUp = Image((x, y, 100, 100), arrowUpImg, 1)
humanArrowUp = Image((x+120, y, 100, 100), arrowUpImg, 1)
zombieArrowUp = Image((x+240, y, 100, 100), arrowUpImg, 1)
obsArrowUp = Image((x+360, y, 100, 100), arrowUpImg, 1)
foodArrowUp = Image((x+480, y, 100, 100), arrowUpImg, 1)
itemRateArrowUp = Image((x+600, y, 100, 100), arrowUpImg, 1)
infectRateArrowUp = Image((x+720, y, 100, 100), arrowUpImg, 1)

gridArrowDown = Image((x, h, 100, 100), arrowDownImg, 1)
humanArrowDown = Image((x+120, h, 100, 100), arrowDownImg, 1)
zombieArrowDown = Image((x+240, h, 100, 100), arrowDownImg, 1)
obsArrowDown = Image((x+360, h, 100, 100), arrowDownImg, 1)
foodArrowDown = Image((x+480, h, 100, 100), arrowDownImg, 1)
itemRateArrowDown = Image((x+600, h, 100, 100), arrowDownImg, 1)
infectRateArrowDown = Image((x+720, h, 100, 100), arrowDownImg, 1)

gridSizeText = Text((x, h-y//1.5, 100, 100), str(gridSize), WHITE,"lucida console", 18, 1, 0,False,True)
numHumansText = Text((x+120, h-y//1.5, 100, 100), str(numHumans), WHITE,"lucida console", 18, 1, 0,False,True)
numZombiesText = Text((x+240, h-y//1.5, 100, 100), str(numZombies), WHITE,"lucida console", 18, 1, 0,False,True)
numObstaclesText = Text((x+360, h-y//1.5, 100, 100), str(numObstacles), WHITE,"lucida console", 18, 1, 0,False,True)
numItemsText = Text((x+480, h-y//1.5, 100, 100), str(numItems), WHITE,"lucida console", 18, 1, 0,False,True)
itemRateText = Text((x+600, h-y//1.5, 100, 100), str(itemRate) + "%", WHITE,"lucida console", 18, 1, 0,False,True)
infectionRateText = Text((x+720, h-y//1.5, 100, 100), str(infectionRate) + "%", WHITE,"lucida console", 18, 1, 0, False, True)

# selection screen sprites
homeMenu = [
Text((0, 0, 400, 100), "Your own zombie apocalypse...", WHITE, "lucida console", 32, 1),
    
Image((x, h//2+y//2, 100, 100), gridImg, 1),
Image((x+120, h//2+y//2, 100, 100), humanImg, 1),
Image((x+240, h//2+y//2, 100, 100), zombImg, 1),
Image((x+360, h//2+y//2, 100, 100), houseImg, 1),
Image((x+480, h//2+y//2, 100, 100), foodImg, 1),
Image((x+600, h//2+y//2, 100, 100), itemRateImg, 1),
Image((x+720, h//2+y//2, 100, 100), infRateImg, 1),

#rect, text, colour, fontStyle, fontSize, layer=1, lineSpacing=30, wrap=False, centered=False

Text((x, h//2, 100, 100), "Grid size", WHITE,"lucida console", 18, 1),
Text((x+120, h//2, 100, 100), "Humans", WHITE,"lucida console", 18, 1),
Text((x+240, h//2, 100, 100), "Zombies", WHITE,"lucida console", 18, 1),
Text((x+360, h//2, 100, 100), "Obstacles", WHITE,"lucida console", 18, 1),
Text((x+480, h//2, 100, 100), "Items", WHITE,"lucida console", 18, 1),
Text((x+600, h//2, 100, 100), "Item spawn chance", WHITE,"lucida console", 18, 1, 20, True),
Text((x+720, h//2, 100, 100), "Infection chance", WHITE,"lucida console", 18, 1, 20, True),
]

homeMenuArrowsUp = [ # the up and down arrows for changing values
gridArrowUp,
humanArrowUp,
zombieArrowUp,
obsArrowUp,
foodArrowUp,
itemRateArrowUp,
infectRateArrowUp,
]
homeMenuArrowsDown = [
gridArrowDown,
humanArrowDown,
zombieArrowDown,
obsArrowDown,
foodArrowDown,
itemRateArrowDown,
infectRateArrowDown    
]
# the start button
newSimButton = Rect((0, SIZE[1]-100, SIZE[0], 100), GREEN, 1)
newSimButtonText = Text((0, SIZE[1]-100, SIZE[0], 100), "Start", WHITE, "lucida console", 60, 1, 0, False, True)

def startSim(): # start new simulation
    global openCells, numObstacles, numItems, numHumans, numZombies, humansAlive, zombiesAlive, STATE, gridSize, gridX, gridY, cellSize
    
    gridX, gridY = gridSize, gridSize
    cellSize = SIZE[1] // gridY
    openCells = [(x, y) for x in range (gridX) for y in range (gridY)]  # square coordinates unoccupied by obstacles
        
    humansAlive = numHumans
    zombiesAlive = numZombies
    for x in range (gridX):  # make grid
        grid.append([])
        for y in range (gridY):
            grid[x].append(Cell((x * cellSize + x * cellSpacing, y * cellSize + y * cellSpacing, cellSize, cellSize)))
        
    for i in range (numObstacles):
        obstacles.append(Obstacle())
        
    for i in range (numItems):
        items.append(Food())
        items.append(Medkit())
        items.append(Weapon())
        
    for i in range (numHumans):
        humans.append(Human())
    for i in range (numZombies):
        zombies.append(Zombie())
    STATE = 1

def saveSim(): # save summary
    outFile = open(saveFile, "w")
    
    if humansAlive > 0:
        outFile.write("Humanity still remains.\n")
    else:
        outFile.write("Humanity went extinct.\n")
    
    outFile.write(str(humansAlive) + " humans were able to survive.\n")
    outFile.write(str(numInfections) + " humans became zombies.\n")
    outFile.write(str(humanDeathsByStarve) + " humans starved to death.\n")
    outFile.write(str((numHumans-humansAlive-numInfections-humanDeathsByStarve))+" humans were killed by zombies.\n")
    outFile.write(str(zombiesAlive) + " zombies continue wreaking havoc.\n")
    outFile.write(str(zombieDeathsByStarve) + " zombies starved, hungry for brains.")
    outFile.close()
        

def resetSim():
    global grid, simSpeed, generation, humanDeathsByStarve, zombieDeathsByStarve, numInfections, paused
    paused = False
    simSpeed = 1
    humanDeathsByStarve = 0
    zombieDeathsByStarve = 0
    numInfections = 0
    speedText.update(str("Speed: " + str(simSpeed) + "x"))
    generation = 1
    grid.clear()
    humans.clear()
    zombies.clear()
    blood.clear()
    items.clear()
    obstacles.clear()
    
# Stats, deaths, humans alive, zombies alive and speed setting
x,y,w,h = frameRect = (SIZE[1], 0, SIZE[0]-SIZE[1], SIZE[1]//2 - 20)

legend = [ # legend ui
Image((x+25, y+40, 40, 40), humanImg, 1), # human
Image((x+25, y+80, 40, 40), zombImg, 1), # zombie
Image((x+25, 120, 40, 40), houseImg, 1), # building
Image((x+25, 160, 40, 40), treeImg, 1), # tree
Image((x+25, 200, 40, 40), foodImg, 1), # food
Image((x+25, 240, 40, 40), weapImg, 1), # weapon
Image((x+25, 280, 40, 40), healImg, 1), # weapon

Text((x, y, 10, 10), "Legend", WHITE, "lucida console", 26, 1), # legend title
Text((x+80, y+40, 10, 10), "Human", GREEN, "lucida console", 18, 1), # human text
Text((x+80, y+80, 10, 10), "Zombie", ENEMYRED, "lucida console", 18, 1), # zombie text
Text((x+80, y+120, 10, 10), "Building", NAVAJOWHITE, "lucida console", 18, 1), # building text
Text((x+80, y+160, 10, 10), "Forest", DARKGREEN, "lucida console", 18, 1), # tree text
Text((x+80, y+200, 10, 10), "Food item", WHITE, "lucida console", 18, 1), # food text
Text((x+80, y+240, 10, 10), "Weapon", WHITE, "lucida console", 18, 1), # weapon text
Text((x+80, y+280, 10, 10), "Medkit", WHITE, "lucida console", 18, 1) # medkit text
]

stats = [ # cannot  be changed during sim but can still be viewed

Text((x, h, 10, 10), "Stats", WHITE, "lucida console", 26, 1), # stats title
Text((x+25, h+30, 10, 10), "Number of obstacles: "+str(numObstacles), WHITE, "lucida console", 18, 1), # num obstacles
Text((x+25, h+60, 10, 10), "Infection rate: "+str(infectionRate)+"%", WHITE, "lucida console", 18, 1), # infection rate
Text((x+25, h+90, 10, 10), "Item spawn rate: "+str(itemRate)+"%", WHITE, "lucida console", 18, 1) # item rate
]

generationText = Text((x+25, h+120, 10, 10), "Generation "+str(generation), SEAGREEN, "lucida console", 18, 1) # generation
humansAliveText = Text((x+25, h+150, 10, 10), "Humans alive: "+str(numHumans-humansAlive)+"/"+str(numHumans), SEAGREEN, "lucida console", 18, 1) # humans alive
humansStarvedText = Text((x+25, h+180, 10, 10), "Humans starved: "+str(humanDeathsByStarve), SEAGREEN, "lucida console", 18, 1) # zombies alive
zombiesAliveText = Text((x+25, h+210, 10, 10), "Zombies alive: "+str(zombiesAlive)+"/"+str(numZombies), SEAGREEN, "lucida console", 18, 1) # zombies alive
zombiesStarvedText = Text((x+25, h+240, 10, 10), "Zombies starved: "+str(zombieDeathsByStarve), SEAGREEN, "lucida console", 18, 1) # zombies alive
infectionsText = Text((x+25, h+270, 10, 10), "Infections: "+str(numInfections), SEAGREEN, "lucida console", 18, 1) # infections
speedText = Text((x+25, h+300, 10, 10), "Speed: "+str(simSpeed)+"x", SEAGREEN, "lucida console", 26, 1) # speed label

speedUpArrow = Image((x+180, h+305, 30, 30), arrowUpImg, 1)
speedDownArrow = Image((x+220, h+305, 30, 30), arrowDownImg, 1)
pause = Image((x+260, h+305, 30, 30), pauseImg, 1)

endButton = Rect((x, SIZE[1]-25, w, 25), RED, 1)
endButtonText = Text(endButton.rect, "End", WHITE, "lucida console", 24, 1)


# summary screen
summary = []
returnHomeButton = Rect((0, SIZE[1]-100, SIZE[0], 100), GREEN, 1)
returnHomeText = Text((0, SIZE[1]-100, SIZE[0], 100), "Return", WHITE, "lucida console", 60, 1, 0, False, True)
def summaryScreen():
    x,y,w,h = 100,150,SIZE[0]-200, SIZE[1]-200
    summary.append(Text((0, 0, 10, 10), "Summary", WHITE, "lucida console", 60, 1)) # summary title
    if humansAlive > 0:
        summary.append(Text((x, y, 10, 10), "Humanity still remains.", WHITE, "lucida console", 30, 1))
    else:
        summary.append(Text((x, y, 10, 10), "Humanity went extinct.", WHITE, "lucida console", 30, 1))
        
    summary.append(Text((x, y+40, 10, 10), str(humansAlive) + " humans were able to survive.", WHITE, "lucida console", 30, 1))
    summary.append(Text((x, y+80, 10, 10), str(numInfections) + " humans became zombies.", WHITE, "lucida console", 30, 1))
    summary.append(Text((x, y+120, 10, 10), str(humanDeathsByStarve) + " humans starved to death.", WHITE, "lucida console", 30, 1))
    summary.append(Text((x, y+160, 10, 10), str((numHumans-humansAlive-numInfections-humanDeathsByStarve))+" humans were killed by zombies.", WHITE, "lucida console", 30, 1))
    summary.append(Text((x, y+200, 10, 10), str(zombiesAlive) + " zombies continue wreaking havoc.", WHITE, "lucida console", 30, 1))
    summary.append(Text((x, y+240, 10, 10), str(zombieDeathsByStarve) + " zombies starved, hungry for brains.", WHITE, "lucida console", 30, 1))
    summary.append(Text((x, y+280, 10, 10), str((numZombies+numInfections-zombieDeathsByStarve-zombiesAlive)) + " zombies were killed by humans.", WHITE, "lucida console", 30, 1))
    summary.append(Text((x, y+320, 10, 10), "Summary saved to "+saveFile, GREEN, "lucida console", 30, 1))
    
    summary.append(returnHomeButton)
    summary.append(returnHomeText)

numFrames = 60 // simSpeed
paused = False
run = True
while run:
    mouse = mousePos()
    screen.fill(BLACK)

    if STATE == 0:
        for e in homeMenu:
            e.draw()
            newSimButton.draw()
            newSimButtonText.draw()
            
        for u in homeMenuArrowsUp:
            if inRect(mouse, u.rect): # mouse collision
                u.sprite = arrowUpHoveredImg
            else:
                u.sprite = arrowUpImg
            u.draw()
        for d in homeMenuArrowsDown:
            if inRect(mouse, d.rect):
                d.sprite = arrowDownHoveredImg
            else:
                d.sprite = arrowDownImg
            d.draw()
        gridSizeText.draw()
        numHumansText.draw()
        numZombiesText.draw()
        numObstaclesText.draw()
        numItemsText.draw()
        itemRateText.draw()
        infectionRateText.draw()
        
        if inRect(mouse, newSimButton.rect): # mouse collision with start button
            newSimButton.colour = DARKGREEN
        else:
            newSimButton.colour = GREEN
        for e in event.get():
            if e.type == QUIT:
                run = False
            elif e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    run = False
            elif e.type == MOUSEBUTTONDOWN:
                increment = 1 # increment makes changing settings faster with right click
                if e.button == 3: # changing setting values
                    increment = 10
                if inRect(mouse, gridArrowUp.rect):
                    if gridSize+increment <= 120:
                        gridSize += increment
                    else:
                        gridSize = 120
                    gridSizeText.update(str(gridSize))
                    
                elif inRect(mouse, humanArrowUp.rect):
                    if numHumans+increment <= gridSize**2-numObstacles:
                        numHumans += increment
                    else:
                        numHumans = gridSize**2-numObstacles
                    numHumansText.update(str(numHumans))
                    
                elif inRect(mouse, zombieArrowUp.rect):
                    if numZombies+increment <= gridSize**2-numObstacles:
                        numZombies += increment
                    else:
                        numZombies = gridSize**2-numObstacles
                    numZombiesText.update(str(numZombies))
                    
                elif inRect(mouse, obsArrowUp.rect):
                    if numObstacles+increment <= gridSize**2-1:
                        numObstacles += increment
                    else:
                        numObstacles = gridSize**2-1
                    numObstaclesText.update(str(numObstacles))
                elif inRect(mouse, foodArrowUp.rect):
                    if numItems+increment <= gridSize**2-numObstacles:
                        numItems += increment
                    else:
                        numItems = gridSize**2-numObstacles
                    numItemsText.update(str(numItems))
                elif inRect(mouse, itemRateArrowUp.rect):
                    if itemRate+increment <= 100:
                        itemRate += increment
                    else:
                        itemRate = 100
                    itemRateText.update(str(itemRate)+"%")
                elif inRect(mouse, infectRateArrowUp.rect):
                    if infectionRate+increment <= 100:
                        infectionRate += increment
                    else:
                        infectionRate = 100
                    infectionRateText.update(str(infectionRate)+"%")
                    
                elif inRect(mouse, gridArrowDown.rect):
                    if gridSize-increment >= 1:
                        gridSize -= increment
                    else:
                        gridSize = 1
                    if numObstacles >= gridSize**2-1:
                        numObstacles = gridSize**2-1
                        numObstaclesText.update(str(numObstacles))
                    if numHumans >= gridSize**2-numObstacles:
                        numHumans = gridSize**2-numObstacles
                        numHumansText.update(str(numHumans))
                    if numZombies >= gridSize**2-numObstacles:
                        numZombies = gridSize**2-numObstacles
                        numZombiesText.update(str(numZombies))
                    if numItems >= gridSize**2-numObstacles:
                        numItems = gridSize**2-numObstacles
                        numItemsText.update(str(numItems))
                    gridSizeText.update(str(gridSize))
                elif inRect(mouse, humanArrowDown.rect):
                    if numHumans- increment >= 0:
                        numHumans -= increment
                    else:
                        numHumans = 0
                    numHumansText.update(str(numHumans))
                elif inRect(mouse, zombieArrowDown.rect):
                    if numZombies-increment >= 0:
                        numZombies -= increment
                    else:
                        numZombies = 0
                    numZombiesText.update(str(numZombies))
                elif inRect(mouse, obsArrowDown.rect):
                    if numObstacles-increment >= 0:
                        numObstacles -= increment
                    else:
                        numObstacles = 0
                    numObstaclesText.update(str(numObstacles)) 
                elif inRect(mouse, foodArrowDown.rect):
                    if numItems-increment >= 0:
                        numItems -= increment
                    else:
                        numItems = 0
                    numItemsText.update(str(numItems))   
                elif inRect(mouse, itemRateArrowDown.rect):
                    if itemRate-increment >= 0:
                        itemRate -= increment
                    else:
                        itemRate = 0
                    itemRateText.update(str(itemRate)+"%")
                elif inRect(mouse, infectRateArrowDown.rect):
                    if infectionRate-increment > 0:
                        infectionRate -= increment
                    else:
                        infectionRate = 0
                    infectionRateText.update(str(infectionRate)+"%")
                    
                elif inRect(mouse, newSimButton.rect):
                    startSim()

    elif STATE == 1: # simulation
        if simSpeed != 0 and not paused:
            if numFrames >= 60 // simSpeed:
                numFrames = 0
                
                spawnItem()
                    
                for h in humans:  # move humans and zombies first, then attack and draw based on new positions
                    h.move()
                for z in zombies:
                    z.move()
                        
                for h in humans:
                    h.attack()
                for z in zombies:
                    z.attack()
                generation += 1
                buzzSound.play()
                
        if inRect(mouse, speedDownArrow.rect): # speed setting ui collision
            speedDownArrow.sprite = arrowDownHoveredImg
        else:
            speedDownArrow.sprite = arrowDownImg
            
        if inRect(mouse, speedUpArrow.rect):
            speedUpArrow.sprite = arrowUpHoveredImg
        else:
            speedUpArrow.sprite = arrowUpImg
                        
        if inRect(mouse, pause.rect):
            pause.sprite = pauseImgHovered
        else:
            pause.sprite = pauseImg
    
        if inRect(mouse, endButton.rect):
            endButton.colour = DARKRED
        else:
            endButton.colour = RED
    
        for l in legend:
            l.draw()
        
        for s in stats:
            s.draw()
        
        speedUpArrow.draw()
        speedDownArrow.draw()
        pause.draw()
        endButton.draw()
        endButtonText.draw()
        
        generationText.update("Generation "+str(generation)) # update and draw simulation stats
        humansAliveText.update("Humans alive: "+str(humansAlive)+"/"+str(numHumans))
        humansStarvedText.update("Humans starved: "+str(humanDeathsByStarve))
        zombiesAliveText.update("Zombies alive: "+str(zombiesAlive)+"/"+str(numZombies))
        zombiesStarvedText.update("Zombies starved: "+str(zombieDeathsByStarve))
        infectionsText.update("Infections: "+str(numInfections))
        
        generationText.draw()
        humansAliveText.draw()
        humansStarvedText.draw()
        zombiesAliveText.draw()
        zombiesStarvedText.draw()
        infectionsText.draw()
        speedText.draw()
        
        for x in range (gridX):
            for y in range (gridY):  # redraw every cell
                grid[x][y].draw()
        for o in obstacles: # redraw everything else
            o.draw()
        for b in blood:
            b.draw()
        for i in items:
            i.draw()
    
        for h in humans:
            h.draw()
        for z in zombies:
            z.draw()            
        for e in event.get():
            if e.type == QUIT:
                run = False
            elif e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    run = False
            elif e.type == MOUSEBUTTONDOWN:
                
                if inRect(mouse, speedDownArrow.rect):
                    if paused:
                        paused = False
                    elif simSpeed > 1:
                        simSpeed //= 2
                elif inRect(mouse, speedUpArrow.rect) and simSpeed < 16:
                    if paused:
                        paused = False
                    else:
                        simSpeed *= 2
                elif inRect(mouse, pause.rect):
                    paused = not paused
                elif inRect(mouse, endButton.rect): # save and return
                    summaryScreen()
                    saveSim()
                    resetSim()
                    STATE = 2
                    break
                
                
                if simSpeed > 0 and not paused:
                    speedText.update("Speed: " + str(simSpeed) + "x")
                else:
                    speedText.update("Paused")
        numFrames += 1
    elif STATE == 2:
        
        for i in summary:
            i.draw()
        
        if inRect(mouse, returnHomeButton.rect):
            returnHomeButton.colour = DARKGREEN
        else:
            returnHomeButton.colour = GREEN
        
        for e in event.get(): # summary screen events
            if e.type == QUIT:
                run = False
            elif e.type == MOUSEBUTTONDOWN:
                if inRect(mouse, returnHomeButton.rect):
                    summary.clear()
                    STATE = 0
            elif e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    run = False
                    
        
    display.update()
    clock.tick(60)
quit()
