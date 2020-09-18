# Importing necesary modules #
import pygame,sys,pickle,json
from pygame.locals import *
from platform import release
from os import environ,remove
from os.path import isfile
from math import ceil
from random import choice
from ctypes import windll; windll.user32.SetProcessDPIAware()
from requests import get
from datetime import datetime,timedelta
from pytz import timezone

# Objects #
class MC:
    __slots__ = ('name','value','category','currency','count','aliases')
    def __init__(self,name,value,category,currency="British Pound Sterling",aliases=0):
        self.name,self.value,self.category,self.currency,self.count,self.aliases = name,value,category,currency,0,aliases
class LineOfText(pygame.sprite.Sprite):
    __slots__ = ('game','text','x','y','size','font','color','static','textid','image','rect','istouched','ishit','align')
    def __init__(self,game,text,x,y,size,font,color,static=0,textid="0",align="center"):
        self.text,self.x,self.y,self.size,self.color,self.static,self.textid,self.istouched,self.ishit,self.align = text,int(x),int(y),size,color,static,textid,0,0,align
        self.font = game.filepath+font+".ttf"
        pygame.sprite.Sprite.__init__(self,game.texts)
        self.image = pygame.font.Font(self.font,self.size).render(self.text,True,color)
        self.refresh()
    def touch(self): self.istouched = 1; self.image = pygame.font.Font(self.font,int(self.size*1.5)).render(self.text,True,(255,255,0)); self.refresh()
    def untouch(self): self.istouched = 0; self.image = pygame.font.Font(self.font,int(self.size)).render(self.text,True,self.color); self.refresh()
    def update(self, newtext): self.text = newtext; self.image = pygame.font.Font(self.font,self.size).render(self.text,True,self.color); self.refresh()
    def refresh(self):
        if self.align == "center": self.rect = self.image.get_rect(**{"center":(int(self.x),int(self.y))})
class Image(pygame.sprite.Sprite):
    __slots__ = ('image','x','y','rect')
    def __init__(self,image,x,y):
        self.image,self.x,self.y = image,x,y
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)

def exchange(base):
    return get("https://api.ratesapi.io/api/latest",params={'base':base,'symbols':'GBP','rtype':'fpy'}).json().get('rates',{}).get('GBP',None)
def crypto(abr):
    return float(get('https://api.coinbase.com/v2/exchange-rates?currency='+abr).json()['data']['rates']['GBP'])

