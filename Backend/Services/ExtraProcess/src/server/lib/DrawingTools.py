import collections

import cv2
from lib.ExtraTools import ExtraTools


class DrawingTools(ExtraTools):
	def __init__(self):
		super().__init__()

		self.regular_angle_descriptors: collections.defaultdict(list) = {
			"r_armpit" 	: [ ["RIGHT", "elbow"],["RIGHT", "shoulder"], ["RIGHT", "hip"]	 	],
			"l_armpit" 	: [ ["LEFT", "elbow"], ["LEFT", "shoulder"],  ["LEFT", "hip"] 	 	],
			"r_elbow" 	: [ ["RIGHT","wrist"], ["RIGHT","elbow"],     ["RIGHT","shoulder"] 	],
			"l_elbow" 	: [ ["LEFT","wrist"],  ["LEFT","elbow"],      ["LEFT","shoulder"]  	],
			"r_knee" 	: [ ["RIGHT","hip"],  ["RIGHT","knee"], 	  ["RIGHT","ankle"]	 	],
			"l_knee" 	: [ ["LEFT","hip"],    ["LEFT","knee"], 	  ["LEFT","ankle"] 	    ]
		}


	def DrawAngles(self, canvas, angle, points):
		for key in self.regular_angle_descriptors:
			item = self.regular_angle_descriptors[key]
			
			point_1 = points[item[0][0]][item[0][1]]
			point_2 = points[item[1][0]][item[1][1]]
			point_3 = points[item[2][0]][item[2][1]]

			P1x = int(point_1.x)
			P1y = int(point_1.y)
			P2x = int(point_2.x)
			P2y = int(point_2.y)
			P3x = int(point_3.x)
			P3y = int(point_3.y)

			canvas = cv2.line(canvas, (P1x, P1y), (P2x, P2y), (255, 255, 255), 2)
			canvas = cv2.line(canvas, (P2x, P2y), (P3x, P3y), (255, 255, 255), 2)
			angle_str = float("%0.2f" % (angle[key]))
			canvas = cv2.putText(canvas, str(angle_str), (P2x, P2y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (66, 179, 245), 1, cv2.LINE_AA)

		return canvas


	def GetSpecialAngles(self, points):
		angles = collections.defaultdict(list)
		for key in self.regular_angle_descriptors:
			item = self.regular_angle_descriptors[key]
			angles[key] = self.getAngle3D(points[item[0][0]][item[0][1]], points[item[1][0]][item[1][1]], points[item[2][0]][item[2][1]]) # Right Armpit

		# angles["dist_ankle"] = self.getDistance(points["LEFT"]["ankle"], points["RIGHT"]["ankle"])
		# angles["leg_angle"] = self.getAngle3D(points["LEFT"]["ankle"], self.getMidPoint(points["LEFT"]["hip"], points["RIGHT"]["hip"]), points["RIGHT"]["ankle"])

		return angles

