"""Find Guild Daily 0/1 and Go within the same card; click Go only."""
import cv2
from detect_activity import ROOT, read_image


def detect_guild(frame, unused=None):
    height, width = frame.shape[:2]
    if abs(width / height - 1.6) > 0.01:
        raise ValueError("Guild detection requires 16:10 capture.")
    reference = cv2.resize(frame, (2048, 1280), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
    def match(area, name):
        template = cv2.cvtColor(read_image(ROOT / f"assets/templates/{name}.png"), cv2.COLOR_BGR2GRAY)
        if area.shape[0] < template.shape[0] or area.shape[1] < template.shape[1]:
            return 0.0, (0, 0), template.shape
        result = cv2.matchTemplate(area, template, cv2.TM_CCOEFF_NORMED)
        _, score, _, point = cv2.minMaxLoc(result)
        return score, point, template.shape
    score, (tx, ty), _ = match(gray[300:1010, 80:1290], "guild_title")
    tx, ty = tx + 80, ty + 300
    if score < 0.90:
        raise RuntimeError("Guild title not found. Open daily activities first; no click.")
    # Require BOTH incomplete count and Go inside this title's card.
    zero, _, _ = match(gray[ty+102:ty+156, tx+85:tx+249], "guild_zero")
    go, (gx, gy), (gh, gw) = match(gray[ty+65:ty+151, tx+310:tx+519], "guild_go")
    if min(zero, go) < 0.90:
        raise RuntimeError("Guild 0/1 and Go not both verified. May be completed/obscured; no click.")
    x, y = tx + 310 + gx, ty + 65 + gy
    sx, sy = width / 2048, height / 1280
    x1, y1 = round(x*sx), round(y*sy)
    return float(min(score, zero, go)), (x1, y1, round((x+gw)*sx)-x1, round((y+gh)*sy)-y1)


if __name__ == "__main__":
    from open_activity import main
    main(task="guild")
