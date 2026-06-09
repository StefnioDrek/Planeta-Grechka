import pygame
import sys
import random
import math
import os
import json
from datetime import datetime

pygame.init()
WIDTH, HEIGHT = 1600, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Планета Гречка - Приключения Боба")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 26)
big_font = pygame.font.Font(None, 48)
small_font = pygame.font.Font(None, 20)
tiny_font = pygame.font.Font(None, 16)

WHITE = (255,255,255); BLACK = (0,0,0); BROWN = (101,67,33); GREEN = (34,139,34)
DARK_GREEN = (20,80,20); RED = (220,50,50); BLUE = (70,130,180); PURPLE = (147,112,219)
GRAY = (128,128,128); YELLOW = (255,255,0); ORANGE = (255,165,0); PINK = (255,192,203)
SKIN = (255,218,185); BG_COLOR = (255,248,220); DARK_BG = (50,50,50); GOLD = (255,215,0)
CYAN = (0,255,255); MAGENTA = (255,0,255); TEAL = (0,180,180); LIME = (180,255,180)

text_cache = {}
def get_text(text, f, color):
    key = (text, id(f), color)
    if key not in text_cache: text_cache[key] = f.render(text, True, color)
    return text_cache[key]

SAVE_FILE = "bob_save.json"

def save_game(bob, loc_name, story):
    data = {"money":bob.money,"energy":bob.energy,"max_energy":bob.max_energy,"debt":bob.debt,
            "debt_paid":bob.debt_paid,"weapon":bob.weapon,"weapon_damage":bob.weapon_damage,
            "weapon_name":bob.weapon_name,"armor":bob.armor,"speed_boost":bob.speed_boost,
            "monsters_defeated":bob.monsters_defeated,"location":loc_name,
            "weapon_durability":bob.weapon_durability,"weapon_max_durability":bob.weapon_max_durability,
            "weapon_range":bob.weapon_range,"ammo":bob.ammo,"ammo_type":bob.ammo_type,
            "needs_ammo":bob.needs_ammo,
            "story_index":story.mi,"story_triggers":list(story.st),
            "undertale":story.undertale_found,"achievements":[a.unlocked for a in achievements.achievements],
            "night":night_system.is_night}
    with open(SAVE_FILE,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)
    return True

def load_game():
    try:
        with open(SAVE_FILE,'r',encoding='utf-8') as f: return json.load(f)
    except: return None

class Particle:
    def __init__(self,x,y,color,vel,life=30,size=3):
        self.x=x; self.y=y; self.color=color; self.vx,self.vy=vel; self.life=life; self.max_life=life; self.size=size

class ParticleSystem:
    def __init__(self): self.particles=[]; self.max=200
    def emit(self,x,y,color,n=10,vr=(-3,3),life=30,size=3):
        for _ in range(min(n,self.max-len(self.particles))):
            self.particles.append(Particle(x,y,color,(random.uniform(*vr),random.uniform(*vr)),life,size))
    def update(self):
        i=0
        while i<len(self.particles):
            p=self.particles[i]; p.x+=p.vx; p.y+=p.vy; p.vy+=0.1; p.life-=1
            if p.life<=0: self.particles[i]=self.particles[-1]; self.particles.pop()
            else: i+=1
    def draw(self,s):
        for p in self.particles:
            a=int(255*p.life/p.max_life)
            if a>10: pygame.draw.circle(s,(*p.color[:3],a),(int(p.x),int(p.y)),p.size)

particles = ParticleSystem()

class Achievement:
    def __init__(self,n,d,c,i="🏆"): self.name=n; self.desc=d; self.cond=c; self.unlocked=False; self.icon=i; self.time=0

