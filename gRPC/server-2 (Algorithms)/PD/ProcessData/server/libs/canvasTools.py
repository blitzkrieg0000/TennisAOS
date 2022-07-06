import random
import numpy as np
import collections
from sympy import Line
import cv2

EPS = np.finfo(float).eps

class ColorManager():
    def __init__(self):
        self._colorSets = collections.defaultdict()
        self.RANDOM_COLOR = lambda : (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    def listColorSets(self):
        return list(self._colorSets.keys())

    def getColorSet(self, name):
        try : return self._colorSets[str(name)]
        except: return [self.RANDOM_COLOR()]

    def setRandomColorSet(self, name, q):
        if q>0: self._colorSets[str(name)] = [self.RANDOM_COLOR() for _ in range(q)]

    def setColorSet(self, name, arr: list):
        """ Color array must like that: [(255, 255, 255), (0, 0, 0), (120, 150, 180)...]"""
        self._colorSets[str(name)] = arr

    def deleteColorSet(self, name):
        try: self._colorSets.pop(name)
        except: pass

colorManager = ColorManager()
colorManager.setRandomColorSet("AOS_1", 10)
colorManager.setRandomColorSet("AOS_2", 10)

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

def drawExtraLine(data:dict, canvas, lineColor=(145, 35, 128)):

    for key in data.keys():
        line = data[key] 
        canvas = cv2.line(canvas, (int(line[0]), int(line[1])), (int(line[2]), int(line[3])), lineColor, 2, cv2.LINE_AA) 
    return canvas

def drawExtraPolly(points_dict:dict, canvas):
    shapes = np.zeros_like(canvas, np.uint8)
    colors = colorManager.getColorSet("AOS_2")
    
    for i, key in enumerate(points_dict.keys()):
        points = np.array(points_dict[key], np.int32)
        shapes = cv2.fillPoly(shapes, [points], colors[i], 1)
    
    alpha = 0.5
    mask = shapes.astype(bool)
    canvas[mask] = cv2.addWeighted(canvas, alpha, shapes, 1 - alpha, 0)[mask]
     
    return canvas

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

def extractSpecialLocations(courtLines, canvas, AOS_TYPE:int=1):
    # Çizgilerin başlangıç noktası sol-üste yakın olan olacak şekilde ayarla
    for i, item in enumerate(courtLines):
        courtLines[i] = reorderLines(item)

    # YER VURUŞU DERİNLİĞİ
    tbl = courtLines[0]                         # Üst base çizgisi
    bbl = courtLines[1]                         # Alt base çizgisi
    nl = courtLines[2]                          # File Çizgisi
    lcl = courtLines[3]                         # Sol çizgi
    rcl = courtLines[4]                         # Sağ çizgi
    lil = courtLines[5]                         # Sol iç çizgi
    ril = courtLines[6]                         # Sağ iç çizgi
    ml = courtLines[7]                          # Orta Çizgisi
    til = courtLines[8]                         # Üst iç çizgi
    bil = courtLines[9]                         # Alt iç çizgi
    tibl = [ lil[0], lil[1], ril[0], ril[1] ]   # Üst iç base çizgisi
    bibl = [ lil[2], lil[3], ril[2], ril[3] ]   # Alt iç base çizgisi
    rin = line_intersection(nl, ril)            #* Sağ iç file çizgisi noktası
    lin = line_intersection(nl, lil)            #* Sol iç file çizgisi noktası
    inl = [ lin[0], lin[1], rin[0], rin[1] ]    # İç file çizgisi
    til_mid = getLineMidPoint(til)
    inl_mid = getLineMidPoint(inl)

    if AOS_TYPE==1:
    #! 1-) YER-VOLE VURUŞU DERİNLİĞİ ALANLARI
        line_data = {}
        line_data['net_line'] = inl
        line_data["top_inner_line"] = til
        line_data["top_inner_base_line"] = tibl
        line_data["left_inner_near_net_line"] = [ til[0], til[1], lin[0], lin[1]]
        line_data["right_inner_near_net_line"] = [ til[2], til[3], rin[0], rin[1]]
        line_data["left_top_short_line"] = [ lil[0], lil[1], til[0], til[1] ]
        line_data["right_top_short_line"] = [ ril[0], ril[1], til[2], til[3] ]
        line_data["middle_top_line"] = [ til_mid[0], til_mid[1], inl_mid[0], inl_mid[1] ]
        line_data["point_line_1"] = [ *getLinePointWithRatio(line_data["left_top_short_line"], 0.33), *getLinePointWithRatio(line_data["right_top_short_line"], 0.33) ] #4p - 3p
        line_data["point_line_2"] = [ *getLinePointWithRatio(line_data["left_top_short_line"], (2/3)), *getLinePointWithRatio(line_data["right_top_short_line"], (2/3)) ] #3p-2p

        point_area_data = {}
        point_area_data["aos_1_area_5"] = [ lil[:2], ril[:2], line_data["point_line_1"][2:], line_data["point_line_1"][:2] ]
        point_area_data["aos_1_area_4"] = [ line_data["point_line_1"][:2], line_data["point_line_1"][2:], line_data["point_line_2"][2:],  line_data["point_line_2"][:2] ]
        point_area_data["aos_1_area_3"] = [ line_data["point_line_2"][:2], line_data["point_line_2"][2:], til[2:], til[:2] ]
        point_area_data["aos_1_area_2"] = [ line_data["middle_top_line"][:2], til[2:], line_data["right_inner_near_net_line"][2:], line_data["middle_top_line"][2:] ]        
        point_area_data["aos_1_area_1"] = [ til[:2], line_data["middle_top_line"][:2], line_data["middle_top_line"][2:], inl[:2] ]

    elif AOS_TYPE==2: 
        #! 2-) YER VURUŞU HASSASİYETİ
        line_data = {}
        line_data["point_line_1"] = [  *getLinePointWithRatio(tibl, 0.25), *getLinePointWithRatio(inl, 0.25) ] #4p - 3p
        line_data["point_line_2"] = [  *getLinePointWithRatio(tibl, 0.75), *getLinePointWithRatio(inl, 0.75) ] #3p-2p
        line_data["right_inner_near_net_line"] = [ tibl[2], tibl[3], rin[0], rin[1] ]
        line_data["left_inner_near_net_line"] = [ tibl[0], tibl[1], lin[0], lin[1] ]
        line_data["top_inner_base_line"] = tibl
        line_data["inner_net"] = inl
        line_data["top_inner_line"] = til

        point_area_data = {}
        lcross = line_intersection(line_data["point_line_1"], til)
        rcross = line_intersection(line_data["point_line_2"], til)
        point_area_data["aos_2_area_6"] = [ tibl[:2], line_data["point_line_1"][:2], lcross, til[:2] ]
        point_area_data["aos_2_area_5"] = [ line_data["point_line_1"][:2], line_data["point_line_2"][:2], rcross, lcross ]
        point_area_data["aos_2_area_4"] = [ line_data["point_line_2"][:2], tibl[2:], til[2:], rcross ]
        point_area_data["aos_2_area_3"] = [ rcross, til[2:], inl[2:], line_data["point_line_2"][2:] ]
        point_area_data["aos_2_area_2"] = [ lcross, rcross, line_data["point_line_2"][2:], line_data["point_line_1"][2:] ]
        point_area_data["aos_2_area_1"] = [ til[:2], lcross, line_data["point_line_1"][2:], inl[:2] ]
    
    elif AOS_TYPE==3:
    #! 3-) SERVİS VURUŞU HASSASİYETİ
        line_data = {}
        line_data["point_line_1"] = [  *getLinePointWithRatio(til, 0.25), *getLinePointWithRatio(inl, 0.25) ] #4p - 3p
        line_data["point_line_2"] = [  *getLinePointWithRatio(til, 0.75), *getLinePointWithRatio(inl, 0.75) ] #3p-2p
        line_data["right_inner_short_near_net_line"] = [ til[2], til[3], rin[0], rin[1] ]
        line_data["left_inner_short_near_net_line"] = [ til[0], til[1], lin[0], lin[1] ]
        line_data["middle_top_short_near_net_line"] = [ ml[0], ml[1], *line_intersection(inl, ml)  ]
        line_data["inner_net"] = inl
        line_data["top_inner_line"] = til
        
        point_area_data = {}
        lcross = line_intersection(line_data["point_line_1"], til)
        rcross = line_intersection(line_data["point_line_2"], til)
        point_area_data["aos_3_area_4"] = [ rcross, til[2:], inl[2:], line_data["point_line_2"][2:] ]
        point_area_data["aos_3_area_3"] = [ line_data["point_line_1"][:2], line_data["middle_top_short_near_net_line"][:2], line_data["middle_top_short_near_net_line"][2:], line_data["point_line_1"][2:] ]
        point_area_data["aos_3_area_2"] = [ line_data["middle_top_short_near_net_line"][:2], line_data["point_line_2"][:2], line_data["point_line_2"][2:], line_data["middle_top_short_near_net_line"][2:] ]
        point_area_data["aos_3_area_1"] = [ til[:2], lcross, line_data["point_line_1"][2:], inl[:2] ]


    canvas = drawExtraPolly(point_area_data, canvas)
    canvas = drawExtraLine(line_data, canvas)

    # Test: İşaretlemek için
    # canvas = cv2.circle(canvas, (int(lil[0]), int(lil[1])),5, (255,255,255), -1)
    return line_data, point_area_data, canvas


"""
        AOS Testi Oyuncunun yeterliliğini puanlamak için gerekli olup ITF tarafından standart haline getirilmiş bir testtir.
    AOS Testi (eğitimci-hakem) tarafından yapılmaktadır. Test esnasında oyuncunun hareketleri ve tenis atışı kamera(lar)
    yardımıyla kaydedilip bu görüntülerdeki her bir kareden, yapay zeka tabanlı görüntü işleme modelleri kullanılarak topun 
    yörüngesi, oyuncu pozisyonları, oyuncu uzuv hareketleri ve tenis sahası bilgileri çıkarılıp bu bilgilerden derin öğrenme, 
    sinyal işleme vb. yöntemler ile oyuncunun test esnasında yapmış olduğu efor analiz edilerek, insan unsurunun
    katılmadığı tarafsız bir puanlama sağlanması amaçlanmaktadır. Aynı zamanda oyuncunun raket vuruşlarını, attığı topun karşı
    sahada nereye düştüğünü, giden topun yörüngesini, test sonunda görsel olarak izleyip nerede eksiği varsa kendini geliştirmesine
    yardımcı olacak karar destek sistemli yazılımlardır.
"""