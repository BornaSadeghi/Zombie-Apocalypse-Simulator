from pygame import *
init()

SIZE = 1000,700
screen = display.set_mode(SIZE)

clock = time.Clock()

class Rect:
    def __init__(self, rect, colour, layer=1, width=0):
        self.rect = rect
        self.colour = colour
        self.width = width
        self.layer = layer
    def draw(self):
        draw.rect(screen, self.colour, self.rect, self.width)

# takes in rect (x,y,w,h), text (string), colour (r,g,b), font (string), font size (int), layer (int)
class Text:
    def __init__(self, rect, text, colour, fontStyle, fontSize, layer=1, lineSpacing=30, wrap=False, centered=False):
        self.textColour = colour
        self.lineSpacing = lineSpacing
        self.wrap = wrap
        self.layer = layer
        self.fontStyle = fontStyle
        self.fontSize = fontSize
        f = font.SysFont(fontStyle, fontSize) # initialize font
        
        if wrap: # if wrap, get a list of lines from the text wrapping function
            self.text = wrapText(text, fontStyle, fontSize, rect, lineSpacing)
        else: # otherwise put the one line in a list
            self.text = [text]
        
        # renders the list of lines
        self.textImg= [f.render (line,1, colour) for line in self.text]
            
        if centered: # centers the text in the rect
            self.rect = self.textImg[0].get_rect(center=(rect[0]+rect[2]//2, rect[1]+rect[3]//2))
        else:
            self.rect = rect
    def update (self, newText=""):
        if newText != "":
            if self.wrap:
                self.text = wrapText(newText, self.fontStyle, self.fontSize, self.rect, self.lineSpacing)
            else:
                self.text = [newText]
            
        f = font.SysFont(self.fontStyle, self.fontSize) # initialize font
        self.textImg= [f.render (line,1, self.textColour) for line in self.text]  
    def draw(self):
        x,y,w,h = self.rect
        i = 0
        for img in self.textImg: # blits every line
            screen.blit(img, (x,y+i*self.lineSpacing,w,h))
            i += 1
        
class Image:
    def __init__(self, rect, sprite, layer=1):
        self.rect = rect
        self.sprite = sprite
        self.layer = layer
    def draw(self):
        img = transform.scale(self.sprite, (self.rect[2], self.rect[3]))
        screen.blit(img, self.rect)

class Line:
    def __init__(self, start, end, colour=(255,255,255), width=1):
        self.start = start
        self.end = end
        self.colour = colour
        self.width = width
    def draw(self):
        draw.line(screen, self.colour, self.start, self.end, self.width)

# not sure if this is needed
class Button:
    def __init__(self, rect):
        self.rect = rect
        self.hovered = False

def mousePos():
    return mouse.get_pos()

def mouseRel():
    return mouse.get_rel()

# return true if a point is within a rectangle (x,y,w,h)
def inRect(pos, rect):
    x, y = pos
    rX, rY, rW, rH = rect
    
    if x >= rX and x <= rX + rW:
        if y >= rY and y <= rY + rH:
            return True
    return False

# returns list of strings
# takes in text (string), font (string), font size (int), rect (4 ints: x,y,w,h), byWord (boolean), line spacing (int)
def wrapText (text, fontStyle, fontSize, rect, byWord=True, lineSpacing=30):
    fontStyle = font.SysFont(fontStyle, fontSize)
    charW, charH = fontStyle.size("a")
    
    lines = []
    rectW, rectH = rect[2], rect[3]
    numLetters = rectW // charW # chars per line
    
    if charH*2-lineSpacing != 0:
        numLines = rectH // charH # num of lines that fit in the height
    else:
        numLines = 1
        print("division by 0")
    lastSpace = 0 # index of space closest to end
    for i in range (numLines):
        if byWord:
            line = text[0:numLetters]
            
            lastSpace = line.rfind(" ")
            if lastSpace == -1:
                lastSpace = len(line)
                
            wrapped = line[0:lastSpace+1]
            text = text[lastSpace+1:]
        else:
            wrapped = text[i*numLetters:(i+1)*numLetters]
        lines.append(wrapped)
    return lines