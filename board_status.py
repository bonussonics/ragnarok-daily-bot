"""Read-only Quest Board observations in physical screenshot coordinates."""
from guild_status import reference, match, activity_page


def board_state(frame):
    gray = reference(frame)
    sx, sy = frame.shape[1]/2048, frame.shape[0]/1280
    def result(state, score, box=None):
        r = {'state': state, 'score': float(score)}
        if box:
            x,y,w,h = box
            r['box'] = [round(x*sx),round(y*sy),round(w*sx),round(h*sy)]
        return r
    heading,_ = match(gray,'board_heading',(110,20,330,110))
    dialog,_ = match(gray,'board_confirm_heading',(790,285,1260,410))
    body,_ = match(gray,'board_confirm_body',(550,510,1500,700))
    confirm,box = match(gray,'board_confirm',(1020,810,1510,970))
    # The long Thai label scrolls horizontally. Match both stationary rims,
    # requiring their relative geometry as well as the modal heading/body.
    top,tbox = match(gray,'board_confirm_rim_top',(1055,820,1490,890))
    bottom,bbox = match(gray,'board_confirm_rim_bottom',(1055,905,1490,975))
    aligned = abs(tbox[0]-bbox[0]) <= 3 and abs(bbox[1]-tbox[1]-87) <= 3
    if aligned and min(top,bottom) >= .90:
        confirm = min(top,bottom)
        box = (tbox[0],tbox[1],tbox[2],114)
    if min(heading,dialog,body,confirm) >= .90:
        return result('confirm',min(heading,dialog,body,confirm),box)
    start,box = match(gray,'board_start',(790,975,1260,1130))
    if min(heading,start) >= .90 and dialog < .80:
        return result('start',min(heading,start),box)
    if not activity_page(frame):
        return result('board_waiting' if heading >= .90 else 'unknown',heading)
    # Title, count and action must all be inside the same card.
    candidates = []
    for name in ('board_done_title','board_card_title'):
        title,(x,y,w,h) = match(gray,name,(95,290,1290,1010))
        if title < .90 or y+160 > 1030:
            continue
        one = max(match(gray,n,(x+80,y+95,x+255,y+160))[0] for n in ('guild_one','board_one','board_one_live'))
        check,_ = match(gray,'guild_check',(x+350,y+30,x+500,y+160))
        candidates.append({'title_score': title, 'one_score': one, 'check_score': check})
        if min(one,check) >= .90:
            return result('completed',min(title,one,check))
        zero,_ = match(gray,'guild_zero',(x+80,y+95,x+255,y+160))
        go,box = match(gray,'guild_go',(x+305,y+60,x+525,y+160))
        if min(zero,go) >= .90:
            return result('pending',min(title,zero,go),box)
    r = result('not_visible_or_unverified',0)
    r['card_candidates'] = candidates
    return r