# Program #
class Program:
    def __init__(self):
        currenttime = datetime.now(tz=timezone('Africa/Algiers')).isoformat()
        try: open("config.json","x")
        except FileExistsError: pass
        with open("config.json", "r+") as config:
            writtento = config.readline()
            if not writtento:
                self.configdict = {"time":currenttime,"display":"english","customcash":[],"cache":True,"displaycurrency":"British Pound Sterling","currencies":{}}
                json.dump(self.configdict,config)
            else:
                config.seek(0);self.configdict = json.load(config)
            refreshtime = datetime.fromisoformat(self.configdict["time"]).replace(hour=8,minute=10,second=0,microsecond=0)
            if refreshtime < datetime.fromisoformat(self.configdict["time"]): refreshtime += timedelta(days=1)
            if self.configdict["currencies"] == {} or refreshtime < datetime.fromisoformat(currenttime):
                self.configdict["time"] = currenttime
                self.configdict["currencies"] = {"United States Dollars":exchange('USD'),"Euro":exchange('EUR'),"Yen":exchange('JPY'),"Australian Dollars":exchange('AUD'),
                    "Canadian Dollars":exchange('CAD'),"Swiss Francs":exchange('CHF'),"Chinese Renminbi":exchange('CNY'),"New Zealand Dollars":exchange('NZD'),"Swedish Krona":exchange('SEK'),
                    "Indian Rupees":exchange('INR'),
                    "Bitcoin":crypto('BTC'),"Ethereum":crypto('ETH'),"Bitcoin Cash":crypto('BCH'),"Litecoin":crypto('LTC'),"XRP":crypto('XRP')}
        with open("config.json", "r+") as config: json.dump(self.configdict,config)
        print(self.configdict["currencies"])

        objectcacheerror = 0
        if self.configdict["cache"]:
            try: open("objectcache","x"); objectcacheerror = 1
            except FileExistsError: pass
            with open("objectcache","r") as objectcache:
                try: 
                    if objectcache.read() == "": objectcacheerror = 1
                except UnicodeDecodeError: objectcacheerror = 1
        self.cash = []
        if objectcacheerror == 0:
            with open('objectcache','rb') as objectcache: self.cash = pickle.load(objectcache)

        self.currencies = {"British Pound Sterling":1}
        self.reset()
        try: 
            open("savedata.txt","x")
            with open("savedata.txt","w") as savedata:
                for c in self.cash: savedata.write("0\n")
        except FileExistsError:
            lines = []
            with open("savedata.txt","r") as savedata:
                for line in savedata: lines.append(line.strip())
            iteration = 0
            for savedata in lines:
                try: savedata = int(savedata)
                except ValueError:
                    for c in self.cash: c.count = 0
                    break
                iteration += 1
                self.cash[iteration-1].count = savedata

        if release() == '10':
            environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (1,30)
            self.window = pygame.display.set_mode((monitor.current_w-2,monitor.current_h-33), pygame.RESIZABLE)
        else:
            environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (8,30)
            self.window = pygame.display.set_mode((monitor.current_w-16,monitor.current_h-40), pygame.RESIZABLE)

        pygame.display.set_caption("Advanced Piggybank Counter")
        self.window_w,self.window_h = pygame.display.get_surface().get_size()
        self.clock = pygame.time.Clock()
        self.texts = pygame.sprite.Group()
        self.menu,self.display,self.key,self.inputboxtimer,self.down,self.cachetoggled,self.image = "home",None,"",0,0,1,False
        self.titles = ["Cameron Johnston's Piggy Bank Counter","Cameron's Advanced Piggy Bank Counter","Burnside Piggy Bank Counter",
            "Cameron Johnston's Piggy Bank Counter","Cameron's Advanced Piggy Bank Counter","Burnside Piggy Bank Counter","Burnside is cool just saying"]

        self.filepath = ""
        if getattr(sys, 'frozen', False):
            self.filepath = sys._MEIPASS+"\\"
        favicon = pygame.image.load(self.filepath+'favicon.png')
        pygame.display.set_icon(favicon)

        pygame.mixer.music.load(self.filepath+"coin.mp3")
        pygame.mixer.music.play(1)
        
    def draw(self):
        self.window.fill((90,14,24))
        if self.image: self.window.blit(self.image.image,(self.image.rect.x,self.image.rect.y))
        for text in self.texts: self.window.blit(text.image,(text.rect.x,text.rect.y))
        pygame.display.update()

    def ask(self,question,information,asktype,other="",image=False):
        self.display = self.menu
        self.texts = pygame.sprite.Group()
        LineOfText(self,choice(self.titles),self.window_w/2,self.window_h-24,48,"Merkur",(255,197,129),1)
        LineOfText(self,question,self.window_w/2,24,32,"Impact",(255,255,255),1)
        LineOfText(self,information,self.window_w/2,48,24,"Arial",(196,196,196),1)
        if image: self.image = Image(pygame.image.load(image[0]).convert_alpha(),image[1],image[2])
        else: self.image = False

        if asktype == "selection":
            for iterate0,rowofanswers in enumerate(other):
                for iterate1,groupofanswers in enumerate(rowofanswers):
                    for iterate2,answer in enumerate(groupofanswers):
                        x = self.window_w/(len(rowofanswers)+1)*(iterate1+1)
                        y = self.window_h/(len(other)+1)*(iterate0+1)-18*(len(groupofanswers)/2-iterate2)
                        if iterate2 == 0:
                            LineOfText(self,answer[0],x,y,12,"Impact",(255,255,255),1,answer[1])
                        else:
                            LineOfText(self,answer[0],x,y,12,"Arial",(255,255,255),textid=answer[1])
        elif asktype == "input":
            self.userinput,self.key = "",""
            LineOfText(self,other,self.window_w/2,self.window_h-60,14,"Arial",(255,255,255),1)
            LineOfText(self,"_",self.window_w/2,self.window_h/2,32,"Impact",(255,255,255),textid="userinput")
            LineOfText(self,"Press [ENTER] to confirm your choice and [ESC] to cancel",self.window_w/2,72,24,"Arial",(196,196,196),1)
        
    def run(self):
        self.clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit();sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: self.down = 1
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1: self.down = 0
            elif event.type == pygame.KEYDOWN: self.key = event.key

        for text in self.texts:
            if text.rect.collidepoint(pygame.mouse.get_pos()) and text.static == 0: text.touch()
            elif not text.rect.collidepoint(pygame.mouse.get_pos()) and text.static == 0 and text.istouched == 1 and text.ishit == 0: text.untouch()
            if text.istouched == 1 and self.down == 1: text.ishit = 1
            elif self.down == 0 and text.ishit == 1:
                text.ishit = 0
                print(text.textid)
                if text.textid == "setting0":
                    req = list(self.configdict['currencies'].keys())
                    req.append('British Pound Sterling')
                    currentlocation = req.index(self.configdict['displaycurrency'])
                    if currentlocation == len(self.configdict['currencies']): self.configdict['displaycurrency'] = req[0]
                    else: self.configdict['displaycurrency'] = req[currentlocation+1]
                    with open("config.json","w") as config: json.dump(self.configdict,config)
                    text.update(self.configdict['displaycurrency'])
                elif text.textid.startswith("cash"): self.menu = text.textid
                elif text.textid == "setting1":
                    for c in self.cash: c.count = 0
                    self.display = None
                elif text.textid == "setting2":
                    with open("savedata.txt","w+") as savedata:
                        for cash in self.cash: savedata.write(str(cash.count)+"\n")
                elif text.textid == "setting3": self.menu = "setting3"
                elif text.textid == "setting4": self.menu = "setting4"
                elif text.textid == "setting5": 
                    self.configdict["cache"],self.cachetoggled = not self.configdict["cache"],1
                    with open("config.json","w") as config: json.dump(self.configdict,config)

            if text.textid == "total" and self.lastdisplaycurrency != self.configdict['displaycurrency']:
                self.lastdisplaycurrency = self.configdict['displaycurrency']
                counts = [c.count for c in self.cash]
                self.cash = []
                if self.configdict["cache"]:
                    with open('objectcache','rb') as objectcache: self.cash = pickle.load(objectcache)
                self.reset()
                for iterate,c in enumerate(counts): self.cash[iterate].count = c
                total = 0
                for c in self.cash: total += c.value*c.count
                text.update("Total: "+str(round(total,2)))
            elif text.textid == "userinput":
                self.inputboxtimer += 1
                if self.inputboxtimer == 60:
                    if text.text[len(text.text)-1] == "_": text.update(self.userinput+"  ")
                    else: text.update(self.userinput+"_")
                    self.inputboxtimer = 0
                elif text.text != self.userinput: text.update(self.userinput+text.text[len(text.text)-1])
            elif text.textid == "setting5" and self.cachetoggled == 1:
                if self.configdict["cache"]: text.color = (0,255,0)
                else: text.color = (255,0,0);remove("objectcache")
                text.update("Toggle cache");self.cachetoggled = 0
        
        if self.menu.startswith("cash") and self.key != "":
            if self.key >= 48 and self.key <= 57:
                self.userinput += str(self.key-48)
            elif self.key == pygame.K_BACKSPACE:
                self.userinput = self.userinput[0:-1]
            elif self.key == pygame.K_RETURN and self.userinput != "":
                self.cash[int(self.menu[4:])].count = float(self.userinput)
                self.menu = "home"
            elif self.key == pygame.K_ESCAPE:
                self.menu = "home"
            elif self.key == pygame.K_PERIOD and not "." in self.userinput and len(self.userinput) >= 1:
                self.userinput += "."
            self.key = ""

        if self.display != self.menu:
            if self.menu == "home":
                self.lastdisplaycurrency = 0
                if self.configdict["display"] == "all": tempcash0 = self.cash
                elif self.configdict["display"] == "english": tempcash0 = [x for x in self.cash if x.category in ["American coins","American notes","British coins","British notes","European coins","European notes","Cryptocurrencies","Australian coins","Australian notes"]]
                elif self.configdict["display"] == "american": tempcash0 = [x for x in self.cash if x.category in ["American coins","American notes"]]
                elif self.configdict["display"] == "british": tempcash0 = [x for x in self.cash if x.category in ["British coins","British notes"]]
                elif self.configdict["display"] == "european": tempcash0 = [x for x in self.cash if x.category in ["European coins","European notes"]]
                elif self.configdict["display"] == "australian": tempcash0 = [x for x in self.cash if x.category in ["Australian coins","Australian notes"]]
                elif self.configdict["display"] == "chinese": tempcash0 = [x for x in self.cash if x.category in ["Chinese coins","Chinese notes"]]
                elif self.configdict["display"] == "coins": tempcash0 = [x for x in self.cash if x.category in ["American coins","British coins","European coins","Japanese coins","Australian coins"]]
                elif self.configdict["display"] == "notes": tempcash0 = [x for x in self.cash if x.category in ["American notes","British notes","European notes","Japanese notes","Australian notes"]]
                elif self.configdict["display"] == "dollars": tempcash0 = [x for x in self.cash if x.category in ["American coins","American notes","Australian coins","Australian notes"]]
                else: tempcash0 = [x for x in self.cash if x.category in self.configdict["display"]]
                total,lastcategory,tempcash1 = 0,0,[]
                for iterate,c in enumerate(self.cash):
                    if c in tempcash0:
                        if lastcategory != c.category:
                            lastcategory = c.category
                            tempcash1.append([[c.category,"category"]])
                        tempcash1[len(tempcash1)-1].append([c.name+" : "+str(c.count),"cash"+str(iterate)])
                        total += c.value*c.count
                tempcash1 = [tempcash1]
                if len(tempcash1[0]) >= 4: tempcash1 = [tempcash1[0][:len(tempcash1[0])-round(len(tempcash1[0])/2)],tempcash1[0][-round(len(tempcash1[0])/2):]]
                tempcash1.append([[["Total: ","total"],[self.configdict["displaycurrency"],"setting0"]],
                [["Settings","category"],["Reset all to 0","setting1"],["Save data","setting2"],["Manage currencies","setting3"],["Manage custom cash items","setting4"],["Toggle cache","setting5"]]])
                self.ask("Choose a cash item from the list below:","If missing one, display or add it in the settings. Hover over and left click it to select.","selection",tempcash1)

            elif self.menu.startswith("cash"):
                req = self.cash[int(self.menu[4:])]
                if isfile(self.filepath+'images\\'+req.category+'\\'+req.name+'.png'): image = [self.filepath+'images\\'+req.category+'\\'+req.name+'.png',150,self.window_h/2]
                else: image = False
                information = " is a currency worth it's value in {} with a {} value of ~{}. You have counted {} so far!".format(req.currency,self.configdict['displaycurrency'],str(round(req.value,2)),str(req.count))
                if req.aliases == 0: information = "The {}{}".format(req.name,information)
                else: information = "The {}, also known as {},{}".format(req.name,req.aliases,information)
                self.ask("What would you like to change it's count to?","(how many of this to add to the total)","input",information,image=image)
            
            elif self.menu == "setting3":
                selections = [[[[currency,"category"],["Change value","value"+str(iterate)],["Delete","delete"+str(iterate)]] for iterate,currency in enumerate(self.configdict["currencies"].keys())]]
                selections = [selections[0][:len(selections[0])-round(len(selections[0])/2)],selections[0][-round(len(selections[0])/2):],
                    [[["Which to display","category"],[self.configdict["display"] if type(self.configdict["display"]) is str else "custom","display"]]]]
                if type(self.configdict["display"]) is list:
                    for b in selections[0:2]:
                        for a in b: a.append(["Show","display"+a[1][1][5:]])
                self.ask("Choose an option from the list below:","","selection",selections)

    def reset(self):
        if self.cash == []:
            self.cash = [MC("One pence coin (1p)",0.01,"British coins",aliases="a penny"),
                MC("Two pence coin (2p)",0.02,"British coins"),
                MC("Five pence coin (5p)",0.05,"British coins"),
                MC("Ten pence coin (10p)",0.1,"British coins"),
                MC("Twenty pence coin (20p)",0.2,"British coins"),
                MC("Fifty pence coin (50p)",0.5,"British coins"),
                MC("One pound coin (£1)",1,"British coins",aliases="a quid"),
                MC("Two pound coin (£2)",2,"British coins"),
                MC("Five pound note (£5)",5,"British notes",aliases="a fiver"),
                MC("Ten pound note (£10)",10,"British notes",aliases="a tenner"),
                MC("Twenty pound note (£20)",20,"British notes",aliases="a score"),
                MC("Fifty pound note (£50)",50,"British notes",aliases="a bullseye"),
                MC("One cent coin (1¢)",0.01,"American coins","United States Dollars","a penny"),
                MC("Five cent coin (5¢)",0.05,"American coins","United States Dollars","a nickel"),
                MC("Ten cent coin (10¢)",0.1,"American coins","United States Dollars","a dime"),
                MC("Twenty five cent coin (25¢)",0.25,"American coins","United States Dollars","a quarter"),
                MC("Fifty cent coin (50¢)",0.5,"American coins","United States Dollars","a half-dollar"),
                MC("Dollar coin ($1)",1,"American coins","United States Dollars","a golden dollar"),
                MC("One dollar bill ($1)",1,"American notes","United States Dollars","a dollar note/buck"),
                MC("Two dollar bill ($2)",2,"American notes","United States Dollars","a deuce"),
                MC("Five dollar bill ($5)",5,"American notes","United States Dollars","a fiver"),
                MC("Ten dollar bill ($10)",10,"American notes","United States Dollars","a Hamilton"),
                MC("Twenty dollar bill ($20)",20,"American notes","United States Dollars","a dub/Jackson"),
                MC("Fifty dollar bill ($50)",50,"American notes","United States Dollars"),
                MC("One hundred dollar bill ($100)",100,"American notes","United States Dollars","a c-note/Benjamin"),
                MC("One thousand dollar bill ($1000)",1000,"American notes","United States Dollars","a grand/large"),
                MC("One cent coin (1¢)",0.01,"European coins","Euro"),
                MC("Two cent coin (2¢)",0.02,"European coins","Euro"),
                MC("Five cent coin (5¢)",0.05,"European coins","Euro"),
                MC("Ten cent coin (10¢)",0.1,"European coins","Euro"),
                MC("Twenty cent coin (20¢)",0.2,"European coins","Euro"),
                MC("Fifty cent coin (50¢)",0.5,"European coins","Euro"),
                MC("One euro coin (€1)",1,"European coins","Euro"),
                MC("Two euro coin (€2)",2,"European coins","Euro"),
                MC("Five euro note (€5)",5,"European notes","Euro"),
                MC("Ten euro note (€10)",10,"European notes","Euro"),
                MC("Twenty euro note (€20)",20,"European notes","Euro"),
                MC("Fifty euro note (€50)",50,"European notes","Euro"),
                MC("One hundred euro note (€100)",100,"European notes","Euro"),
                MC("Two hundred euro note (€200)",200,"European notes","Euro"),
                MC("Five hundred euro note (€500)",500,"European notes","Euro"),
                MC("One yen coin (¥1)",1,"Japanese coins","Yen"),
                MC("Five yen coin (¥5)",5,"Japanese coins","Yen"),
                MC("Ten yen coin (¥10)",10,"Japanese coins","Yen"),
                MC("Fifty yen coin (¥50)",50,"Japanese coins","Yen"),
                MC("One hundred yen coin (¥100)",100,"Japanese coins","Yen"),
                MC("Five hundred yen coin (¥500)",500,"Japanese coins","Yen"),
                MC("One thousand yen note (¥1000)",1000,"Japanese notes","Yen"),
                MC("Two thousand yen note (¥2000)",2000,"Japanese notes","Yen"),
                MC("Five thousand yen note (¥5000)",5000,"Japanese notes","Yen"),
                MC("Ten thousand yen note (¥10000)",10000,"Japanese notes","Yen"),
                MC("Five cent coin (5¢)",0.05,"Australian coins","Australian Dollars"),
                MC("Ten cent coin (10¢)",0.1,"Australian coins","Australian Dollars"),
                MC("Twenty cent coin (20¢)",0.2,"Australian coins","Australian Dollars"),
                MC("Fifty cent coin (50¢)",0.5,"Australian coins","Australian Dollars"),
                MC("One dollar coin ($1)",1,"Australian coins","Australian Dollars"),
                MC("Two dollar coin ($2)",2,"Australian coins","Australian Dollars"),
                MC("One dollar bill ($1)",1,"Australian notes","Australian Dollars"),
                MC("Two dollar bill ($2)",2,"Australian notes","Australian Dollars"),
                MC("Five dollar bill ($5)",5,"Australian notes","Australian Dollars"),
                MC("Ten dollar bill ($10)",10,"Australian notes","Australian Dollars"),
                MC("Twenty dollar bill ($20)",20,"Australian notes","Australian Dollars"),
                MC("Fifty dollar bill ($50)",50,"Australian notes","Australian Dollars"),
                MC("Hundred dollar bill ($100)",100,"Australian notes","Australian Dollars"),
                MC("Five cent coin (5¢)",0.05,"Canadian coins","Canadian Dollars"),
                MC("Ten cent coin (10¢)",0.1,"Canadian coins","Canadian Dollars"),
                MC("Twenty cent coin (25¢)",0.2,"Canadian coins","Canadian Dollars"),
                MC("Fifty cent coin (50¢)",0.5,"Canadian coins","Canadian Dollars"),
                MC("One dollar coin ($1)",1,"Canadian coins","Canadian Dollars"),
                MC("Two dollar coin ($1)",2,"Canadian coins","Canadian Dollars"),
                MC("Five dollar bill ($5)",5,"Canadian notes","Canadian Dollars"),
                MC("Ten dollar bill ($10)",10,"Canadian notes","Canadian Dollars"),
                MC("Twenty dollar bill ($20)",20,"Canadian notes","Canadian Dollars"),
                MC("Fifty dollar bill ($50)",50,"Canadian notes","Canadian Dollars"),
                MC("Five cent coin (5¢)",0.05,"Swiss coins","Swiss Francs"),
                MC("Ten cent coin (10¢)",0.1,"Swiss coins","Swiss Francs"),
                MC("Twenty cent coin (20¢)",0.2,"Swiss coins","Swiss Francs"),
                MC("Fifty cent coin (50¢)",0.5,"Swiss coins","Swiss Francs"),
                MC("One franc coin (1₣)",1,"Swiss coins","Swiss Francs"),
                MC("Two franc coin (2₣)",2,"Swiss coins","Swiss Francs"),
                MC("Five franc coin (5₣)",5,"Swiss coins","Swiss Francs"),
                MC("One fen coin (¥0.01)",0.01,"Chinese coins","Chinese Renminbi","a lot of other things"),
                MC("Two fen coin (¥0.02)",0.02,"Chinese coins","Chinese Renminbi","a lot of other things"),
                MC("Five fen coin (¥0.05)",0.05,"Chinese coins","Chinese Renminbi","a lot of other things"),
                MC("One jiao coin (¥0.1)",0.1,"Chinese coins","Chinese Renminbi","a lot of other things"),
                MC("Two jiao coin (¥0.2)",0.2,"Chinese coins","Chinese Renminbi","a lot of other things"),
                MC("Five jiao coin (¥0.5)",0.5,"Chinese coins","Chinese Renminbi","a lot of other things"),
                MC("One yuan coin (¥1)",1,"Chinese coins","Chinese Renminbi","a lot of other things"),
                MC("One yuan note (¥1)",1,"Chinese notes","Chinese Renminbi","a lot of other things"),
                MC("Five yuan note (¥5)",5,"Chinese notes","Chinese Renminbi","a lot of other things"),
                MC("Ten yuan note (¥10)",10,"Chinese notes","Chinese Renminbi","a lot of other things"),
                MC("Twenty yuan note (¥20)",20,"Chinese notes","Chinese Renminbi","a lot of other things"),
                MC("Fifty yuan note (¥50)",50,"Chinese notes","Chinese Renminbi","a lot of other things"),
                MC("One hundred yuan note (¥100)",100,"Chinese notes","Chinese Renminbi","a lot of other things"),
                MC("Ten cent coin (10¢)",0.1,"Kiwi coins","New Zealand Dollars"),
                MC("Twenty cent coin (20¢)",0.2,"Kiwi coins","New Zealand Dollars"),
                MC("Fifty cent coin (50¢)",0.5,"Kiwi coins","New Zealand Dollars"),
                MC("One franc coin ($1)",1,"Kiwi coins","New Zealand Dollars"),
                MC("Two franc coin ($2)",2,"Kiwi coins","New Zealand Dollars"),
                MC("One krona coin (1kr)",1,"Swedish coins","Swedish Krona"),
                MC("Two krona coin (2kr)",2,"Swedish coins","Swedish Krona"),
                MC("Five krona coin (5kr)",5,"Swedish coins","Swedish Krona"),
                MC("Ten krona coin (10kr)",10,"Swedish coins","Swedish Krona"),
                MC("Twenty krona note (20kr)",20,"Swedish notes","Swedish Krona"),
                MC("Fifty krona note (50kr)",50,"Swedish notes","Swedish Krona"),
                MC("One hundred krona note (100kr)",100,"Swedish notes","Swedish Krona"),
                MC("Two hundred krona note (200kr)",200,"Swedish notes","Swedish Krona"),
                MC("Five hundred krona note (500kr)",500,"Swedish notes","Swedish Krona"),
                MC("One thousand krona note (1000kr)",1000,"Swedish notes","Swedish Krona"),
                MC("Ten paisa coin (10p‎)",0.1,"Indian coins","Indian Rupees"),
                MC("Twenty paisa coin (20p‎)",0.2,"Indian coins","Indian Rupees"),
                MC("Twenty five paisa coin (25p‎)",0.25,"Indian coins","Indian Rupees"),
                MC("Fifty paisa coin (50p‎)",0.5,"Indian coins","Indian Rupees"),
                MC("One rupee coin (1Rs‎)",1,"Indian coins","Indian Rupees"),
                MC("Two rupee coin (2‎Rs)",2,"Indian coins","Indian Rupees"),
                MC("Five rupee coin (5‎Rs)",5,"Indian coins","Indian Rupees"),
                MC("Five rupee note (5‎Rs)",5,"Indian notes","Indian rupees"),
                MC("Ten rupee note (‎10Rs)",10,"Indian notes","Indian rupees"),
                MC("Twenty rupee note (‎20Rs)",20,"Indian notes","Indian rupees"),
                MC("Fifty rupee note (‎50Rs)",50,"Indian notes","Indian rupees"),
                MC("One hundred rupee note (‎100Rs)",100,"Indian notes","Indian rupees"),
                MC("Five hundred rupee note (‎500Rs)",500,"Indian notes","Indian rupees"),
                MC("One thousand rupee note (1000‎Rs)",1000,"Indian notes","Indian rupees"),
                MC("Bank balance / cheque",1,"Cryptocurrencies"),
                MC("Bitcoin",1,"Cryptocurrencies","Bitcoin"),
                MC("Ethereum",1,"Cryptocurrencies","Ethereum"),
                MC("Bitcoin Cash",1,"Cryptocurrencies","Bitcoin Cash"),
                MC("Litecoin",1,"Cryptocurrencies","Litecoin"),
                MC("XRP",1,"Cryptocurrencies","XRP")]
            if self.configdict["cache"]: 
                with open('objectcache', 'wb') as objectcache: pickle.dump(self.cash, objectcache)

        for c in self.configdict["customcash"]: self.cash.append(MC(c[0],c[1],c[2],c[3],c[4]))
        self.cash.sort(key=lambda x: x.category)
        for c in self.cash:
            if c.currency in self.configdict["currencies"]: c.value *= self.configdict["currencies"][c.currency]
            if self.configdict["displaycurrency"] != "British Pound Sterling": c.value /= self.configdict["currencies"][self.configdict["displaycurrency"]]

pygame.init()
monitor = pygame.display.Info()
g = Program()
while True:
    g.draw();g.run()