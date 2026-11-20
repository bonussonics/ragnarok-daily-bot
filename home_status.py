"""Home entry detection. Uniform scaling preserves both 16:9 and 16:10 UI."""
from functools import lru_cache
import cv2
import numpy as np
from detect_activity import ROOT, read_image


@lru_cache(maxsize=8)
def template(name):
    return cv2.cvtColor(read_image(ROOT/'assets/templates'/f'{name}.png'), cv2.COLOR_BGR2GRAY)


def home_state(frame):
    h,w=frame.shape[:2]
    if not 1.5 <= w/h <= 1.9:
        return {'state':'unsupported_aspect'}
    scale=w/1920
    gray=cv2.cvtColor(cv2.resize(frame,(1920,round(h/scale))),cv2.COLOR_BGR2GRAY)
    nh=gray.shape[0]
    def find(name,roi):
        x,y,r,b=roi
        crop=gray[y:b,x:r]
        best=(0.,[0,0,0,0])
        for s in np.arange(.80,1.261,.02):
            t=cv2.resize(template(name),None,fx=float(s),fy=float(s))
            th,tw=t.shape
            if crop.shape[0]<th or crop.shape[1]<tw: continue
            _,score,_,pos=cv2.minMaxLoc(cv2.matchTemplate(crop,t,cv2.TM_CCOEFF_NORMED))
            if score>best[0]:
                best=(float(score),[round(v*scale) for v in (x+pos[0],y+pos[1],tw,th)])
        return best
    heading=find('home_heading',(70,0,350,150))
    back=find('home_return',(1450,int(nh*.70),1920,nh))
    if min(heading[0],back[0])>=.90:
        return {'state':'return_home','score':min(heading[0],back[0]),'box':back[1]}
    menu=find('home_menu',(1450,int(nh*.55),1900,int(nh*.96)))
    if menu[0]>=.93:
        return {'state':'home_menu','score':menu[0],'box':menu[1]}
    return {'state':'not_visible_or_unverified','score':max(menu[0],back[0])}