class AchievementSystem:
    def __init__(self):
        self.achievements=[
            Achievement("Первая кровь","Убить монстра",lambda b:b.monsters_defeated>=1,"⚔️"),
            Achievement("Охотник","10 монстров",lambda b:b.monsters_defeated>=10,"🏹"),
            Achievement("Истребитель","50 монстров",lambda b:b.monsters_defeated>=50,"💀"),
            Achievement("Тысячник","1000 монет",lambda b:b.money>=1000,"💰"),
            Achievement("Богач","5000 монет",lambda b:b.money>=5000,"💎"),
            Achievement("Секретный агент","Undertale",lambda b:False,"🌟"),
            Achievement("Вооружён","Оружие",lambda b:b.weapon,"🗡️"),
            Achievement("Защищён","Броня",lambda b:b.armor>0,"🛡️"),
            Achievement("Быстрый","Скорость",lambda b:b.speed_boost>0,"👟"),
            Achievement("Плательщик","Выплатить 1000",lambda b:b.debt_paid>=1000,"💳")]
        self.recent=None; self.timer=0
    def check(self,bob,story):
        for a in self.achievements:
            if not a.unlocked and a.cond(bob): a.unlocked=True; a.time=120; self.recent=a; self.timer=180
        for a in self.achievements:
            if a.name=="Секретный агент" and not a.unlocked and story.undertale_found: a.unlocked=True; a.time=120; self.recent=a; self.timer=180
    def update(self):
        if self.timer>0: self.timer-=1
        if self.timer==0: self.recent=None
    def draw(self,s):
        if self.recent and self.timer>0:
            a=min(255,self.timer*2); y=max(50,self.timer-100)
            t=get_text(f"{self.recent.icon} {self.recent.name}",font,GOLD); r=t.get_rect(center=(WIDTH//2,y))
            bg=pygame.Surface((r.w+30,r.h+15),pygame.SRCALPHA); bg.fill((50,50,50,a))
            s.blit(bg,(r.x-15,r.y-7)); pygame.draw.rect(s,GOLD,(r.x-15,r.y-7,r.w+30,r.h+15),2)
            t.set_alpha(a); s.blit(t,r)

achievements = AchievementSystem()

class NightSystem:
    def __init__(self): self.is_night=False; self.timer=0; self.transition=0
    def update(self):
        self.timer+=1
        if self.timer>18000: self.timer=0; self.is_night=not self.is_night
        if self.is_night and self.transition<180: self.transition+=1
        elif not self.is_night and self.transition>0: self.transition-=1
    def get_darkness(self): return self.transition

night_system = NightSystem()

class Item:
    def __init__(self,n,t,p,d,e=None,r=None): self.name=n; self.type=t; self.price=p; self.desc=d; self.effect=e or {}; self.recipe=r

SHOP_ITEMS=[
    Item("Хлеб","food",5,"+15 энергии",{'energy':15}), Item("Сыр","food",10,"+30 энергии",{'energy':30}),
    Item("Пирог","food",20,"+60 энергии",{'energy':60}), Item("Эликсир","potion",35,"+100 энергии",{'energy':100}),
    Item("Зелье силы","potion",40,"+20 макс",{'max_energy':20}), Item("Зелье скорости","potion",45,"+1 скорости",{'speed':1}),
    Item("Газонокосилка","weapon",50,"Урон:1 Даль:75 Проч:25",{'damage':1,'range':75,'durability':25}),
    Item("Меч-траворез","weapon",150,"Урон:2 Даль:80 Проч:30",{'damage':2,'range':80,'durability':30}),
    Item("Огнемёт","weapon",400,"Урон:3 Даль:175 Проч:35",{'damage':3,'range':175,'durability':35,'needs_ammo':True,'ammo_type':'Горючее'}),
    Item("Бластер","weapon",800,"Урон:5 Даль:250 Проч:40",{'damage':5,'range':250,'durability':40,'needs_ammo':True,'ammo_type':'Плазма'}),
    Item("Гречневая пушка","weapon",1500,"Урон:8 Даль:300 Проч:50",{'damage':8,'range':300,'durability':50,'needs_ammo':True,'ammo_type':'Гречка'}),
    Item("Горючее","ammo",50,"Патроны для Огнемёта (35)",{'weapon':'Огнемёт','ammo':35}),
    Item("Плазма","ammo",100,"Патроны для Бластера (40)",{'weapon':'Бластер','ammo':40}),
    Item("Гречка-патроны","ammo",200,"Патроны для Пушки (50)",{'weapon':'Гречневая пушка','ammo':50}),
    Item("Кожаная куртка","armor",60,"Защита:10%",{'defense':10}),
    Item("Кольчуга","armor",200,"Защита:25%",{'defense':25}),
    Item("Гречневый панцирь","armor",500,"Защита:50%",{'defense':50})]

CRAFT_RECIPES=[
    Item("Зелье здоровья","potion",0,"+50 энергии",{'energy':50},{'flower':5,'mushroom':2}),
    Item("Бомба","weapon",0,"Урон:10",{'damage':10,'single_use':True},{'bug':10,'mushroom':3}),
    Item("Эликсир скорости","potion",0,"+2 скорости",{'speed':2},{'flower':8,'golden_grain':1})]

class Monster:
    def __init__(self,x,y,t,pr=100):
        self.x=x; self.y=y; self.sx=x; self.sy=y; self.type=t; self.pr=pr; self.at=random.uniform(0,6.28)
        D={"slug":(1.5,20,20,3,10,"Слизень",150),"beetle":(2.5,35,25,5,25,"Жук-вредитель",180),
           "weed":(1.0,50,30,8,50,"Злой сорняк",130),"boss_cricket":(3.0,80,40,20,200,"Гигантский сверчок",250),
           "mutant_grain":(2.0,60,28,12,100,"Мутант-зерно",200),"grecha_demon":(3.5,100,45,30,500,"Демон Гречки",300),
           "flowey":(0,5,20,99,0,"Flowey",100)}
        s=D[t]; self.sp,self.dmg,self.sz,self.hp,self.sc,self.name,self.ar=s; self.mhp=self.hp
        self.r=pygame.Rect(x-self.sz,y-self.sz,self.sz*2,self.sz*2); self.st="patrol"
        self.dir=random.uniform(0,6.28); self.cdt=random.randint(60,180); self.stun=0; self.ac=0; self.ait=0
    def move(self,br,lb=None):
        if self.type=="flowey" or self.stun>0:
            if self.stun>0: self.stun-=1
            return
        self.at+=0.05; db=math.hypot(self.x-br.centerx,self.y-br.centery); ds=math.hypot(self.x-self.sx,self.y-self.sy)
        ab=50 if night_system.is_night else 0
        if db<self.ar+ab:
            if self.st!="chase": self.st="chase"; self.ait=60
        elif ds>10 and self.st=="chase": self.st="return"
        elif ds<=10 and self.st=="return": self.st="patrol"; self.dir=random.uniform(0,6.28)
        if self.st=="chase":
            dx=br.centerx-self.x; dy=br.centery-self.y; d=max(1,math.hypot(dx,dy))
            sm=1.8 if night_system.is_night else 1.5; self.x+=dx/d*self.sp*sm; self.y+=dy/d*self.sp*sm
        elif self.st=="return":
            dx=self.sx-self.x; dy=self.sy-self.y; d=max(1,math.hypot(dx,dy)); self.x+=dx/d*self.sp; self.y+=dy/d*self.sp
        else:
            self.cdt-=1
            if self.cdt<=0: self.dir=random.uniform(0,6.28); self.cdt=random.randint(60,180)
            nx=self.x+math.cos(self.dir)*self.sp; ny=self.y+math.sin(self.dir)*self.sp
            if math.hypot(nx-self.sx,ny-self.sy)<=self.pr: self.x=nx; self.y=ny
            else: self.dir=math.atan2(self.sy-self.y,self.sx-self.x)
        if lb: self.x=max(lb[0]+self.sz,min(lb[0]+lb[2]-self.sz,self.x)); self.y=max(lb[1]+self.sz,min(lb[1]+lb[3]-self.sz,self.y))
        self.r.center=(int(self.x),int(self.y))
        if self.ac>0: self.ac-=1
        if self.ait>0: self.ait-=1
    def draw(self,s):
        x,y=int(self.x),int(self.y); t=self.at
        if self.type=="flowey":
            sb=math.sin(t*2)*2; pygame.draw.line(s,DARK_GREEN,(x,y+10),(x,y+30+sb),3)
            for i in range(5): a=i*1.256+math.sin(t*3+i)*0.3; pygame.draw.circle(s,YELLOW,(int(x+math.cos(a)*14),int(y+math.sin(a)*14)),7)
            pygame.draw.circle(s,(255,255,200),(x,y),10); ea=math.sin(t*2)*5
            pygame.draw.circle(s,WHITE,(x-5,y-3),4); pygame.draw.circle(s,WHITE,(x+5,y-3),4)
            pygame.draw.circle(s,BLACK,(int(x-5+ea),y-3),2); pygame.draw.circle(s,BLACK,(int(x+5+ea),y-3),2)
            pygame.draw.arc(s,BLACK,(x-5,y,10,6+math.sin(t*3)),0,3.14,2); return
        if self.st=="chase":
            ss=pygame.Surface((self.ar*2,self.ar*2),pygame.SRCALPHA)
            pygame.draw.circle(ss,(255,0,0,int(20+math.sin(t*5)*10)),(self.ar,self.ar),self.ar); s.blit(ss,(x-self.ar,y-self.ar))
        if self.ait>0:
            tx=get_text("!",font,RED); r=tx.get_rect(center=(x,y-self.sz-20+math.sin(self.ait*0.3)*5)); s.blit(tx,r)
        if self.type=="slug":
            p=1+math.sin(t*3)*0.1; w,h=int(34*p),int(18*p); b=math.sin(t*3)*2
            pygame.draw.ellipse(s,(150,255,150),(x-w//2,y-h//2+b,w,h)); pygame.draw.ellipse(s,(200,255,200),(x-w//2+3,y-h//2+2+b,w-6,h-4))
            sw=math.sin(t*4)*2; pygame.draw.line(s,(150,255,150),(x-9,y-9+b),(int(x-13+sw),int(y-15+b)),2)
            pygame.draw.line(s,(150,255,150),(x+9,y-9+b),(int(x+13+sw),int(y-15+b)),2)
        elif self.type=="beetle":
            sb=math.sin(t*5)*1; pygame.draw.circle(s,(139,69,19),(x,y+sb),self.sz); pygame.draw.circle(s,(100,50,10),(x,y+sb),self.sz-4)
            hx=x+self.sz-5+math.sin(t*3)*2; pygame.draw.circle(s,BLACK,(int(hx),y),9)
            gl=int(150+math.sin(t*8)*50); pygame.draw.circle(s,(255,gl,gl),(int(hx+6),y-3),3); pygame.draw.circle(s,(255,gl,gl),(int(hx+6),y+3),3)
        elif self.type=="weed":
            sw=math.sin(t*2)*5; pygame.draw.line(s,DARK_GREEN,(x,y),(x+sw,y+22),4)
            for side in[-1,1]: pygame.draw.ellipse(s,GREEN,(x+side*17+math.sin(t*3+side)*3-7,y+9,14,7))
            pygame.draw.circle(s,(100,255,100),(x,y),self.sz-5)
            for i in range(5): a=t*2+i*1.256; pygame.draw.circle(s,(50,205,50),(int(x+math.cos(a)*14),int(y+math.sin(a)*14)),7)
            pygame.draw.circle(s,RED,(x-6,y-6),6); pygame.draw.circle(s,RED,(x+6,y-6),6)
        elif self.type=="boss_cricket":
            wf=math.sin(t*10)*6; pygame.draw.ellipse(s,(255,255,100),(x-18,int(y-18-wf),36,int(12+wf)))
            vb=math.sin(t*20)*1; pygame.draw.ellipse(s,(200,200,0),(x-23,int(y-12+vb),46,24)); pygame.draw.circle(s,(180,180,0),(x-25,y),14)
            eg=int(200+math.sin(t*15)*55); pygame.draw.circle(s,(eg,0,0),(x-30,y-5),5); pygame.draw.circle(s,(eg,0,0),(x-30,y+5),5)
            aa=int(30+math.sin(t*3)*15); au=pygame.Surface((90,90),pygame.SRCALPHA); pygame.draw.circle(au,(255,255,0,aa),(45,45),40); s.blit(au,(x-45,y-45))
        elif self.type=="mutant_grain":
            p=1+math.sin(t*4)*0.15; r=int(self.sz*p)
            pygame.draw.circle(s,(180,50,180),(x,y),r); pygame.draw.circle(s,(200,80,200),(x,y),r-5)
            for i in range(6): a=t*3+i*1.047; pygame.draw.circle(s,RED,(int(x+math.cos(a)*r),int(y+math.sin(a)*r)),4)
        elif self.type=="grecha_demon":
            vb=math.sin(t*15)*2; pygame.draw.circle(s,(255,30,30),(x,int(y+vb)),self.sz); pygame.draw.circle(s,(200,20,20),(x,int(y+vb)),self.sz-6)
            for i in range(4): a=t*2+i*1.57; pygame.draw.circle(s,YELLOW,(int(x+math.cos(a)*(self.sz-2)),int(y+math.sin(a)*(self.sz-2)+vb)),6)
        if self.hp<self.mhp:
            bw,bh=35,5; bx,by=x-bw//2,y-self.sz-18; pygame.draw.rect(s,RED,(bx,by,bw,bh))
            hw=int(self.hp/self.mhp*bw); c=GREEN if self.hp>self.mhp*0.5 else (YELLOW if self.hp>self.mhp*0.25 else RED)
            pygame.draw.rect(s,c,(bx,by,hw,bh))
    def attack(self,bob):
        if self.type=="flowey" or self.ac>0: return False
        if math.hypot(self.x-bob.r.centerx,self.y-bob.r.centery)<self.sz+18:
            d=max(1,self.dmg-bob.armor)
            if night_system.is_night: d=int(d*1.5)
            if bob.shield: d//=2
            bob.hurt(d); self.ac=50; return True
        return False
    def hit(self,dmg):
        if self.type=="flowey": return False
        self.hp-=dmg; self.stun=25; particles.emit(self.x,self.y,YELLOW,5,(-2,2),15,2)
        if self.hp<=0: c=RED if self.type=="grecha_demon" else GREEN; particles.emit(self.x,self.y,c,12,(-4,4),25,4); return True
        return False

class Collectible:
    def __init__(self,x,y,t):
        self.x=x; self.y=y; self.type=t; self.col=False; self.at=random.uniform(0,6.28)
        V={'flower':5,'bug':8,'mushroom':12,'golden_grain':50,'undertale_flower':25}; self.val=V.get(t,5)
    def draw(self,s):
        if self.col: return
        self.at+=0.03; t=self.at
        if self.type=='flower':
            sw=math.sin(t*2)*2; pygame.draw.line(s,DARK_GREEN,(self.x,self.y),(self.x+sw,self.y+14),2)
            for i in range(5): a=i*1.256+math.sin(t*3+i)*0.2; pygame.draw.circle(s,(255,150,150),(int(self.x+math.cos(a)*7),int(self.y+math.sin(a)*7)),4)
            pygame.draw.circle(s,YELLOW,(self.x,self.y),int(2.5+math.sin(t*4)*0.5))
        elif self.type=='bug':
            c=math.sin(t*5)*2; pygame.draw.ellipse(s,(150,255,150),(self.x-4+c,self.y-2,8,5))
        elif self.type=='mushroom':
            pygame.draw.rect(s,WHITE,(self.x-3,self.y,6,12)); wb=math.sin(t*1.5)*3
            pygame.draw.ellipse(s,(200,150,100),(self.x-9+wb,self.y-7,18,12))
        elif self.type=='golden_grain':
            sc=1+math.sin(t*3)*0.15; ga=int(80+math.sin(t*4)*40)
            g=pygame.Surface((24,24),pygame.SRCALPHA); pygame.draw.circle(g,(255,215,0,ga),(12,12),12); s.blit(g,(self.x-12,self.y-12))
        elif self.type=='undertale_flower':
            sw=math.sin(t*1.5)*2; pygame.draw.line(s,DARK_GREEN,(self.x,self.y),(self.x+sw,self.y+14),2)
            for i in range(5): a=i*1.256+math.sin(t*2+i)*0.2; pygame.draw.circle(s,YELLOW,(int(self.x+math.cos(a)*7),int(self.y+math.sin(a)*7)),5)
            pygame.draw.circle(s,(255,255,200),(self.x,self.y),int(3+math.sin(t*3)*0.5))
    def check(self,br): return not self.col and math.hypot(self.x-br.centerx,self.y-br.centery)<25

class Building:
    def __init__(self,x,y,w,h,c,n,i): self.r=pygame.Rect(x,y,w,h); self.color=c; self.name=n; self.icon=i; self.at=random.uniform(0,6.28)
    def draw(self,s):
        self.at+=0.02; t=self.at
        pygame.draw.rect(s,self.color,self.r,border_radius=15); pygame.draw.rect(s,WHITE,self.r,3,border_radius=15)
        if self.name=="Дом":
            pygame.draw.polygon(s,(139,69,19),[(self.r.x,self.r.y),(self.r.centerx,self.r.y-30),(self.r.right,self.r.y)])
            for i in range(2):
                sx=self.r.right-20+math.sin(t*2+i)*10; sy=self.r.y-20-i*10+math.cos(t*3+i)*6
                sm=pygame.Surface((10,10),pygame.SRCALPHA); pygame.draw.circle(sm,(200,200,200,150-i*40),(5,5),5); s.blit(sm,(sx,sy))
        elif self.name=="Ресторан":
            sy=self.r.y-15+math.sin(t*3)*3; pygame.draw.rect(s,YELLOW,(self.r.x+20,sy,100,25),border_radius=5)
            s.blit(get_text("РЕСТОРАН",small_font,BLACK),(self.r.x+30,sy+5))
        elif self.name=="Магазин":
            for i in range(0,self.r.width,15): pygame.draw.rect(s,RED if i%30==0 else WHITE,(self.r.x+i,self.r.y-5,15,8))
        elif self.name=="Кузница":
            pygame.draw.rect(s,GRAY,(self.r.x+30,self.r.y-20,100,25))
            for i in range(3): pygame.draw.circle(s,ORANGE,(self.r.x+50+i*25,self.r.y+20),8)
        elif self.name=="Банк":
            pygame.draw.rect(s,DARK_BG,(self.r.x+50,self.r.y-15,60,20))
            s.blit(get_text("$",big_font,GOLD),(self.r.centerx-10,self.r.centery-10))
        elif self.name=="Библиотека":
            for i in range(4): pygame.draw.rect(s,(139,90,50),(self.r.x+20+i*25,self.r.y+10,15,40))
            pygame.draw.rect(s,BROWN,(self.r.x+35,self.r.y,90,10))
        tx=get_text(self.icon,font,WHITE); s.blit(tx,tx.get_rect(center=(self.r.centerx,self.r.centery-15)))
        tx=get_text(self.name,font,WHITE); r=tx.get_rect(center=(self.r.centerx,self.r.centery+20))
        pygame.draw.rect(s,BLACK,r.inflate(10,5),border_radius=5); s.blit(tx,r)

class LocationPortal:
    def __init__(self,x,y,t,n,c=PURPLE): self.r=pygame.Rect(x,y,50,50); self.target=t; self.name=n; self.color=c; self.p=0
    def draw(self,s):
        self.p+=0.05; t=self.p; ps=math.sin(t)*3
        for r in[25,20,15]:
            a=100+int(math.sin(t+r)*50); c=(min(255,self.color[0]),min(255,self.color[1]+a//3),min(255,self.color[2]+a//3))
            pygame.draw.circle(s,c,self.r.center,r+ps)
        pygame.draw.ellipse(s,DARK_BG,self.r); pygame.draw.ellipse(s,self.color,self.r,3)
        for i in range(5):
            a=t*2+i*1.256; d=18+math.sin(t*3+i)*5
            pygame.draw.circle(s,(random.randint(100,255),random.randint(100,255),255),(int(self.r.centerx+math.cos(a)*d),int(self.r.centery+math.sin(a)*d)),2)
        tx=get_text(self.name,small_font,WHITE); r=tx.get_rect(center=(self.r.centerx,self.r.bottom+15))
        pygame.draw.rect(s,BLACK,r.inflate(10,5),border_radius=5); s.blit(tx,r)

class ShopWindow:
    def __init__(self): self.active=False; self.sel=0; self.msg=""; self.mt=0; self.tab=0
    def open(self): self.active=True; self.sel=0; self.msg=""; self.tab=0
    def close(self): self.active=False
    def update(self):
        if self.mt>0: self.mt-=1
        if self.mt==0: self.msg=""
    def buy(self,bob,item):
        if bob.money>=item.price:
            bob.money-=item.price
            if item.type=='food': bob.energy=min(bob.max_energy,bob.energy+item.effect.get('energy',0)); self.msg=f"Куплено: {item.name}!"
            elif item.type=='potion':
                if'energy'in item.effect: bob.energy=min(bob.max_energy,bob.energy+item.effect['energy'])
                if'max_energy'in item.effect: bob.max_energy+=item.effect['max_energy']
                if'speed'in item.effect: bob.speed_boost+=item.effect['speed']; bob.speed=4+bob.speed_boost
                self.msg=f"Куплено: {item.name}!"
            elif item.type=='weapon':
                bob.weapon=True; bob.weapon_damage=item.effect.get('damage',1)
                bob.weapon_name=item.name; bob.weapon_durability=item.effect.get('durability',25)
                bob.weapon_max_durability=item.effect.get('durability',25)
                bob.weapon_range=item.effect.get('range',55)
                bob.needs_ammo=item.effect.get('needs_ammo',False)
                bob.ammo_type=item.effect.get('ammo_type','')
                if bob.needs_ammo: bob.ammo=0
                self.msg=f"Куплено: {item.name}!"
            elif item.type=='ammo':
                if bob.weapon and bob.needs_ammo:
                    weapon_match=item.effect.get('weapon','')
                    if bob.weapon_name==weapon_match or bob.ammo_type==weapon_match:
                        bob.ammo+=item.effect.get('ammo',0)
                        self.msg=f"Куплено: {item.name}! Патронов: {bob.ammo}"
                    else: self.msg=f"Не подходит! Нужно: {bob.ammo_type}"; bob.money+=item.price; self.mt=60; return False
                else: self.msg="Нет оружия или не нужны патроны!"; bob.money+=item.price; self.mt=60; return False
            elif item.type=='armor': bob.armor=item.effect.get('defense',0); self.msg=f"Куплено: {item.name}!"
            self.mt=120; return True
        else: self.msg="Недостаточно денег!"; self.mt=60; return False
    def craft(self,bob,item):
        if item.recipe:
            ok=True
            for m,c in item.recipe.items():
                if bob.materials.get(m,0)<c: ok=False; break
            if ok:
                for m,c in item.recipe.items(): bob.materials[m]-=c
                if'energy'in item.effect: bob.energy=min(bob.max_energy,bob.energy+item.effect['energy'])
                if'speed'in item.effect: bob.speed_boost+=item.effect['speed']; bob.speed=4+bob.speed_boost
                self.msg=f"Создано: {item.name}!"; self.mt=120; return True
            else: self.msg="Недостаточно материалов!"; self.mt=60
        return False
    def draw(self,s,bob):
        if not self.active: return
        o=pygame.Surface((WIDTH,HEIGHT)); o.set_alpha(180); o.fill(BLACK); s.blit(o,(0,0))
        ww,wh=700,600; wx=WIDTH//2-ww//2; wy=HEIGHT//2-wh//2
        pygame.draw.rect(s,(40,40,40),(wx,wy,ww,wh),border_radius=15); pygame.draw.rect(s,GOLD,(wx,wy,ww,wh),4,border_radius=15)
        tabs=["МАГАЗИН","КРАФТ"]
        for i,tn in enumerate(tabs): c=YELLOW if i==self.tab else WHITE; s.blit(get_text(tn,font,c),(wx+50+i*200,wy+15))
        s.blit(get_text(f"Деньги: {bob.money}",font,GOLD),(wx+400,wy+20))
        pygame.draw.line(s,GOLD,(wx+30,wy+50),(wx+ww-30,wy+50),2)
        items=CRAFT_RECIPES if self.tab==1 else SHOP_ITEMS
        yo=wy+60
        for i,item in enumerate(items):
            if i==self.sel: pygame.draw.rect(s,(60,60,60),(wx+20,yo+i*28-2,ww-40,26),border_radius=5)
            icon=""
            if item.type=="weapon":
                if "Газонокосилка" in item.name: icon="🪚"
                elif "Меч" in item.name: icon="⚔️"
                elif "Огнемёт" in item.name: icon="🔥"
                elif "Бластер" in item.name: icon="🔫"
                elif "Пушка" in item.name: icon="💥"
            elif item.type=="ammo":
                if "Горючее" in item.name: icon="🛢️"
                elif "Плазма" in item.name: icon="🔮"
                elif "Гречка" in item.name: icon="🌾"
            elif item.type=="food": icon="🍞"
            elif item.type=="potion": icon="🧪"
            elif item.type=="armor": icon="🛡️"
            s.blit(get_text(f"{icon} {item.name}",small_font,WHITE),(wx+30,yo+i*28))
            if self.tab==0: s.blit(get_text(f"{item.desc} - {item.price} монет",tiny_font,GRAY),(wx+250,yo+i*28+3))
            else:
                rc=" + ".join([f"{v}x {k}" for k,v in item.recipe.items()])
                s.blit(get_text(f"{item.desc} | {rc}",tiny_font,GRAY),(wx+200,yo+i*28+3))
        if self.msg:
            c=GREEN if"Куплено"in self.msg or"Создано"in self.msg else RED
            tx=get_text(self.msg,font,c); r=tx.get_rect(center=(wx+ww//2,wy+wh-60))
            pygame.draw.rect(s,BLACK,r.inflate(20,10),border_radius=5); s.blit(tx,r)
        s.blit(get_text("Tab-вкладки|Стрелки|Enter|E-выход",small_font,WHITE),(wx+50,wy+wh-30))

class InventoryWindow:
    def __init__(self): self.active=False
    def open(self): self.active=True
    def close(self): self.active=False
    def draw(self,s,bob):
        if not self.active: return
        o=pygame.Surface((WIDTH,HEIGHT)); o.set_alpha(180); o.fill(BLACK); s.blit(o,(0,0))
        ww,wh=600,450; wx=WIDTH//2-ww//2; wy=HEIGHT//2-wh//2
        pygame.draw.rect(s,(40,40,40),(wx,wy,ww,wh),border_radius=15); pygame.draw.rect(s,GOLD,(wx,wy,ww,wh),4,border_radius=15)
        s.blit(get_text("ИНВЕНТАРЬ",big_font,YELLOW),(wx+200,wy+10))
        st=[f"Деньги: {bob.money}",f"Энергия: {int(bob.energy)}/{bob.max_energy}",
            f"Оружие: {bob.weapon_name} (урон:{bob.weapon_damage})",f"Дальность: {bob.weapon_range}",
            f"Прочность: {bob.weapon_durability}/{bob.weapon_max_durability}",
            f"Патроны: {bob.ammo if bob.needs_ammo else 'не нужны'}",
            f"Защита: {bob.armor}%",f"Скорость: {bob.speed}",
            f"Убито: {bob.monsters_defeated}",f"Долг: {bob.debt-bob.debt_paid}/{bob.debt}",
            f"Q-щит({max(0,int(bob.shield_cd/60))}с) R-файрбол({max(0,int(bob.fire_cd/60))}с) H-хил({max(0,int(bob.heal_cd/60))}с)"]
        for i,st in enumerate(st): s.blit(get_text(st,font,WHITE),(wx+30,wy+60+i*30))
        s.blit(get_text("Материалы:",font,YELLOW),(wx+30,wy+400))
        ms=[f"Цветы:{bob.materials.get('flower',0)}",f"Жуки:{bob.materials.get('bug',0)}",
            f"Грибы:{bob.materials.get('mushroom',0)}",f"Золото:{bob.materials.get('golden_grain',0)}"]
        for i,m in enumerate(ms): s.blit(get_text(m,small_font,WHITE),(wx+30+i*140,wy+430))
        s.blit(get_text("Нажми I чтобы закрыть",small_font,WHITE),(wx+220,wy+wh-30))

class HelpWindow:
    def __init__(self): self.active=False
    def open(self): self.active=True
    def close(self): self.active=False
    def draw(self,s):
        if not self.active: return
        o=pygame.Surface((WIDTH,HEIGHT)); o.set_alpha(190); o.fill(BLACK); s.blit(o,(0,0))
        ww,wh=750,500; wx=WIDTH//2-ww//2; wy=HEIGHT//2-wh//2
        pygame.draw.rect(s,(30,30,50),(wx,wy,ww,wh),border_radius=15)
        pygame.draw.rect(s,GOLD,(wx,wy,ww,wh),4,border_radius=15)
        s.blit(get_text("ИНСТРУКЦИЯ",big_font,YELLOW),(wx+250,wy+15))
        lines=["Цель: выплатить кредит 10000 монет Мистеру Грече!","",
               "УПРАВЛЕНИЕ:","  WASD - движение","  E - взаимодействие / атака",
               "  SPACE - выплатить кредит (50 монет)","  Q - щит (3 сек, кулдаун 5 сек)",
               "  R - фаербол (урон всем рядом)","  H - лечение (+50 энергии)",
               "  I - инвентарь","  F1 - эта инструкция","  F5 - сохранить игру","  ESC - выход","",
               "ОРУЖИЕ: прочность, дальность, патроны, кулдаун","  Бластер - самый быстрый! КД 0.25с","",
               "ЗДАНИЯ: Дом, Ресторан, Магазин, Кузница, Банк,","  Библиотека, Таверна, Склад",
               "  Ресторан: кулдаун 5 сек между работами","",
               "ПОРТАЛЫ (справа): 4 локации + секретная","  Мобы респавнятся при перезаходе в локацию!"]
        for i,line in enumerate(lines):
            if line: s.blit(get_text(line,small_font,WHITE),(wx+30,wy+60+i*22))
        s.blit(get_text("Нажми F1 чтобы закрыть",font,GOLD),(wx+250,wy+wh-35))

class GameOverMenu:
    def __init__(self): self.active=False; self.sel=0
    def show(self): self.active=True; self.sel=0
    def draw(self,s):
        if not self.active: return
        o=pygame.Surface((WIDTH,HEIGHT)); o.set_alpha(200); o.fill(BLACK); s.blit(o,(0,0))
        s.blit(get_text("GAME OVER",big_font,RED),get_text("GAME OVER",big_font,RED).get_rect(center=(WIDTH//2,HEIGHT//2-80)))
        for i,opt in enumerate(["Рестарт","Выйти"]):
            c=YELLOW if i==self.sel else WHITE; s.blit(get_text(opt,font,c),get_text(opt,font,c).get_rect(center=(WIDTH//2,HEIGHT//2+i*40)))

class VictoryMenu:
    def __init__(self): self.active=False; self.sel=0
    def show(self): self.active=True; self.sel=0
    def draw(self,s):
        if not self.active: return
        o=pygame.Surface((WIDTH,HEIGHT)); o.set_alpha(200); o.fill(BLACK); s.blit(o,(0,0))
        s.blit(get_text("ПОБЕДА!",big_font,YELLOW),get_text("ПОБЕДА!",big_font,YELLOW).get_rect(center=(WIDTH//2,HEIGHT//2-80)))
        s.blit(get_text("Боб выплатил кредит!",font,WHITE),get_text("Боб выплатил кредит!",font,WHITE).get_rect(center=(WIDTH//2,HEIGHT//2-30)))
        for i,opt in enumerate(["Продолжить","Выйти"]):
            c=YELLOW if i==self.sel else WHITE; s.blit(get_text(opt,font,c),get_text(opt,font,c).get_rect(center=(WIDTH//2,HEIGHT//2+i*40+20)))

class TraderNPC:
    def __init__(self): self.active=False; self.x=0; self.y=0; self.r=pygame.Rect(0,0,40,50); self.timer=0; self.st=random.randint(600,1800)
    def update(self,loc):
        if loc!="main": self.active=False; return
        self.st-=1
        if self.st<=0 and not self.active: self.active=True; self.x=random.randint(300,1300); self.y=random.randint(int(HEIGHT*0.3)+50,HEIGHT-200); self.r.x=self.x; self.r.y=self.y; self.timer=600
        if self.active: self.timer-=1
        if self.timer<=0: self.active=False; self.st=random.randint(600,1800)
    def draw(self,s):
        if not self.active: return
        x,y=self.x,self.y; t=pygame.time.get_ticks()*0.01
        pygame.draw.rect(s,PURPLE,(x-10,int(y-10+math.sin(t)*2),20,12)); pygame.draw.rect(s,PURPLE,(x-6,int(y-18+math.sin(t)*2),12,10))
        pygame.draw.rect(s,GREEN,(x-8,y,16,20),border_radius=4)
        pygame.draw.circle(s,WHITE,(x-4,y+6),3); pygame.draw.circle(s,WHITE,(x+4,y+6),3)
        pygame.draw.circle(s,BLACK,(x-4,y+6),1); pygame.draw.circle(s,BLACK,(x+4,y+6),1)
        pygame.draw.circle(s,GOLD,(x+12,int(y+8+math.sin(t*2)*2)),6)
        s.blit(get_text("Торговец (E)",tiny_font,YELLOW),get_text("Торговец (E)",tiny_font,YELLOW).get_rect(center=(x,y-25)))

trader = TraderNPC()

class Bob:
    def __init__(self,x,y):
        self.r=pygame.Rect(x,y,28,36); self.speed=4; self.speed_boost=0; self.money=20; self.energy=100; self.max_energy=100
        self.debt=10000; self.debt_paid=0; self.portal_unlocked=False; self.action_text=""; self.action_timer=0
        self.dir="right"; self.at=0; self.inv_timer=0; self.monsters_defeated=0; self.weapon=False; self.weapon_damage=0
        self.weapon_name="Нет"; self.armor=0; self.ac=0; self.blink=random.randint(60,180); self.moving=False
        self.materials={'flower':0,'bug':0,'mushroom':0,'golden_grain':0}
        self.shield=False; self.shield_timer=0; self.shield_cd=0; self.fire_cd=0; self.heal_cd=0
        self.weapon_durability=0; self.weapon_max_durability=0; self.weapon_range=55
        self.needs_ammo=False; self.ammo=0; self.ammo_type=""
        self.restaurant_cooldown=0
    def move(self,keys):
        dx,dy=0,0; self.moving=False
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx=-self.speed; self.dir="left"; self.moving=True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx=self.speed; self.dir="right"; self.moving=True
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy=-self.speed; self.moving=True
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy=self.speed; self.moving=True
        self.r.x+=dx; self.r.y+=dy
        min_y=int(HEIGHT*0.30); max_y=HEIGHT-130
        self.r.x=max(0,min(WIDTH-self.r.width,self.r.x)); self.r.y=max(min_y,min(max_y-self.r.height,self.r.y))
        if self.moving: self.energy=max(0,self.energy-0.01); self.at+=0.15
        else: self.at=0
        self.blink-=1
        if self.blink<=0: self.blink=random.randint(60,180)
    def hurt(self,dmg):
        if self.inv_timer<=0: self.energy=max(0,self.energy-dmg); self.inv_timer=80; self.action_text=f"Урон: -{dmg}"; self.action_timer=60; particles.emit(self.r.centerx,self.r.centery,RED,8,(-3,3),20,3); return True
        return False
    def draw(self,s):
        if self.inv_timer>0 and self.inv_timer%10<5: return
        cx,cy=self.r.centerx,self.r.centery; t=self.at
        pygame.draw.ellipse(s,(150,150,150),(cx-10,cy+14,20,6))
        if self.moving: lol=math.sin(t*5)*4; lor=math.sin(t*5+math.pi)*4; aol=math.sin(t*5+math.pi)*5; aor=math.sin(t*5)*5; bb=math.sin(t*10)*1
        else: lol=lor=aol=aor=bb=0
        pygame.draw.line(s,(50,30,20),(cx-4,cy+16),(cx-5-lol,cy+22),3); pygame.draw.line(s,(50,30,20),(cx+4,cy+16),(cx+5-lor,cy+22),3)
        pygame.draw.rect(s,BLUE,(cx-8,cy-2+bb,16,16),border_radius=4); pygame.draw.rect(s,BROWN,(cx-8,cy+8+bb,16,3))
        pygame.draw.line(s,SKIN,(cx-8,cy+2+bb),(cx-14+aol,cy+10+bb),4); pygame.draw.circle(s,SKIN,(int(cx-14+aol),int(cy+10+bb)),3)
        pygame.draw.line(s,SKIN,(cx+8,cy+2+bb),(cx+14+aor,cy+10+bb),4); pygame.draw.circle(s,SKIN,(int(cx+14+aor),int(cy+10+bb)),3)
        pygame.draw.circle(s,SKIN,(cx,cy-8+bb),10)
        hb=math.sin(t*3)*1 if self.moving else 0
        pygame.draw.arc(s,BROWN,(cx-10,cy-18+bb+hb,20,14),3.14,6.28,5)
        for i in range(-4,5,2): pygame.draw.line(s,BROWN,(cx+i,cy-16+bb+hb),(cx+i-2,cy-12+bb+hb),2)
        ed=-2 if self.dir=="left" else 2
        if self.blink<5: eh=1
        else: eh=3
        pygame.draw.ellipse(s,WHITE,(cx-7+ed//2,cy-11+bb,5,eh*2)); pygame.draw.ellipse(s,WHITE,(cx+2+ed//2,cy-11+bb,5,eh*2))
        if self.blink>=5: pygame.draw.circle(s,BLACK,(cx-4+ed//2,cy-10+bb),1); pygame.draw.circle(s,BLACK,(cx+5+ed//2,cy-10+bb),1)
        if self.energy>50: pygame.draw.arc(s,BLACK,(cx-3,cy-6+bb,6,4),0,3.14,1)
        elif self.energy>20: pygame.draw.line(s,BLACK,(cx-3,cy-4+bb),(cx+3,cy-4+bb),1)
        else: pygame.draw.arc(s,BLACK,(cx-3,cy-2+bb,6,4),3.14,6.28,1)
        if self.shield:
            sa=int(100+math.sin(pygame.time.get_ticks()*0.01)*40); sh=pygame.Surface((40,40),pygame.SRCALPHA)
            pygame.draw.circle(sh,(100,200,255,sa),(20,20),18); s.blit(sh,(cx-20,cy-25+bb))
        if self.weapon:
            wx=cx-12 if self.dir=="left" else cx+12; wy=cy-5+bb
            if "Газонокосилка" in self.weapon_name:
                pygame.draw.rect(s,GRAY,(wx-3,wy-10,6,18)); pygame.draw.rect(s,RED,(wx-6,wy-12,12,6)); pygame.draw.circle(s,GREEN,(wx,wy-5),3)
            elif "Меч" in self.weapon_name:
                pygame.draw.rect(s,(180,180,200),(wx-1,wy-14,3,22)); pygame.draw.rect(s,GOLD,(wx-3,wy-16,7,6)); pygame.draw.rect(s,BROWN,(wx-2,wy-10,5,6))
            elif "Огнемёт" in self.weapon_name:
                pygame.draw.rect(s,RED,(wx-4,wy-10,8,20)); pygame.draw.rect(s,ORANGE,(wx-2,wy-12,4,24)); pygame.draw.circle(s,YELLOW,(wx,wy-12),3)
            elif "Бластер" in self.weapon_name:
                pygame.draw.rect(s,(100,100,200),(wx-3,wy-12,6,20)); pygame.draw.rect(s,CYAN,(wx-1,wy-14,4,6)); pygame.draw.circle(s,WHITE,(wx,wy-14),2)
            elif "Пушка" in self.weapon_name or "Гречневая" in self.weapon_name:
                pygame.draw.rect(s,(150,100,50),(wx-5,wy-12,10,22)); pygame.draw.rect(s,GOLD,(wx-3,wy-14,6,8)); pygame.draw.circle(s,RED,(wx,wy-4),2)
            else:
                wc=GRAY if self.weapon_damage<=2 else (GOLD if self.weapon_damage<=5 else RED)
                pygame.draw.rect(s,wc,(wx-2,wy-8,4,16)); pygame.draw.rect(s,RED,(wx-5,wy-10,10,5))
    def use_ability(self,ability,monsters):
        if ability=="fireball" and self.fire_cd<=0:
            self.fire_cd=180
            for m in monsters[:]:
                if math.hypot(self.r.centerx-m.x,self.r.centery-m.y)<200:
                    if m.hit(5): monsters.remove(m); self.monsters_defeated+=1
            particles.emit(self.r.centerx,self.r.centery,ORANGE,20,(-5,5),30,5); self.action_text="Файрбол!"; self.action_timer=45
        elif ability=="shield" and self.shield_cd<=0:
            self.shield_cd=300; self.shield=True; self.shield_timer=180
            particles.emit(self.r.centerx,self.r.centery,CYAN,10,(-2,2),20,4); self.action_text="Щит!"; self.action_timer=45
        elif ability=="heal" and self.heal_cd<=0:
            self.heal_cd=600; self.energy=min(self.max_energy,self.energy+50)
            particles.emit(self.r.centerx,self.r.centery,GREEN,15,(-3,3),25,4); self.action_text="+50 энергии!"; self.action_timer=45
    def collect(self,item):
        self.money+=item.val; item.col=True
        mm={'flower':'flower','bug':'bug','mushroom':'mushroom','golden_grain':'golden_grain'}
        if item.type in mm: self.materials[mm[item.type]]=self.materials.get(mm[item.type],0)+1
        particles.emit(item.x,item.y,YELLOW,8,(-2,2),15,3)
        self.action_text=f"+{item.val} монет!"; self.action_timer=60
    def interact(self,b):
        if b.name=="Ресторан":
            if self.restaurant_cooldown>0:
                self.action_text=f"Подожди {int(self.restaurant_cooldown/60)+1} сек"; self.action_timer=30; return
            if self.energy>=30:
                self.energy-=30; tips=random.randint(20,50); self.money+=tips
                self.restaurant_cooldown=300
                self.action_text=f"+{tips} монет"; self.action_timer=90
            else: self.action_text="Нужно 30+ энергии"; self.action_timer=60
        elif b.name=="Дом":
            if self.energy<self.max_energy: self.energy=self.max_energy; self.action_text="Энергия восстановлена!"; self.action_timer=60
            else: self.action_text="Энергия полная!"; self.action_timer=40
        elif b.name=="Кузница":
            if self.weapon and self.money>=200:
                self.money-=200; self.weapon_damage+=1
                self.weapon_name=f"{self.weapon_name}+"
                self.weapon_max_durability+=5; self.weapon_durability=self.weapon_max_durability
                self.action_text=f"Оружие улучшено! Урон: {self.weapon_damage}"; self.action_timer=90
            elif self.armor>0 and self.money>=150:
                self.money-=150; self.armor=min(80,self.armor+5)
                self.action_text=f"Броня улучшена! Защита: {self.armor}%"; self.action_timer=90
            elif not self.weapon and self.armor==0: self.action_text="Нужно оружие или броня"; self.action_timer=60
            else: self.action_text="Нужно больше денег (150-200)"; self.action_timer=60
        elif b.name=="Банк":
            if self.money>=100:
                self.money-=100; self.debt_paid+=150
                self.action_text="Вложил 100, долг уменьшен на 150!"; self.action_timer=90
            else: self.action_text="Нужно 100 монет"; self.action_timer=60
        elif b.name=="Библиотека":
            if self.money>=10:
                self.money-=10; self.max_energy+=5; self.energy=min(self.energy+10,self.max_energy)
                self.action_text="Прочитал книгу! +5 макс. энергии"; self.action_timer=90
            else: self.action_text="Нужно 10 монет за книгу"; self.action_timer=60
        elif b.name=="Таверна":
            if self.money>=30:
                self.money-=30
                r=random.random()
                if r<0.4: self.money+=80; self.action_text="Выиграл в карты 80 монет!"; self.action_timer=90
                elif r<0.7: self.action_text="Познакомился с NPC... интересно"; self.action_timer=60
                else: self.energy=max(0,self.energy-20); self.action_text="Драка в таверне! -20 энергии"; self.action_timer=90
            else: self.action_text="Нужно 30 монет"; self.action_timer=60
        elif b.name=="Склад":
            bonus=random.randint(3,8)
            self.materials['flower']=self.materials.get('flower',0)+bonus
            self.action_text=f"Нашёл {bonus} цветков на складе!"; self.action_timer=60
    def pay_debt(self):
        if self.money>=50:
            pay=min(50, max(0, self.debt-self.debt_paid))
            if pay<=0: self.action_text="Кредит уже выплачен!"; self.action_timer=60; return
            self.money-=pay; self.debt_paid+=pay
            if self.debt_paid>=self.debt: self.portal_unlocked=True; self.action_text="КРЕДИТ ВЫПЛАЧЕН!"; particles.emit(self.r.centerx,self.r.centery,GOLD,30,(-6,6),40,6)
            else: self.action_text=f"Выплачено {pay}. Осталось: {self.debt-self.debt_paid}"
            self.action_timer=120
        else: self.action_text="Нужно 50 монет!"; self.action_timer=60
    def attack(self,m):
        if self.ac>0: return False
        if self.weapon:
            if self.needs_ammo and self.ammo<=0:
                self.action_text="Нет патронов!"; self.action_timer=45; return False
            dist=math.hypot(self.r.centerx-m.x,self.r.centery-m.y)
            if dist<self.weapon_range:
                if "Газонокосилка" in self.weapon_name: self.ac=30
                elif "Меч" in self.weapon_name: self.ac=25
                elif "Огнемёт" in self.weapon_name: self.ac=35
                elif "Бластер" in self.weapon_name: self.ac=15
                elif "Пушка" in self.weapon_name: self.ac=40
                else: self.ac=25
                if self.needs_ammo: self.ammo-=1
                self.weapon_durability-=1
                if self.weapon_durability<=0:
                    self.weapon=False; self.weapon_damage=0; self.weapon_name="Сломано!"
                    self.action_text="Оружие сломалось!"; self.action_timer=90; return False
                if m.hit(self.weapon_damage): self.money+=m.sc; self.monsters_defeated+=1; self.action_text=f"Побеждён {m.name}!"; self.action_timer=90; return True
                else: self.action_text=f"Попадание!"; self.action_timer=45
            else: self.action_text="Слишком далеко!"; self.action_timer=30
        return False
    def update(self):
        if self.action_timer>0: self.action_timer-=1
        if self.inv_timer>0: self.inv_timer-=1
        if self.ac>0: self.ac-=1
        if self.shield_cd>0: self.shield_cd-=1
        if self.fire_cd>0: self.fire_cd-=1
        if self.heal_cd>0: self.heal_cd-=1
        if self.restaurant_cooldown>0: self.restaurant_cooldown-=1
        if self.shield: self.shield_timer-=1
        if self.shield_timer<=0: self.shield=False

class CollectZone:
    def __init__(self,x,y,w,h,n,c,ipz=8):
        self.r=pygame.Rect(x,y,w,h); self.name=n; self.color=c; self.items=[]; self.max=ipz; self.sc=0; self.special=[]
    def add_special(self,item): self.special.append(item)
    def spawn(self):
        if len(self.items)<self.max and self.sc<=0:
            t=random.choice(['flower']*3+['bug']*2+['mushroom']*2+['golden_grain'])
            self.items.append(Collectible(random.randint(self.r.x+25,self.r.x+self.r.width-25),random.randint(self.r.y+25,self.r.y+self.r.height-25),t))
            self.sc=random.randint(100,250)
    def update(self):
        if self.sc>0: self.sc-=1
        self.items=[i for i in self.items if not i.col]
        if self.name!="Секретная локация": self.spawn()
    def draw(self,s):
        ss=pygame.Surface((self.r.width,self.r.height)); ss.set_alpha(30); ss.fill(self.color); s.blit(ss,(self.r.x,self.r.y))
        pygame.draw.rect(s,self.color,self.r,2); s.blit(get_text(self.name,small_font,self.color),(self.r.x+5,self.r.y+5))
        for i in self.items: i.draw(s)
        for i in self.special: i.draw(s)

class StoryTeller:
    def __init__(self):
        self.messages=["Боб: Где я?","Мистер Греча: Добро пожаловать! Ты должен 10000 монет!",
                       "Мистер Греча: Иди в поля, работай в ресторане.","Мистер Греча: Осторожно — монстры!",
                       "Боб: 10000?! Нужно оружие!","Мистер Греча: В магазине всё есть.",
                       "Боб: Я заработаю!","Совет: Собирай материалы для крафта!",
                       "Совет: Q-щит, R-фаербол, H-лечение."]
        self.mi=0; self.showing=False; self.mt=0; self.text=""; self.undertale_found=False
        self.stage={1:"Боб: Нужно оружие!",2:"Боб: Я сражаюсь!",3:"Греча: Плати кредит!",
                    4:"Греча: 1000 выплачено!",5:"Греча: 3000! Неплохо!",
                    6:"Греча: 6000! Портал светится!",7:"Греча: 9000! Чуть-чуть!"}
        self.st=set()
    def update(self,bob,loc=""):
        if self.mi<len(self.messages) and not self.showing: self.show(self.messages[self.mi],350); self.mi+=1
        if loc=="undertale_ruins" and not self.undertale_found: self.undertale_found=True; self.show("Боб: Это Руины из Undertale!",300)
        if bob.weapon and 1 not in self.st: self.st.add(1); self.show(self.stage[1],300)
        if bob.monsters_defeated>=5 and 2 not in self.st: self.st.add(2); self.show(self.stage[2],300)
        if bob.debt_paid>=100 and 3 not in self.st: self.st.add(3); self.show(self.stage[3],300)
        if bob.debt_paid>=1000 and 4 not in self.st: self.st.add(4); self.show(self.stage[4],300)
        if bob.debt_paid>=3000 and 5 not in self.st: self.st.add(5); self.show(self.stage[5],300)
        if bob.debt_paid>=6000 and 6 not in self.st: self.st.add(6); self.show(self.stage[6],300)
        if bob.debt_paid>=9000 and 7 not in self.st: self.st.add(7); self.show(self.stage[7],350)
        if self.showing: self.mt-=1
        if self.mt<=0: self.showing=False
    def show(self,text,duration=350): self.showing=True; self.mt=duration; self.text=text
    def draw(self,s):
        if self.showing:
            ss=pygame.Surface((WIDTH,100)); ss.set_alpha(200); ss.fill(BLACK); s.blit(ss,(0,HEIGHT-180))
            tx=get_text(self.text,font,WHITE); r=tx.get_rect(center=(WIDTH//2,HEIGHT-130))
            pygame.draw.rect(s,DARK_BG,r.inflate(40,20),border_radius=10); pygame.draw.rect(s,GOLD,r.inflate(40,20),2,border_radius=10)
            s.blit(tx,r)

class MrGrecha:
    def __init__(self,x,y): self.x=x; self.y=y; self.at=0
    def draw(self,s):
        self.at+=0.03; t=self.at; hb=math.sin(t*2)*2; bb=math.sin(t*2)*1.5
        pygame.draw.ellipse(s,(150,150,150),(self.x-18,self.y+32,36,8))
        pygame.draw.line(s,BROWN,(self.x+16,self.y+15),(self.x+26+math.sin(t*3)*3,self.y+35),3)
        pygame.draw.circle(s,GOLD,(int(self.x+26+math.sin(t*3)*3),self.y+35),4)
        pygame.draw.circle(s,BROWN,(self.x,self.y+15+bb),18); pygame.draw.circle(s,(160,120,70),(self.x,self.y+15+bb),14)
        for i in range(3): pygame.draw.circle(s,(180,140,100),(int(self.x-5+i*5+math.sin(t+i)*2),int(self.y+12+bb+math.cos(t+i)*2)),1)
        pygame.draw.ellipse(s,BLACK,(self.x-15,self.y-8+hb,30,12)); pygame.draw.rect(s,BLACK,(self.x-8,self.y-18+hb,16,12)); pygame.draw.rect(s,GOLD,(self.x-8,self.y-8+hb,16,3))
        ey=self.y+10+bb
        if math.sin(t*0.5)>0.95: pygame.draw.line(s,BLACK,(self.x-8,ey),(self.x-2,ey),2); pygame.draw.line(s,BLACK,(self.x+2,ey),(self.x+8,ey),2)
        else: pygame.draw.circle(s,WHITE,(self.x-5,ey),4); pygame.draw.circle(s,WHITE,(self.x+5,ey),4); pygame.draw.circle(s,BLACK,(self.x-5,ey),2); pygame.draw.circle(s,BLACK,(self.x+5,ey),2)

class FinalPortal:
    def __init__(self,x,y): self.r=pygame.Rect(x,y,60,60); self.p=0
    def draw(self,s,unlocked):
        self.p+=0.05; t=self.p; ps=math.sin(t)*5
        if unlocked:
            for r in[40,33,26]:
                a=80+int(math.sin(t+r)*60); c=(min(255,PURPLE[0]+a//2),min(255,PURPLE[1]+a//2),min(255,PURPLE[2]+a))
                pygame.draw.circle(s,c,self.r.center,r+ps)
            for i in range(12): a=t*3+i*0.523; d=25+math.sin(t*5+i)*8; pygame.draw.circle(s,YELLOW,(int(self.r.centerx+math.cos(a)*d),int(self.r.centery+math.sin(a)*d)),int(2+math.sin(t*10+i)))
        else:
            for r in[35,28,21]: pygame.draw.circle(s,GRAY,self.r.center,r)
        pygame.draw.ellipse(s,DARK_BG,self.r); pygame.draw.ellipse(s,PURPLE if unlocked else GRAY,self.r,3)
        s.blit(get_text("🌀" if unlocked else "🔒",big_font,YELLOW if unlocked else WHITE),get_text("🌀" if unlocked else "🔒",big_font,YELLOW if unlocked else WHITE).get_rect(center=self.r.center))

class Location:
    def __init__(self,name,bg):
        self.name=name; self.bg=bg; self.buildings=[]; self.zones=[]; self.monsters=[]
        self.portals=[]; self.at=0; self.undertale=False
        self.monster_spawns=[]
        random.seed(hash(name)%10000)
        self.bushes=[]
        for i in range(12):
            bx=random.randint(50,WIDTH-50); by=random.randint(int(HEIGHT*0.30)+20,HEIGHT-170)
            self.bushes.append((bx,by))
        self.rocks=[]
        for i in range(10):
            rx=random.randint(50,WIDTH-50); ry=random.randint(int(HEIGHT*0.30)+20,HEIGHT-160)
            shade=150+(i%3)*20; w=12+i%8; h=7+i%4
            self.rocks.append((rx,ry,shade,w,h))
        random.seed()
    def add_b(self,b): self.buildings.append(b)
    def add_z(self,z): self.zones.append(z)
    def add_p(self,p): self.portals.append(p)
    def add_monster_spawn(self,monster_type,x,y,patrol_radius=100):
        self.monster_spawns.append((monster_type,x,y,patrol_radius))
    def respawn_monsters(self):
        self.monsters=[]
        for m_type,x,y,pr in self.monster_spawns: self.monsters.append(Monster(x,y,m_type,pr))
    def draw_bg(self,s):
        self.at+=0.005; t=self.at
        s.fill((0,0,0))
        if self.undertale:
            s.fill((30,20,40))
            for y in range(0,HEIGHT,45):
                for x in range(0,WIDTH,70):
                    sh=40+math.sin(x*0.01+y*0.01+t)*10; c=(sh,sh-10,sh+20); pygame.draw.rect(s,c,(x,y,68,43)); pygame.draw.rect(s,(20,15,30),(x,y,68,43),1)
            for i in range(0,WIDTH,20): pygame.draw.rect(s,DARK_GREEN,(i,HEIGHT-80,18,12+math.sin(i*0.1+t)*4))
            return
        sky_h=int(HEIGHT*0.30); s.fill(self.bg,(0,0,WIDTH,sky_h))
        for i in range(5):
            cx=(i*350+t*10)%(WIDTH+200)-100; cy=30+i*35
            if cy<sky_h:
                for dx,dy,r in[(0,0,20),(18,5,16),(-16,8,14)]: pygame.draw.circle(s,(245,245,250),(int(cx+dx),int(cy+dy)),r)
        hr=min(255,self.bg[0]+15); hg=min(255,self.bg[1]+10); hb=min(255,self.bg[2]+5)
        pygame.draw.rect(s,(hr,hg,hb),(0,sky_h,WIDTH,3))
        gt=sky_h; gb=HEIGHT-150
        gr=max(0,self.bg[0]-25); gg=max(0,self.bg[1]-25); gb2=max(0,self.bg[2]-15)
        gc=(gr,gg,gb2)
        pygame.draw.rect(s,gc,(0,gt,WIDTH,gb-gt))
        pc=(210,195,170)
        for py in[gt+80,gt+250,gt+420]:
            if py<gb-30: pygame.draw.rect(s,pc,(0,py,WIDTH,25)); pygame.draw.rect(s,(180,165,140),(0,py,WIDTH,3)); pygame.draw.rect(s,(180,165,140),(0,py+22,WIDTH,3))
        for x in range(0,WIDTH,8):
            h=6+math.sin(x*0.05+t)*3; pygame.draw.line(s,GREEN,(x,gt),(x+3,gt-h),1)
        for i,(bx,by) in enumerate(self.bushes):
            sw=math.sin(t*2+i)*2
            for dx,dy,r in[(0,0,10),(6,-2,8),(-5,-3,7)]: pygame.draw.circle(s,(40,150,40),(int(bx+dx+sw),int(by+dy)),r)
        for rx,ry,shade,w,h in self.rocks: pygame.draw.ellipse(s,(shade,shade,shade),(rx,ry,w,h))
        dr=min(255,gc[0]+15); dg=min(255,gc[1]+15); db=min(255,gc[2]+5)
        pygame.draw.rect(s,(dr,dg,db),(0,gb,WIDTH,150))

def create_locations():
    locs={}
    so=int(HEIGHT*0.30)
    ms=Location("Главная площадь",(180,210,240))
    for b in[Building(60,so+60,160,95,GREEN,"Дом","🏠"),
             Building(60,so+180,160,95,RED,"Ресторан","🍽️"),
             Building(60,so+300,160,95,BLUE,"Магазин","🛒"),
             Building(60,so+420,160,95,ORANGE,"Кузница","🔨"),
             Building(250,so+60,140,90,TEAL,"Банк","🏦"),
             Building(250,so+180,140,90,LIME,"Библиотека","📚"),
             Building(250,so+300,140,90,(200,160,160),"Таверна","🍺"),
             Building(250,so+420,140,90,(200,180,150),"Склад","📦")]: ms.add_b(b)
    for p in[LocationPortal(1400,so+50,"flower_field","Цветочное поле",PINK),
             LocationPortal(1400,so+170,"bug_forest","Жучиный лес",GREEN),
             LocationPortal(1400,so+290,"mushroom_glade","Грибная поляна",ORANGE),
             LocationPortal(1400,so+410,"dark_valley","Тёмная долина",RED)]: ms.add_p(p)
    locs["main"]=ms
    ff=Location("Цветочное поле",(255,235,245))
    ff.add_z(CollectZone(200,so+20,500,250,"Цветы",PINK,10)); ff.add_z(CollectZone(800,so+20,500,250,"Редкие цветы",PINK,8))
    ff.add_p(LocationPortal(700,so+350,"main","На главную площадь",BLUE)); ff.add_p(LocationPortal(1400,so+150,"undertale_ruins","???",YELLOW))
    ff.add_monster_spawn("slug",350,so+150,180); ff.add_monster_spawn("slug",1000,so+150,180); ff.add_monster_spawn("weed",700,so+300,130)
    ff.respawn_monsters()
    locs["flower_field"]=ff
    bf=Location("Жучиный лес",(230,245,230))
    bf.add_z(CollectZone(200,so+20,500,250,"Жуки",GREEN,8)); bf.add_z(CollectZone(800,so+20,500,250,"Лесные жуки",GREEN,7))
    bf.add_p(LocationPortal(700,so+350,"main","На главную площадь",BLUE))
    bf.add_monster_spawn("beetle",350,so+150,200); bf.add_monster_spawn("beetle",950,so+200,200); bf.add_monster_spawn("slug",700,so+100,130)
    bf.respawn_monsters()
    locs["bug_forest"]=bf
    mg=Location("Грибная поляна",(240,230,210))
    mg.add_z(CollectZone(200,so+20,500,250,"Грибы",ORANGE,7)); mg.add_z(CollectZone(800,so+20,500,250,"Тёмные грибы",ORANGE,6))
    mg.add_p(LocationPortal(700,so+350,"main","На главную площадь",BLUE))
    mg.add_monster_spawn("weed",400,so+150,160); mg.add_monster_spawn("weed",900,so+250,160); mg.add_monster_spawn("slug",350,so+350,130); mg.add_monster_spawn("boss_cricket",1000,so+80,220)
    mg.respawn_monsters()
    locs["mushroom_glade"]=mg
    dv=Location("Тёмная долина",(50,45,60))
    dv.add_z(CollectZone(200,so+50,400,200,"Редкие руды",PURPLE,5)); dv.add_z(CollectZone(700,so+50,400,200,"Тёмные кристаллы",MAGENTA,4))
    dv.add_p(LocationPortal(700,so+350,"main","На главную площадь",BLUE))
    dv.add_monster_spawn("mutant_grain",350,so+150,180); dv.add_monster_spawn("mutant_grain",850,so+200,180); dv.add_monster_spawn("boss_cricket",600,so+100,180); dv.add_monster_spawn("grecha_demon",700,so+350,220)
    dv.respawn_monsters()
    locs["dark_valley"]=dv
    ur=Location("Руины (Undertale)",(30,20,40)); ur.undertale=True
    uz=CollectZone(200,so+30,500,300,"Золотые цветы",YELLOW,0)
    for _ in range(25): uz.add_special(Collectible(random.randint(250,650),random.randint(so+50,so+300),'undertale_flower'))
    ur.add_z(uz); ur.add_monster_spawn("flowey",800,so+150,0); ur.respawn_monsters()
    ur.add_p(LocationPortal(700,so+380,"flower_field","Вернуться в поле",BLUE))
    locs["undertale_ruins"]=ur
    return locs

class Minimap:
    def __init__(self): self.size=140; self.m=8
    def draw(self,s,loc,bob):
        mx=WIDTH-self.size-self.m; my=HEIGHT-self.size-100
        ss=pygame.Surface((self.size,self.size)); ss.set_alpha(180); ss.fill((30,30,30)); s.blit(ss,(mx,my))
        pygame.draw.rect(s,WHITE,(mx,my,self.size,self.size),2)
        sx=self.size/WIDTH; sy=self.size/HEIGHT
        for b in loc.buildings: pygame.draw.rect(s,b.color,(mx+b.r.x*sx,my+b.r.y*sy,max(2,b.r.width*sx),max(2,b.r.height*sy)))
        for p in loc.portals: pygame.draw.circle(s,p.color,(int(mx+p.r.x*sx),int(my+p.r.y*sy)),3)
        for m in loc.monsters: pygame.draw.circle(s,RED,(int(mx+m.x*sx),int(my+m.y*sy)),2)
        pygame.draw.circle(s,YELLOW,(int(mx+bob.r.centerx*sx),int(my+bob.r.centery*sy)),3)

minimap=Minimap()

def main():
    global locations
    locations=create_locations(); cl=locations["main"]
    so=int(HEIGHT*0.30)
    bob=Bob(750,so+200); mr=MrGrecha(1400,so-20); fp=FinalPortal(1400,so+470)
    story=StoryTeller(); sw=ShopWindow(); iw=InventoryWindow(); hw=HelpWindow()
    gom=GameOverMenu(); vm=VictoryMenu()
    sd=load_game()
    if sd:
        try:
            bob.money=sd.get("money",20); bob.energy=sd.get("energy",100); bob.max_energy=sd.get("max_energy",100)
            bob.debt=sd.get("debt",10000); bob.debt_paid=sd.get("debt_paid",0)
            bob.weapon=sd.get("weapon",False); bob.weapon_damage=sd.get("weapon_damage",0)
            bob.weapon_name=sd.get("weapon_name","Нет"); bob.armor=sd.get("armor",0)
            bob.speed_boost=sd.get("speed_boost",0); bob.speed=4+bob.speed_boost
            bob.monsters_defeated=sd.get("monsters_defeated",0)
            bob.weapon_durability=sd.get("weapon_durability",0); bob.weapon_max_durability=sd.get("weapon_max_durability",0)
            bob.weapon_range=sd.get("weapon_range",55); bob.ammo=sd.get("ammo",0)
            bob.ammo_type=sd.get("ammo_type",""); bob.needs_ammo=sd.get("needs_ammo",False)
            cl=locations.get(sd.get("location","main"),locations["main"])
            story.mi=sd.get("story_index",0); story.st=set(sd.get("story_triggers",[]))
            story.undertale_found=sd.get("undertale",False)
            if sd.get("achievements"):
                for i,u in enumerate(sd["achievements"]):
                    if i<len(achievements.achievements): achievements.achievements[i].unlocked=u
            night_system.is_night=sd.get("night",False)
        except: pass
    else: story.show(story.messages[0],350); story.mi=1
    ic=0; running=True; go=False; win=False; ta=0; tr=False
    while running:
        dt=clock.tick(60)
        for e in pygame.event.get():
            if e.type==pygame.QUIT:
                if not go and not win: save_game(bob,cl.name,story)
                running=False
            elif e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE:
                    if gom.active or vm.active: gom.active=False; vm.active=False; running=False
                    else:
                        if not go and not win: save_game(bob,cl.name,story); bob.action_text="Сохранено!"; bob.action_timer=60
                        running=False
                if gom.active:
                    if e.key==pygame.K_UP: gom.sel=max(0,gom.sel-1)
                    elif e.key==pygame.K_DOWN: gom.sel=min(1,gom.sel+1)
                    elif e.key==pygame.K_RETURN:
                        if gom.sel==0: locations=create_locations(); cl=locations["main"]; bob=Bob(750,so+200); story=StoryTeller(); go=False; gom.active=False; ta=255; tr=True
                        else: running=False
                elif vm.active:
                    if e.key==pygame.K_UP: vm.sel=max(0,vm.sel-1)
                    elif e.key==pygame.K_DOWN: vm.sel=min(1,vm.sel+1)
                    elif e.key==pygame.K_RETURN:
                        if vm.sel==0: vm.active=False
                        else: running=False
                elif not go and not win:
                    if sw.active:
                        if e.key==pygame.K_TAB: sw.tab=1-sw.tab; sw.sel=0
                        elif e.key==pygame.K_UP: sw.sel=max(0,sw.sel-1)
                        elif e.key==pygame.K_DOWN: items=CRAFT_RECIPES if sw.tab==1 else SHOP_ITEMS; sw.sel=min(len(items)-1,sw.sel+1)
                        elif e.key==pygame.K_RETURN:
                            if sw.tab==0: sw.buy(bob,SHOP_ITEMS[sw.sel])
                            else: sw.craft(bob,CRAFT_RECIPES[sw.sel])
                        elif e.key==pygame.K_e: sw.close()
                    elif iw.active:
                        if e.key in[pygame.K_i,pygame.K_e]: iw.close()
                    elif hw.active:
                        if e.key==pygame.K_F1 or e.key==pygame.K_e: hw.close()
                    else:
                        if e.key==pygame.K_q: bob.use_ability("shield",cl.monsters)
                        elif e.key==pygame.K_r: bob.use_ability("fireball",cl.monsters)
                        elif e.key==pygame.K_h: bob.use_ability("heal",cl.monsters)
                        elif e.key==pygame.K_F1: hw.open()
                        elif e.key==pygame.K_SPACE: bob.pay_debt()
                        elif e.key==pygame.K_e:
                            if trader.active and bob.r.colliderect(trader.r): bob.money+=100; bob.action_text="+100!"; bob.action_timer=60; trader.active=False; particles.emit(trader.x,trader.y,GOLD,15,(-3,3),20,4)
                            elif bob.r.colliderect(pygame.Rect(60,so+300,160,95)) and cl.name=="Главная площадь": sw.open()
                            else:
                                for p in cl.portals:
                                    if bob.r.colliderect(p.r): cl=locations[p.target]; cl.respawn_monsters(); bob.r.x=WIDTH//2; bob.r.y=so+200; story.show(f"Переход: {cl.name}",250); ta=255; tr=True; break
                                else:
                                    if bob.ac<=0:
                                        att=False
                                        for m in cl.monsters:
                                            if math.hypot(bob.r.centerx-m.x,bob.r.centery-m.y)<50:
                                                if m.type=="flowey": story.show("Flowey: Howdy!",250); att=True; break
                                                if bob.attack(m): cl.monsters.remove(m)
                                                att=True; break
                                        if not att:
                                            for b in cl.buildings:
                                                if bob.r.colliderect(b.r) and b.name in["Дом","Ресторан","Кузница","Банк","Библиотека","Таверна","Склад"]: bob.interact(b); break
                        elif e.key==pygame.K_i: iw.open()
                        elif e.key==pygame.K_F5: save_game(bob,cl.name,story); bob.action_text="Сохранено!"; bob.action_timer=60
        if not go and not win and not sw.active and not iw.active and not gom.active and not vm.active and not hw.active:
            keys=pygame.key.get_pressed(); bob.move(keys)
            night_system.update(); trader.update(cl.name)
            for m in cl.monsters: m.move(bob.r,(0,so,WIDTH,HEIGHT-130-so)); m.attack(bob)
            for z in cl.zones:
                for i in z.items:
                    if i.check(bob.r): bob.collect(i)
                for i in z.special:
                    if i.check(bob.r): bob.collect(i)
                z.update()
            ic-=1
            if ic<=0:
                for b in cl.buildings:
                    if bob.r.colliderect(b.r) and b.name in["Дом","Ресторан","Кузница","Банк","Библиотека","Таверна","Склад"]: bob.interact(b); ic=120; break
            bob.update(); story.update(bob,cl.name); sw.update(); particles.update()
            achievements.check(bob,story); achievements.update()
            if tr: ta=max(0,ta-5)
            if ta==0: tr=False
            if bob.energy<=0: go=True; gom.show()
            if bob.r.colliderect(fp.r) and bob.portal_unlocked and cl.name=="Главная площадь": win=True; vm.show()
        cl.draw_bg(screen)
        dark=night_system.get_darkness()
        if dark>0: ds=pygame.Surface((WIDTH,HEIGHT)); ds.set_alpha(dark); ds.fill((10,10,40)); screen.blit(ds,(0,0))
        for z in cl.zones: z.draw(screen)
        for b in cl.buildings: b.draw(screen)
        for p in cl.portals: p.draw(screen)
        for m in cl.monsters: m.draw(screen)
        if cl.name=="Главная площадь": fp.draw(screen,bob.portal_unlocked)
        if not go and not win: bob.draw(screen)
        if cl.name=="Главная площадь": mr.draw(screen); trader.draw(screen)
        particles.draw(screen)
        tx=get_text(cl.name,big_font,BLACK if not cl.undertale else WHITE); r=tx.get_rect(center=(WIDTH//2,30))
        bc=WHITE if not cl.undertale else (50,30,60); pygame.draw.rect(screen,bc,r.inflate(25,12),border_radius=8)
        pygame.draw.rect(screen,GOLD if cl.undertale else BLACK,r.inflate(25,12),2,border_radius=8); screen.blit(tx,r)
        story.draw(screen); sw.draw(screen,bob); iw.draw(screen,bob); hw.draw(screen)
        achievements.draw(screen); gom.draw(screen); vm.draw(screen); minimap.draw(screen,cl,bob)
        screen.blit(get_text("🌙 Ночь" if night_system.is_night else "☀️ День",small_font,YELLOW if night_system.is_night else GOLD),(WIDTH-170,10))
        if not go and not win:
            panel=pygame.Rect(0,HEIGHT-80,WIDTH,80); pygame.draw.rect(screen,DARK_BG,panel); pygame.draw.rect(screen,WHITE,panel,2)
            dl=bob.debt-bob.debt_paid
            if dl<=1000: dc=GOLD
            elif dl<=3000: dc=YELLOW
            elif dl<=6000: dc=ORANGE
            else: dc=WHITE
            for txt,col,pos in[(f"Долг:{dl}/{bob.debt}",dc,(15,HEIGHT-70)),(f"Монеты:{bob.money}",YELLOW,(15,HEIGHT-45)),
                               (f"Энергия:{int(bob.energy)}/{bob.max_energy}",WHITE,(300,HEIGHT-58)),(f"Прочность:{bob.weapon_durability}/{bob.weapon_max_durability}",CYAN,(500,HEIGHT-58)),
                               (f"Оружие:{bob.weapon_name}",GOLD if bob.weapon else GRAY,(700,HEIGHT-58)),(f"Защита:{bob.armor}%",BLUE if bob.armor>0 else GRAY,(920,HEIGHT-58))]:
                screen.blit(get_text(txt,font,col),pos)
            if bob.needs_ammo: screen.blit(get_text(f"Патроны:{bob.ammo}",font,ORANGE),(1120,HEIGHT-58))
            if bob.weapon:
                if bob.ac>0: cdt=f"КД:{bob.ac/60:.1f}с"; cdc=GRAY
                else: cdt="Готов!"; cdc=GREEN
            else: cdt="Нет оружия"; cdc=RED
            screen.blit(get_text(cdt,font,cdc),(1350,HEIGHT-58))
            screen.blit(get_text(f"Q-щит:{max(0,int(bob.shield_cd/60))}с R-огонь:{max(0,int(bob.fire_cd/60))}с H-хил:{max(0,int(bob.heal_cd/60))}с",tiny_font,CYAN),(1120,HEIGHT-40))
            if bob.action_text: screen.blit(get_text(bob.action_text,font,ORANGE),(15,HEIGHT-20))
            for i,h in enumerate(["WASD-ход|E-действие|I-инвентарь|F1-помощь|SPACE-платить","Q-щит|R-фаербол|H-лечение|F5-сохранить"]): screen.blit(get_text(h,small_font,(200,200,200)),(WIDTH-500,HEIGHT-70+i*18))
        if tr: ts=pygame.Surface((WIDTH,HEIGHT)); ts.set_alpha(ta); ts.fill(BLACK); screen.blit(ts,(0,0))
        pygame.display.flip()
    pygame.quit(); sys.exit()

if __name__=="__main__": main()
