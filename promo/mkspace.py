import sys, random
from PIL import Image, ImageDraw, ImageFilter
W,H=960,1280;im=Image.new('RGB',(W,H));d=ImageDraw.Draw(im)
for y in range(H):
    t=y/H;d.line([(0,y),(W,y)],fill=(int(12+40*t),int(10+18*t),int(48+60*t)))
random.seed(3)
for _ in range(260):
    x,y=random.randrange(W),random.randrange(H);r=random.choice([1,1,1,2,2,3]);c=random.randint(170,255);d.ellipse([x-r,y-r,x+r,y+r],fill=(c,c,255))
glow=Image.new('RGB',(W,H));g=ImageDraw.Draw(glow);g.ellipse([520,120,880,480],fill=(120,60,200));glow=glow.filter(ImageFilter.GaussianBlur(60))
im=Image.blend(im,Image.composite(glow,im,Image.new('L',(W,H),255)),0.35);d=ImageDraw.Draw(im)
d.ellipse([560,160,840,440],fill=(100,150,255));d.ellipse([600,190,820,420],fill=(120,175,255))
d.arc([480,260,920,340],200,340,fill=(255,210,120),width=10)
d.ellipse([90,240,170,320],fill=(255,200,90))
im.save(sys.argv[1])
