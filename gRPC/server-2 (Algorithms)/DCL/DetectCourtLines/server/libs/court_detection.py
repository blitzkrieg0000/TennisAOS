from http.client import ImproperConnectionState
from itertools import combinations

import cv2
import numpy as np
from sympy import Line
from libs.court_reference import CourtReference
import logging
class CourtDetector():
    def __init__(self):
        self.court_reference = CourtReference()
        self.colour_threshold = 200
        self.dist_tau = 3
        self.intensity_threshold = 40
        self.v_width = 0
        self.v_height = 0
        self.frame = None
        self.gray = None
        self.court_warp_matrix = []
        self.game_warp_matrix = []
        self.court_score = 0
        self.baseline_top = None
        self.baseline_bottom = None
        self.net = None
        self.left_court_line = None
        self.right_court_line = None
        self.left_inner_line = None
        self.right_inner_line = None
        self.middle_line = None
        self.top_inner_line = None
        self.bottom_inner_line = None
        self.success_flag = False
        self.success_accuracy = 80
        self.success_score = 1000
        self.best_conf = None
        self.frame_points = None
        self.dist = 5
        self.saved_lines = []

    def detect(self, frame):
        """Sahayı Tespit Et"""
        self.frame = frame
        self.v_height, self.v_width = frame.shape[:2]
        
        # Threshold
        self.gray = self._threshold(frame)

        # Bilinen saha yapısını kullanarak filtreleme işlemi yap
        filtered = self._filter_pixels(self.gray)

        # Hough Transform kullanarak çizgileri tespit et
        horizontal_lines, vertical_lines = self._detect_lines(filtered)
        
        for x in horizontal_lines:
            frame = cv2.line(frame, (x[0],x[1]), (x[2],x[3]), (52, 255,52), 2)
        
        for x in vertical_lines:
            frame = cv2.line(frame, (x[0],x[1]), (x[2],x[3]), (52, 255,52), 2)

        # Homografileri bul
        court_warp_matrix, game_warp_matrix, self.court_score = self._find_homography(horizontal_lines, vertical_lines)
        self.court_warp_matrix.append(court_warp_matrix)
        self.game_warp_matrix.append(game_warp_matrix)
        court_accuracy = self._get_court_accuracy()
        
        if court_accuracy > self.success_accuracy and self.court_score > self.success_score:
            self.success_flag = True
        logging.info('Saha tespit doğruluğu(accuracy):  = %.4f' % court_accuracy)
        
        # Önemli çizgileri bul
        self.find_lines_location()
        return frame

    def _threshold(self, frame):
        """Threshold Uygula ve Beyaz Kenarları Çıkart"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)[1]
        return gray

    def _filter_pixels(self, gray):
        """Saha yapısına uygun olanları seç"""
        for i in range(self.dist_tau, len(gray) - self.dist_tau): #1080
            for j in range(self.dist_tau, len(gray[0]) - self.dist_tau): #1920
                if gray[i, j] == 0:
                    continue
                if (gray[i, j] - gray[i + self.dist_tau, j] > self.intensity_threshold and
                        gray[i, j] - gray[i - self.dist_tau, j] > self.intensity_threshold):
                    continue

                if (gray[i, j] - gray[i, j + self.dist_tau] > self.intensity_threshold and
                        gray[i, j] - gray[i, j - self.dist_tau] > self.intensity_threshold):
                    continue
                gray[i, j] = 0
        return gray

    def _detect_lines(self, gray):
        """Hough transform ile tüm olası çizgi noktalarını bul"""
        minLineLength = 100
        maxLineGap = 20
        
        # Tüm çizgileri tespit et
        lines = cv2.HoughLinesP(gray, 1, np.pi / 180, 80, minLineLength=minLineLength, maxLineGap=maxLineGap)
        lines = np.squeeze(lines)

        # Eğimlerini karşılaştırarak çizgileri sınıfla
        horizontal, vertical = self._classify_lines(lines)

        # Aynı doğrultu üzerindeki küçük çizgileri birleştir
        horizontal, vertical = self._merge_lines(horizontal, vertical)

        return horizontal, vertical

    def _classify_lines(self, lines):
        """Yatay ve Dikey çizgileri sınıfla"""
        horizontal = []
        vertical = []
        highest_vertical_y = np.inf
        lowest_vertical_y = 0
        for line in lines:
            x1, y1, x2, y2 = line
            dx = abs(x1 - x2)
            dy = abs(y1 - y2)
            if dx > 2 * dy:
                horizontal.append(line)
            else:
                vertical.append(line)
                highest_vertical_y = min(highest_vertical_y, y1, y2)
                lowest_vertical_y = max(lowest_vertical_y, y1, y2)

        # Dikey çizgileri kullanarak yatay çizgilerin sınırlarını filtrele yani dikey çizgilerin arasında kalan çizgileri(yatay çizgileri) al
        clean_horizontal = []
        h = lowest_vertical_y - highest_vertical_y
        lowest_vertical_y += h / 15
        highest_vertical_y -= h * 2 / 15
        for line in horizontal:
            x1, y1, x2, y2 = line
            #Eğer En yüksek ve En düşük noktalar arasındaysa yatay çizgileri çiz
            if lowest_vertical_y > y1 > highest_vertical_y and lowest_vertical_y > y2 > highest_vertical_y:
                clean_horizontal.append(line)
        return clean_horizontal, vertical

    def _classify_vertical(self, vertical, width):
        """Dikey çizgileri sağ ve sol dikey çizgilere göre sınıflandır"""
        vertical_lines = []
        vertical_left = []
        vertical_right = []
        right_th = width * 4 / 7
        left_th = width * 3 / 7
        for line in vertical:
            x1, y1, x2, y2 = line
            if x1 < left_th or x2 < left_th:
                vertical_left.append(line)
            elif x1 > right_th or x2 > right_th:
                vertical_right.append(line)
            else:
                vertical_lines.append(line)
        return vertical_lines, vertical_left, vertical_right

    def _merge_lines(self, horizontal_lines, vertical_lines):
        """
        Aynı doğrultudaki çizgileri birleştir
        """

        # Yatay çizgileri birleştir
        horizontal_lines = sorted(horizontal_lines, key=lambda item: item[0])
        mask = [True] * len(horizontal_lines)
        
        new_horizontal_lines = []
        for i, line in enumerate(horizontal_lines):
            if mask[i]:
                for j, s_line in enumerate(horizontal_lines[i + 1:]):
                    if mask[i + j + 1]:
                        x1, y1, x2, y2 = line
                        x3, y3, x4, y4 = s_line
                        dy = abs(y3 - y2)
                        if dy < 10:
                            points = sorted([(x1, y1), (x2, y2), (x3, y3), (x4, y4)], key=lambda x: x[0])
                            line = np.array([*points[0], *points[-1]])
                            mask[i + j + 1] = False
                new_horizontal_lines.append(line)

        # Dikey çizgileri birleştir
        vertical_lines = sorted(vertical_lines, key=lambda item: item[1])
        xl, yl, xr, yr = (0, self.v_height * 6 / 7, self.v_width, self.v_height * 6 / 7)
        mask = [True] * len(vertical_lines)
        new_vertical_lines = []
        for i, line in enumerate(vertical_lines):
            if mask[i]:
                for j, s_line in enumerate(vertical_lines[i + 1:]):
                    if mask[i + j + 1]:
                        x1, y1, x2, y2 = line
                        x3, y3, x4, y4 = s_line
                        xi, yi = line_intersection(((x1, y1), (x2, y2)), ((xl, yl), (xr, yr)))
                        xj, yj = line_intersection(((x3, y3), (x4, y4)), ((xl, yl), (xr, yr)))

                        dx = abs(xi - xj)
                        if dx < 10:
                            points = sorted([(x1, y1), (x2, y2), (x3, y3), (x4, y4)], key=lambda x: x[1])
                            line = np.array([*points[0], *points[-1]])
                            mask[i + j + 1] = False

                new_vertical_lines.append(line)
        return new_horizontal_lines, new_vertical_lines

    def _find_homography(self, horizontal_lines, vertical_lines):
        """4 tane eşleşen noktadan referans sahayı çıkart"""
        max_score = -np.inf
        max_mat = None
        max_inv_mat = None
        k = 0
        # 4 tane kesişim bulmak için tüm olası yatay ve çizgilerin kombinasyonlarını kullan 
        for horizontal_pair in list(combinations(horizontal_lines, 2)):
            for vertical_pair in list(combinations(vertical_lines, 2)):
                h1, h2 = horizontal_pair
                v1, v2 = vertical_pair
                # Kesişim noktalarını çıkart
                i1 = line_intersection((tuple(h1[:2]), tuple(h1[2:])), (tuple(v1[0:2]), tuple(v1[2:])))
                i2 = line_intersection((tuple(h1[:2]), tuple(h1[2:])), (tuple(v2[0:2]), tuple(v2[2:])))
                i3 = line_intersection((tuple(h2[:2]), tuple(h2[2:])), (tuple(v1[0:2]), tuple(v1[2:])))
                i4 = line_intersection((tuple(h2[:2]), tuple(h2[2:])), (tuple(v2[0:2]), tuple(v2[2:])))

                intersections = [i1, i2, i3, i4]
                intersections = sort_intersection_points(intersections)

                for i, configuration in self.court_reference.court_conf.items():
                    #Bulunan tüm yatay ve dikey çizgilerden elde edilen tüm olası kesişimleri manuel belirlenen court structure harita yapısına göre Homography Matrisi bulunur.
                    
                    # Homografi matrisini bul
                    matrix, mask = cv2.findHomography(np.float32(configuration), np.float32(intersections), method=0)
                    inv_matrix = cv2.invert(matrix)[1]

                    # Dönüşüme puan ver
                    confi_score = self._get_confi_score(matrix)

                    if max_score < confi_score:
                        max_score = confi_score
                        max_mat = matrix
                        max_inv_mat = inv_matrix
                        self.best_conf = i
                    k += 1

        logging.info(f'Puan = {max_score}')
        logging.info(f'{k} Kombinasyon Test Edildi.')

        return max_mat, max_inv_mat, max_score

    def _get_confi_score(self, matrix):
        """
        -> Bulunan bu matrislerin homograpy matrisleri referans saha ile işleme tabi tutularak,
        referans matris gerilir ve yeni bir şekil elde edilir.
        -> Elde edilen yeni şekil, kenarı çıkartılan filtrelenmiş saha resmi ile farkına bakılarak,
        eşleşme oranları aşağıdak, gibi ölçülür.
        """

        # M1 = M2 x HomograpyMatrix: Bulunan homography matrisi ile orijinal referans alınan resim işleme girerek yeni bir gerilmiş resim elde edilir.
        # Bulunan court çizgileri ile uyuşup uyuşmadığına ise aşağıdaki işlemler yapılarak bir puan yardımıyla bakılır.
        court = cv2.warpPerspective(self.court_reference.court, matrix, self.frame.shape[1::-1])

        #Resim sadece 1 ve 0 lardan oluşması için
        court[court > 0] = 1    
        gray = self.gray.copy()
        gray[gray > 0] = 1      

        #Uyuşan değerler iki resim nokta çarpımı yapılarak üst üste binen değerler bulunur. 1*0 = 0 ve 1*1 = 1 mantığı ile
        correct = court * gray  #Örtüşen kısım da kalan 1 sayısı
        wrong = court - correct  #Örtüşmeyen kısımda kalan 1 sayısı
        c_p = np.sum(correct)
        w_p = np.sum(wrong)

        #Toplam hata: (DOĞRU - 0.5 * YANLIŞ)
        #Yanlışların sayısı 0.5 katsayı ile çarpılarak yanlışlara tolerans tanınır.
        return c_p - 0.5 * w_p

    def add_court_overlay(self, frame, homography=None, overlay_color=(255, 255, 255), frame_num=-1):
        if homography is None and len(self.court_warp_matrix) > 0 and frame_num < len(self.court_warp_matrix):
            homography = self.court_warp_matrix[frame_num]
        court = cv2.warpPerspective(self.court_reference.court, homography, frame.shape[1::-1])
        frame[court > 0, :] = overlay_color
        return frame

    def find_lines_location(self):
        """Önemli çizgileri bul"""
        p = np.array(self.court_reference.get_important_lines(), dtype=np.float32).reshape((-1, 1, 2))
        lines = cv2.perspectiveTransform(p, self.court_warp_matrix[-1]).reshape(-1)
        self.baseline_top = lines[:4]
        self.baseline_bottom = lines[4:8]
        self.net = lines[8:12]
        self.left_court_line = lines[12:16]
        self.right_court_line = lines[16:20]
        self.left_inner_line = lines[20:24]
        self.right_inner_line = lines[24:28]
        self.middle_line = lines[28:32]
        self.top_inner_line = lines[32:36]
        self.bottom_inner_line = lines[36:40]
        for x in range(4,41,4):
            self.saved_lines.append(lines[x-4: x])

    def get_extra_parts_location(self, frame_num=-1):
        parts = np.array(self.court_reference.get_extra_parts(), dtype=np.float32).reshape((-1, 1, 2))
        parts = cv2.perspectiveTransform(parts, self.court_warp_matrix[frame_num]).reshape(-1)
        top_part = parts[:2]
        bottom_part = parts[2:]
        return top_part, bottom_part

    def delete_extra_parts(self, frame, frame_num=-1):
        img = frame.copy()
        top, bottom = self.get_extra_parts_location(frame_num)
        img[int(bottom[1] - 10):int(bottom[1] + 10), int(bottom[0] - 15):int(bottom[0] + 15), :] = (0, 0, 0)
        img[int(top[1] - 10):int(top[1] + 10), int(top[0] - 15):int(top[0] + 15), :] = (0, 0, 0)
        return img

    def get_warped_court(self):
        """Sahanın homografi matrisini kullarak, "self.court_reference.court" u çarpıt"""
        court = cv2.warpPerspective(self.court_reference.court, self.court_warp_matrix[-1], self.frame.shape[1::-1])
        court[court > 0] = 1
        return court

    def _get_court_accuracy(self):
        """Sahanın accuracysini tespitten sonra bul"""
        frame = self.frame.copy()
        gray = self._threshold(frame)
        gray[gray > 0] = 1

        gray = cv2.dilate(gray, np.ones((9, 9), dtype=np.uint8))
        court = self.get_warped_court()
        total_white_pixels = sum(sum(court))
        sub = court.copy()
        sub[gray == 1] = 0
        accuracy = 100 - (sum(sum(sub)) / total_white_pixels) * 100

        return accuracy

    def track_court(self, frame, cimage):
        """Saha çizgilerini takip et"""
        copy = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.frame_points is None:
            conf_points = np.array(self.court_reference.court_conf[self.best_conf], dtype=np.float32).reshape((-1, 1, 2))
            self.frame_points = cv2.perspectiveTransform(conf_points, self.court_warp_matrix[-1]).squeeze().round()
        
        # Saha çizgileri
        line1 = self.frame_points[:2]
        line2 = self.frame_points[2:4]
        line3 = self.frame_points[[0, 2]]
        line4 = self.frame_points[[1, 3]]
        lines = [line1, line2, line3, line4]

        new_lines = []
        for line in lines:
            # Her köşenin arasına 100 adet nokta belirle
            points_on_line = np.linspace(line[0], line[1], 102)[1:-1]  # 100 samples on the line

            # Resmin sınırlarında olan noktaları sağdan ve soldan bul.
            p1 = None
            p2 = None
            if line[0][0] > self.v_width or line[0][0] < 0 or line[0][1] > self.v_height or line[0][1] < 0:
                for p in points_on_line:
                    if 0 < p[0] < self.v_width and 0 < p[1] < self.v_height:
                        p1 = p
                        break

            if line[1][0] > self.v_width or line[1][0] < 0 or line[1][1] > self.v_height or line[1][1] < 0:
                for p in reversed(points_on_line):
                    if 0 < p[0] < self.v_width and 0 < p[1] < self.v_height:
                        p2 = p
                        break

            # Resmin içinde kalan noktaları alır.
            if p1 is not None or p2 is not None:
                logging.info('points outside screen')
                points_on_line = np.linspace(p1 if p1 is not None else line[0], p2 if p2 is not None else line[1], 102)[1:-1]

            new_points = []
            # Her bir noktanın piksel yoğunluğunu ölç
            for p in points_on_line:
                p = (int(round(p[0])), int(round(p[1])))

                top_y, top_x = max(p[1] - self.dist, 0), max(p[0] - self.dist, 0)
                bottom_y, bottom_x = min(p[1] + self.dist, self.v_height), min(p[0] + self.dist, self.v_width)

                patch = gray[top_y: bottom_y, top_x: bottom_x]
                # Matrisimiz 10x10 olduğu için y,x konumu düz bir dizideki index numarasıyla aynı oluyor.
                y, x = np.unravel_index(np.argmax(patch), patch.shape)
                #imgray = gray.copy()
                if patch[y, x] > 150:
                    new_p = (x + top_x + 1, y + top_y + 1)
                    new_points.append(new_p)
                    
                    #imgray = cv2.circle(imgray, p, 1, (0, 0, 0), 1)
                    #imgray = cv2.circle(imgray, new_p, 1, (0, 0, 255), 1)

                #random_rgb = (int(random.random()*255), int(random.random()*255), int(random.random()*255))
                #imgray = cv2.rectangle(imgray, (top_x, top_y), (bottom_x-1, bottom_y-1), random_rgb, 1)
                #cv2.imshow("",imgray)
                #cv2.waitKey(0)  

            new_points = np.array(new_points, dtype=np.float32).reshape((-1, 1, 2))
            # find line fitting the new points
            [vx, vy, x, y] = cv2.fitLine(new_points, cv2.DIST_L2, 0, 0.01, 0.01)
            new_lines.append(((int(x - vx * self.v_width), int(y - vy * self.v_width)),
                              (int(x + vx * self.v_width), int(y + vy * self.v_width))))

            # if less than 50 points were found detect court from the start instead of tracking
            if len(new_points) < 50:
                if self.dist > 20:
                    cv2.imshow('court', copy)
                    if cv2.waitKey(0) & 0xff == 27:
                        cv2.destroyAllWindows()
                    self.detect(frame)
                    conf_points = np.array(self.court_reference.court_conf[self.best_conf], dtype=np.float32).reshape((-1, 1, 2))
                    self.frame_points = cv2.perspectiveTransform(conf_points, self.court_warp_matrix[-1]).squeeze().round()

                    logging.info('Smaller than 50')
                    return
                else:
                    logging.info('Court tracking failed, adding 5 pixels to dist')
                    self.dist += 5
                    cimage = self.track_court(frame, cimage)
                    return

        # Find transformation from new lines
        i1 = line_intersection(new_lines[0], new_lines[2])
        i2 = line_intersection(new_lines[0], new_lines[3])
        i3 = line_intersection(new_lines[1], new_lines[2])
        i4 = line_intersection(new_lines[1], new_lines[3])
        intersections = np.array([i1, i2, i3, i4], dtype=np.float32)
        matrix, _ = cv2.findHomography(np.float32(self.court_reference.court_conf[self.best_conf]), intersections, method=0)
        inv_matrix = cv2.invert(matrix)[1]
        self.court_warp_matrix.append(matrix)
        self.game_warp_matrix.append(inv_matrix)
        self.frame_points = intersections

        #DRAW LINES
        for court_conf in self.court_reference.court_conf.values():
            conf_points = np.array(court_conf, dtype=np.float32).reshape((-1, 1, 2))
            lines = cv2.perspectiveTransform(conf_points, self.court_warp_matrix[-1]).squeeze().round()
            #line = [ [ 578.  303.] [1330.  302.] [ 366.  855.] [1559.  853.] ]
            line1 = lines[:2]     #[ [ 578.  303.] [1330.  302.] ]
            line2 = lines[2:4]
            line3 = lines[[0, 2]]
            line4 = lines[[1, 3]]

            drawlines = [line1, line2, line3, line4]
            for line in drawlines:
                cimage = cv2.line(cimage, ( int(line[0][0]), int(line[0][1]) ), ( int(line[1][0]), int(line[1][1]) ), (66, 245, 102), 3)
        
        #Çizgileri Güncelle
        self.find_lines_location()
        return cimage


def sort_intersection_points(intersections):
    """Kesişim değerlerini sol üstten, sağ alta doğru sırala"""
    y_sorted = sorted(intersections, key=lambda x: x[1])
    p12 = y_sorted[:2]
    p34 = y_sorted[2:]
    p12 = sorted(p12, key=lambda x: x[0])
    p34 = sorted(p34, key=lambda x: x[0])
    return p12 + p34

def line_intersection(line1, line2):
    """İki çizginin kesişim noktalarını bul"""
    l1 = Line(line1[0], line1[1])
    l2 = Line(line2[0], line2[1])

    intersection = l1.intersection(l2)
    return intersection[0].coordinates

def display_lines_on_frame(frame, horizontal=(), vertical=()):
    """Noktaları çiz"""

    for line in horizontal:
        x1, y1, x2, y2 = line
        cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.circle(frame, (x1, y1), 1, (255, 0, 0), 2)
        cv2.circle(frame, (x2, y2), 1, (255, 0, 0), 2)

    for line in vertical:
        x1, y1, x2, y2 = line
        cv2.line(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.circle(frame, (x1, y1), 1, (255, 0, 0), 2)
        cv2.circle(frame, (x2, y2), 1, (255, 0, 0), 2)

    cv2.imshow('court', frame)
    if cv2.waitKey(0) & 0xff == 27:
        cv2.destroyAllWindows()
    return frame

def display_lines_and_points_on_frame(frame, lines=(), points=(), line_color=(0, 0, 255), point_color=(255, 0, 0)):
    """Tüm çizgi ve noktaları göster"""

    for line in lines:
        x1, y1, x2, y2 = line
        frame = cv2.line(frame, (x1, y1), (x2, y2), line_color, 2)
    for p in points:
        frame = cv2.circle(frame, p, 2, point_color, 2)

    cv2.imshow('court', frame)
    if cv2.waitKey(0) & 0xff == 27:
        cv2.destroyAllWindows()
    return frame