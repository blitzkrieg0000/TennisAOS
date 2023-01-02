import cv2
import numpy as np

from libs.helper import CWD


class CourtReference():
    """Court reference model"""
    def __init__(self):
        self.baseline_top = ((286, 561), (1379, 561))
        self.baseline_bottom = ((286, 2935), (1379, 2935))
        self.net = ((286, 1748), (1379, 1748))
        self.left_court_line = ((286, 561), (286, 2935))
        self.right_court_line = ((1379, 561), (1379, 2935))
        self.left_inner_line = ((423, 561), (423, 2935))
        self.right_inner_line = ((1242, 561), (1242, 2935))
        self.middle_line = ((832, 1110), (832, 2386))
        self.top_inner_line = ((423, 1110), (1242, 1110))
        self.bottom_inner_line = ((423, 2386), (1242, 2386))
        self.top_extra_part = (832.5, 580)
        self.bottom_extra_part = (832.5, 2910)

        self.court_conf = {1: [*self.baseline_top, *self.baseline_bottom],
                           2: [self.left_inner_line[0], self.right_inner_line[0], self.left_inner_line[1],
                               self.right_inner_line[1]],
                           3: [self.left_inner_line[0], self.right_court_line[0], self.left_inner_line[1],
                               self.right_court_line[1]],
                           4: [self.left_court_line[0], self.right_inner_line[0], self.left_court_line[1],
                               self.right_inner_line[1]],
                           5: [*self.top_inner_line, *self.bottom_inner_line],
                           6: [*self.top_inner_line, self.left_inner_line[1], self.right_inner_line[1]],
                           7: [self.left_inner_line[0], self.right_inner_line[0], *self.bottom_inner_line],
                           8: [self.right_inner_line[0], self.right_court_line[0], self.right_inner_line[1],
                               self.right_court_line[1]],
                           9: [self.left_court_line[0], self.left_inner_line[0], self.left_court_line[1],
                               self.left_inner_line[1]],
                           10: [self.top_inner_line[0], self.middle_line[0], self.bottom_inner_line[0],
                                self.middle_line[1]],
                           11: [self.middle_line[0], self.top_inner_line[1], self.middle_line[1],
                                self.bottom_inner_line[1]],
                           12: [*self.bottom_inner_line, self.left_inner_line[1], self.right_inner_line[1]]}
        self.line_width = 1
        self.court_width = 1117
        self.court_height = 2408
        self.top_bottom_border = 549
        self.right_left_border = 274
        self.court_total_width = self.court_width + self.right_left_border * 2
        self.court_total_height = self.court_height + self.top_bottom_border * 2

        self.court = cv2.cvtColor(cv2.imread(CWD() + "/court_configurations/court_reference.png"), cv2.COLOR_BGR2GRAY) #/usr/src/app/src/server/libs/court_configurations/court_reference.png


    def GetImportantLines(self):
        """Sahanın tüm çizgilerinini al"""
        lines = [*self.baseline_top, *self.baseline_bottom, *self.net, *self.left_court_line, *self.right_court_line,
                 *self.left_inner_line, *self.right_inner_line, *self.middle_line,
                 *self.top_inner_line, *self.bottom_inner_line]
        return lines


    def GetExtraParts(self):
        parts = [self.top_extra_part, self.bottom_extra_part]
        return parts


    def SaveAllCourtConfigurations(self):
        """Saha referansındaki 4 noktanın tüm konfigürasyonunu oluştur"""
        for i, conf in self.court_conf.items():
            c = cv2.cvtColor(255 - self.court, cv2.COLOR_GRAY2BGR)
            for p in conf:
                c = cv2.circle(c, p, 15, (0, 0, 255), 30)
            cv2.imwrite(f'/usr/src/app/DetectCourtLines/server/libs/court_configurations/court_conf_{i}.png', c) #/usr/src/app/DetectCourtLines/server/   Container içindeki path


    def GetCourtMask(self, mask_type=0):
        """Sahanın maskesini al"""
        mask = np.ones_like(self.court)
        if mask_type == 1:  # Bottom half court
            mask[:self.net[0][1] - 1000, :] = 0
        elif mask_type == 2:  # Top half court
            mask[self.net[0][1]:, :] = 0
        elif mask_type == 3: # court without margins
            mask[:self.baseline_top[0][1], :] = 0
            mask[self.baseline_bottom[0][1]:, :] = 0
            mask[:, :self.left_court_line[0][0]] = 0
            mask[:, self.right_court_line[0][0]:] = 0
        return mask


if '__main__' == __name__:
    import numpy as np
    COURT_REFERENCE = CourtReference()
    lines = COURT_REFERENCE.GetImportantLines()
    print(np.array(lines).shape)
    print(lines, "\n")
    p = np.array(lines, dtype=np.float32).reshape((-1, 1, 2))
    print(p)