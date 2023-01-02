import random
import numpy as np
import cv2
from libs.courtDetector import CourtDetector

EPS = np.finfo(float).eps
RANDOM_COLOR = lambda : (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

colors = []
for x in range(4):
    colors.append(RANDOM_COLOR()) 


def isVertical(line) -> bool:
    """
    else horizontal or diagonal 
    Params:
        line -> [P1x, P1y, P2x, P2y]
    """
    return (abs(line[3]-line[1]) > abs(line[2]-line[0]))


def reorderLines(line):
    """
    İlk nokta, sol ve üstte kalacak şekilde yeniden noktayı düzenle
    Params:
        line -> [P1x, P1y, P2x, P2y]
    """
    axis = 1 if isVertical(line) else 0
    line = [line[:2], line[2:]]
    x1, y1 = min(line, key=lambda item:item[axis])
    x2, y2 = max(line, key=lambda item:item[axis])
    return [x1, y1, x2, y2]


def drawExtraLine(data:dict, canvas_image_skt):
    for key in data.keys():
        line = data[key] 
        canvas_image_skt = cv2.line(canvas_image_skt, (int(line[0]), int(line[1])), (int(line[2]), int(line[3])), (255, 255, 255), 2, cv2.LINE_AA) 
    return canvas_image_skt


def drawExtraPolly(points_dict:dict, canvas_image_skt):
    shapes = np.zeros_like(canvas_image_skt, np.uint8)

    for i,key in enumerate(points_dict.keys()):
        points = np.array(points_dict[key], np.int32)
        
        canvas_image_skt = cv2.fillPoly(canvas_image_skt, [points], colors[i], 1)

        alpha = 0.8
        mask = shapes.astype(bool)
        canvas_image_skt[mask] = cv2.addWeighted(canvas_image_skt, alpha, shapes, 1 - alpha, 0)[mask]
     
    return canvas_image_skt


def getLinePointWithRatio(line, ratio=0.5):
    x1, y1, x2, y2 = line
    m = (y2-y1)/((x2-x1)+EPS)
    len_y = (y2-y1)
    point_y = y1+len_y*ratio
    point_x = ((point_y-y1)/(m+EPS)) + x1
    return (point_x, point_y)


def getPointOnLine(line, xx=None, yy=None):
    m = (line[3]-line[1]) / ((line[2]-line[0])+EPS)
    if yy is None:
        f = lambda x: ((x-line[0])*m + line[1])
        return f(xx)
    elif xx is None:
        f = lambda y: ((y-line[1]) / (m+EPS))+line[0]
        return f(yy)
    else:
        raise "İki değer birden sağlanamaz!"


def getLineMidPoint(line):
    point = ( int((line[0] + line[2])/2), int((line[1] + line[3])/2) )
    return point


def extractSpecialLines(court_detector:CourtDetector, canvas_image_skt):
    line_data = {}
    bil = reorderLines(court_detector.bottom_inner_line) # Alt iç çizgi
    til = reorderLines(court_detector.top_inner_line)    # Üst iç çizgi
    lil = reorderLines(court_detector.left_inner_line)   # Sol iç çizgi
    ril = reorderLines(court_detector.right_inner_line)  # Sağ iç çizgi

    left_net_inner = getLineMidPoint([ til[0], til[1], bil[0], bil[1] ])
    right_net_inner = getLineMidPoint([ til[2], til[3], bil[2], bil[3] ])

    line_data['net'] = (getPointOnLine(court_detector.left_court_line,yy=left_net_inner[1]), left_net_inner[1], getPointOnLine(court_detector.right_court_line, yy=right_net_inner[1]), right_net_inner[1]) # Net(Tenis Filesi) çizgisinin en dış çizgiden başlaması için
    line_data["left_top_short_line"] = [ lil[0], lil[1], til[0], til[1] ]
    line_data["right_top_short_line"] = [ ril[0], ril[1], til[2], til[3] ]
    line_data["point_line_1"] = (*getLinePointWithRatio(line_data["left_top_short_line"], 0.33), *getLinePointWithRatio(line_data["right_top_short_line"], 0.33) ) #4p - 3p
    line_data["point_line_2"] = (*getLinePointWithRatio(line_data["left_top_short_line"], (2/3)), *getLinePointWithRatio(line_data["right_top_short_line"], (2/3)) ) #3p-2p

    point_area_data = {}
    point_area_data['area_4'] = [ lil[:2], ril[:2], line_data["point_line_1"][2:], line_data["point_line_1"][:2]]
    point_area_data['area_3'] = [ line_data["point_line_1"][:2], line_data["point_line_1"][2:], line_data["point_line_2"][2:],  line_data["point_line_2"][:2]]
    point_area_data['area_2'] = [ line_data["point_line_2"][:2], line_data["point_line_2"][2:], til[2:], til[:2] ]
    point_area_data['area_1'] = [ til[:2], til[2:], right_net_inner, left_net_inner]

    canvas_image_skt = drawExtraPolly(point_area_data, canvas_image_skt)
    canvas_image_skt = drawExtraLine(line_data, canvas_image_skt)
    #canvas_image_skt = cv2.circle(canvas_image_skt, (int(lil[0]), int(lil[1])),5, (255,255,255), -1)
    return line_data, point_area_data, canvas_image_skt