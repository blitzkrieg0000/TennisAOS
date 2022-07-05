import random
import numpy as np
from sympy import Line
import cv2

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
        canvas_image_skt = cv2.line(canvas_image_skt, (int(line[0]), int(line[1])), (int(line[2]), int(line[3])), (100, 100, 100), 2, cv2.LINE_AA) 
    return canvas_image_skt

def drawExtraPolly(points_dict:dict, canvas_image_skt):
    shapes = np.zeros_like(canvas_image_skt, np.uint8)

    for i,key in enumerate(points_dict.keys()):
        points = np.array(points_dict[key], np.int32)
        shapes = cv2.fillPoly(shapes, [points], colors[i], 1)
    
    alpha = 0.5
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


def line_intersection(line1, line2):
    """İki çizginin kesişim noktalarını bul"""
    l1 = Line((line1[0],line1[1]), (line1[2],line1[3]))
    l2 = Line((line2[0],line2[1]), (line2[2],line2[3]))

    intersection = l1.intersection(l2)
    return intersection[0].coordinates

def extractSpecialLines(courtLines, canvas_image_skt):
    
    # Çizgilerin başlangıç noktası sol-üste yakın olan olacak şekilde ayarla
    for i, item in enumerate(courtLines):
        courtLines[i] = reorderLines(item)

    # YER VURUŞU DERİNLİĞİ
    tbl = courtLines[0]                         # Üst servis çizgisi
    bbl = courtLines[1]                         # Alt servis çizgisi
    nt = courtLines[2]                          # File Çizgisi
    lcl = courtLines[3]                         # Sol çizgi
    rcl = courtLines[4]                         # Sağ çizgi
    lil = courtLines[5]                         # Sol iç çizgi
    ril = courtLines[6]                         # Sağ iç çizgi
    ml = courtLines[7]                          # Orta Çizgisi
    til = courtLines[8]                         # Üst iç çizgi
    bil = courtLines[9]                         # Alt iç çizgi
    tisl = [ lil[0], lil[1], ril[0], ril[1] ]   # Üst iç servis çizgisi
    bisl = [ lil[2], lil[3], ril[2], ril[3] ]   # Alt iç servis çizgisi
    right_inner_net = line_intersection(nt, ril)
    left_inner_net = line_intersection(nt, lil)

    inl = [ left_inner_net[0], left_inner_net[1], right_inner_net[0], right_inner_net[1] ] # İç file çizgisi

    til_mid = getLineMidPoint(til)
    inl_mid = getLineMidPoint(inl)


    #! 1-) YER-VOLE VURUŞU DERİNLİĞİ ALANLARI
    line_data = {}
    line_data['net_line'] = nt
    line_data["top_inner_line"] = til
    line_data["top_inner_service_line"] = tisl
    line_data["left_inner_near_net_line"] = [ left_inner_net[0], left_inner_net[1], til[0], til[1] ]
    line_data["right_inner_near_net_line"] = [ right_inner_net[0], right_inner_net[1], til[2], til[3] ]
    line_data["left_top_short_line"] = [ lil[0], lil[1], til[0], til[1] ]
    line_data["right_top_short_line"] = [ ril[0], ril[1], til[2], til[3] ]
    line_data["middle_top_line"] = [ til_mid[0], til_mid[1], inl_mid[0], inl_mid[1] ]
    line_data["point_line_1"] = [ *getLinePointWithRatio(line_data["left_top_short_line"], 0.33), *getLinePointWithRatio(line_data["right_top_short_line"], 0.33) ] #4p - 3p
    line_data["point_line_2"] = [ *getLinePointWithRatio(line_data["left_top_short_line"], (2/3)), *getLinePointWithRatio(line_data["right_top_short_line"], (2/3)) ] #3p-2p

    point_area_data = {}
    point_area_data["area_4"] = [ lil[:2], ril[:2], line_data["point_line_1"][2:], line_data["point_line_1"][:2] ]
    point_area_data["area_3"] = [ line_data["point_line_1"][:2], line_data["point_line_1"][2:], line_data["point_line_2"][2:],  line_data["point_line_2"][:2] ]
    point_area_data["area_2"] = [ line_data["point_line_2"][:2], line_data["point_line_2"][2:], til[2:], til[:2] ]
    point_area_data["area_1"] = [ til[:2], til[2:], (right_inner_net[0], right_inner_net[1]), (left_inner_net[0], left_inner_net[1]) ]


    #! 2-) YER VURUŞU HASSASİYETİ
    



    




    canvas_image_skt = drawExtraPolly(point_area_data, canvas_image_skt)
    canvas_image_skt = drawExtraLine(line_data, canvas_image_skt)

    # Test: İşaretlemek için
    # canvas_image_skt = cv2.circle(canvas_image_skt, (int(lil[0]), int(lil[1])),5, (255,255,255), -1)
    return line_data, point_area_data, canvas_image_skt