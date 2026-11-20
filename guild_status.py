"""Guild state from full-card evidence or a visible disabled title and check."""
from functools import lru_cache
import cv2
from detect_activity import ROOT, read_image, detect
from guild_daily import detect_guild


@lru_cache(maxsize=32)
def template(name):
    return cv2.cvtColor(read_image(ROOT / f"assets/templates/{name}.png"), cv2.COLOR_BGR2GRAY)


def reference(frame):
    h, w = frame.shape[:2]
    if abs(w/h - 1.6) > 0.01:
        raise ValueError("Expected 16:10 game capture.")
    return cv2.cvtColor(cv2.resize(frame, (2048, 1280), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)


def match(gray, name, roi):
    x1, y1, x2, y2 = roi
    x1, y1, x2, y2 = max(0,x1), max(0,y1), min(2048,x2), min(1280,y2)
    area, t = gray[y1:y2,x1:x2], template(name)
    h,w = t.shape
    if area.shape[0] < h or area.shape[1] < w:
        return 0.0, (0,0,w,h)
    _,score,_,(x,y) = cv2.minMaxLoc(cv2.matchTemplate(area,t,cv2.TM_CCOEFF_NORMED))
    return float(score),(x+x1,y+y1,w,h)


def activity_page(frame):
    gray=reference(frame)
    return min(match(gray,"activities_heading",(110,20,310,110))[0],
               match(gray,"activities_tab",(105,195,365,280))[0]) >= .90


def guild_active(frame):
    return match(reference(frame),"guild_active",(35,245,330,700))[0] >= .85


def world_visible(frame):
    return (detect(frame,read_image(ROOT/"assets/templates/activity.png"))[0] >= .85
            or match(reference(frame),"world_objectives",(350,240,650,340))[0] >= .90)


def guild_state(frame):
    if not activity_page(frame):
        return {"state":"unknown"}
    gray=reference(frame)
    title,(x,y,w,h)=match(gray,"guild_done_title",(95,295,1285,1000))
    # Below y=1030, the activity reward strip obscures the list.
    if title >= .90 and y+150 <= 1030:
        one,_=match(gray,"guild_one",(x+85,y+98,x+249,y+153))
        check,_=match(gray,"guild_check",(x+355,y+35,x+490,y+155))
        if min(one,check)>=.90:
            sx,sy=frame.shape[1]/2048,frame.shape[0]/1280
            return {"state":"completed","score":min(title,one,check),
                    "evidence":"title_one_check",
                    "title_box":[round(x*sx),round(y*sy),round(w*sx),round(h*sy)]}
    # Bottom card may be permanently hidden behind the reward strip. Require
    # the disabled Guild title AND 50 rows of the check (including its diagonal
    # stroke), not merely a grey card or the absence of a Go button.
    if title >= .95 and y+150 > 1030:
        t=template("guild_check")[:50]
        best=0.0
        for top in range(y+40,y+54):
            if top+50 > 1030:
                continue
            area=gray[top:top+50,x+355:min(x+490,2048)]
            if area.shape[1] < t.shape[1]:
                continue
            score=cv2.minMaxLoc(cv2.matchTemplate(area,t,cv2.TM_CCOEFF_NORMED))[1]
            best=max(best,float(score))
        if best >= .95:
            sx,sy=frame.shape[1]/2048,frame.shape[0]/1280
            return {"state":"completed","score":min(title,best),
                    "evidence":"disabled_guild_title_and_visible_check_top",
                    "title_box":[round(x*sx),round(y*sy),round(w*sx),round(h*sy)]}
        return {"state":"guild_card_obscured","score":title,
                "note":"Guild title visible; completion evidence insufficient."}
    try:
        score,box=detect_guild(frame)
    except RuntimeError:
        return {"state":"not_visible_or_unverified"}
    # Do not act on a partially occluded bottom card.
    if box[1]+box[3] > 1030*frame.shape[0]/1280:
        return {"state":"not_visible_or_unverified"}
    return {"state":"pending","score":score,"go_box":box}
