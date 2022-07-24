import logging
import queue
import time
import cv2
import numpy as np
# from libs.inference import InferenceManager
from libs.inference import InferenceManager

class KalmanFilter:
	kf = cv2.KalmanFilter(4, 2)
	kf.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
	kf.transitionMatrix = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32)
	kf.processNoiseCov = np.array( [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]], np.float32) * 0.03
	
	def predict(self, coordX, coordY):
		measured = np.array([[np.float32(coordX)], [np.float32(coordY)]])
		self.kf.correct(measured)
		predicted = self.kf.predict()
		x, y = int(predicted[0]), int(predicted[1])
		return x, y

class TrackNetObjectDetection(object):
	def __init__(self):
		self.inferenceManager = InferenceManager()
		self.n_classes = 256
		self.width, self.height = 640, 360
		self.img, self.img1, self.img2 = None, None, None
		self.xy_coordinates = np.array([[None, None], [None, None]])
		self.bounces_indices = []
		self.intp1d_ball_coordinates_y = []

		#KALMAN
		self.kf = KalmanFilter()

		# QUEUEUEUES
		self.queue_length = 9
		self.q = queue.deque()
		for i in range(0, self.queue_length):
			self.q.appendleft(None)
		
		self.miss_counter_length = 3
		self.miss_queue = queue.deque()
		for i in range(0, self.miss_counter_length):
			self.miss_queue.appendleft(False)

		# Ana topu bulmak için iyileştirmeler
		self.last_x = None
		self.last_y = None
		self.predicted_x = None
		self.predicted_y = None
		self.MIN_DIST = 1.0       	 # Top az da olsa hareket etmiş olmalıdır. Hareketsiz noktaların takibini bırak
		self.MAX_DIST = 50.0		 # Son konuma göre bulunacak topun maksimum uzaklığı
		self.MIN_DIST_KALMAN = 1.0
		self.MAX_DIST_KALMAN = 50.0
		self.PREFIX = 0.0			 # Son konuma göre top bulunamamışsa self.MAX_DIST bu değer kadar arttırılıp tekrar denenir.
		self.DIST_CHANGE = 18		 # Tekrar son konuma göre kaç kere self.MAX_DIST, self.PREFIX_INC_VAL kadar arttırılıp denemeye yapılacak.
		self.PREFIX_INC_VAL = 5.0 	 # self.MAX_DIST değerine eklenecek self.PREFIX değerini adım başı arttırma miktarı

	def add_queue(self, queue_var, item):
		queue_var.appendleft(item)
		queue_var.pop()

	def is_miss_queue_is_full_reset_counters(self):
		if all([x for x in list(self.miss_queue)]):
			for i in range(0, self.miss_counter_length):
				self.add_queue(self.miss_queue, False)
				self.last_x = None
				self.last_y = None

	def update_last_positions(self, x, y):
		self.last_x, self.last_y = x, y

	def calculate_distance_availability(self, circles, distances):
		x, y = None, None
		for i in range(0, self.DIST_CHANGE): #şans en az 1 olmalıdır
			distance_indexes = np.where( (distances>=self.MIN_DIST) & (distances<=(self.MAX_DIST + self.PREFIX)) )[0]

			dist = np.full(distances.shape, np.inf)

			if len(distance_indexes) > 0:
				dist[distance_indexes] = distances[distance_indexes]

				logging.info(dist)
				index = np.argmin( dist )

				logging.info("index: ",index)
				x, y, z = circles[index]
				logging.info("last: ", self.last_y)
				logging.info("y: ",y)
				break
			else:
				self.PREFIX = self.PREFIX_INC_VAL + self.PREFIX
		self.PREFIX = 0
		
		return x, y

	def determine_positions(self, circles):
		x, y = None, None
		if circles is not None:
			circles = circles[0]
			
			# Eğer art arda yeteri kadar top bulunamamışsa, durumu sıfırla
			self.is_miss_queue_is_full_reset_counters()

			if self.last_y is not None:
				
				# SON DEĞER VARSA, YENİ DEĞERLERİ BU DEĞERLE KARŞILAŞTIR. EĞER İSTENİLEN YER DEĞİŞTİRME SAĞLANMIŞSA YENİ KONUMU AL
				distances = np.array([])
				for circle in circles:
					x = int(circle[0])
					y = int(circle[1])
					dist = np.linalg.norm( np.array([x, y]) - np.array([self.last_x, self.last_y]) )
					distances = np.append(distances, dist)
				logging.info("LAST_DISTANCE: ", distances)
				px, py = self.calculate_distance_availability(circles, distances)
				if py is not None:
					# EKLE
					x, y = px, py
					self.update_last_positions(x, y)
					self.add_queue(self.miss_queue, False)
					self.add_queue(self.q, [x, y])
				
				else:
					logging.info("CIRCLE DISTANCE İLE BULUNAMADI!")
					self.add_queue(self.miss_queue, True)
					self.add_queue(self.q, None)
			
			else:
				# SON KONUMU REFERANS ALINACAK TOPU BUL
				# SON KONUM YOKSA BURAYA GİRER (MISS SAYISI BELİRLENEN SAYI KADAR ART ARDA TRUE GELMİŞSE)
				distances_pre = np.array([])
				for circle in circles:
					x = int(circle[0])
					y = int(circle[1])

					#// TODO Kalmandan hesaplanan noktanın ne kadar doğru olduğunu bul(Kalman son noktaya ne kadar yakın?)
					# TODO Kalman filtresi atışlardan sonra hesaplanmaya başlasın topun her konumunu kalman filtresine koyma
					# Kalmandan hesaplanan nokta varsa o noktayı kullan
					if self.predicted_y:
						dist = np.linalg.norm( np.array([x, y]) - np.array([self.predicted_x, self.predicted_y]) )
						distances_pre = np.append(distances_pre, dist)

				logging.info("KALMAN_DISTANCE: ", distances_pre)
				distance_indexes_pre = np.where( (distances_pre>self.MIN_DIST_KALMAN) & (distances_pre<self.MAX_DIST_KALMAN ) )[0]
				dist = np.full(distances_pre.shape, np.inf)
				if len(distance_indexes_pre) > 0:
					dist[distance_indexes_pre] = distances_pre[distance_indexes_pre]
					index = np.argmin( dist )
					x, y, z = circles[index]
				
				self.update_last_positions(x, y)
				self.add_queue(self.miss_queue, False)
				self.add_queue(self.q, [x, y])
		
		else:
			#! CIRCLE YOK (HİÇ CIRCLE YOKTUR)
			logging.info("CIRCLE HİÇ YOK!")
			self.add_queue(self.miss_queue, True)
			self.add_queue(self.q, None)
		
		logging.info("MISS_QUEUE: ", self.miss_queue, "\n\n")

		if self.last_y is not None:
			self.predicted_x, self.predicted_y = self.kf.predict(self.last_x, self.last_y)
			dist_reliability = np.linalg.norm( np.array([self.last_x, self.last_y]) - np.array([self.predicted_x, self.predicted_y]) )
			logging.info(dist_reliability)
			if not (0 <= dist_reliability <= 100):
				self.predicted_x, self.predicted_y = None, None

		return x, y

	def draw_canvas(self, canvas, draw):
		if draw:
			if self.predicted_y:
				canvas = cv2.circle(canvas, (self.predicted_x, self.predicted_y), 5, (0, 0, 255), 2)

			for i in range(0, self.queue_length):
				if self.q[i] is not None:
					draw_x = self.q[i][0]
					draw_y = self.q[i][1]
					canvas = cv2.ellipse(canvas, (int(draw_x), int(draw_y)), (4, 4), 0, 0, 360, (0, 255, 255), 1)
		return canvas

	def detect(self, frame, canvas_image, draw=False):
		x, y = None, None
		canvas = canvas_image
		output_height, output_width = frame.shape[:-1]
		self.current_frame = cv2.resize(frame, ( self.width , self.height ))
		self.current_frame = self.current_frame.astype(np.float32)
		
		# Toplam 3 image olana kadar bekler ve ardışık 3 frami alır
		self.img2 = self.img1
		self.img1 = self.img
		self.img = self.current_frame
		
		if self.img2 is not None:
			# 3 ardışık resmi yan yana birleştir (width , height, rgb*3)
			X = np.concatenate((self.img, self.img1, self.img2), axis=2)

			# TrackNet channel_first bir yapı alır yani 640, 360, 3 değilde 3, 640, 360 şeklinde input shape ister.
			X = np.rollaxis(X, 2, 0)


			#TODO INFERENCE
			# Inference
			tic = time.time()
			pr = self.inferenceManager.inference(X)
			toc = time.time()
			logging.info(f"Inference Time: {toc-tic}")


			# TrackNet çıkışı ( net_output_height*model_output_width , n_classes ) olduğundan
			# tekrar boyutlandırmamız gerekiyor: ( net_output_height, model_output_width , n_classes(depth) )
			#.argmax( axis=2 ) => Argmax sağolsun en iyi ihtimal değerini döndürüyoruz.
			pr = pr.reshape(( self.height ,  self.width , self.n_classes )).argmax( axis=2 )

			# numpy.int64 -> numpy.uint8 (0-255 ya hani)
			pr = pr.astype(np.uint8) 

			# Çıkışı tekrar boyutlandırırız zaten heatmap olduğundan şekiller önemli bizim için
			heatmap = cv2.resize(pr, (output_width, output_height ))
			
			# Threshold
			ret, heatmap = cv2.threshold(heatmap, 127, 255,cv2.THRESH_BINARY)
			kernelSize = (3, 3)
			kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernelSize)
			heatmap = cv2.morphologyEx(heatmap, cv2.MORPH_OPEN, kernel)

			# cv2.imshow('', heatmap)
			# cv2.waitKey(0)

			# Hough dönüşümü ile kapalı şekilleri(çemberleri) buluruz 2<=çap<=7
			circles = cv2.HoughCircles(heatmap, cv2.HOUGH_GRADIENT, dp=1, minDist=1, param1=50, param2=5, minRadius=3, maxRadius=7)
			if circles is not None:
				for circle in circles[0]:
					canvas = cv2.ellipse(canvas, (int(circle[0]), int(circle[1])), (7, 7), 0, 0, 360, (255, 255, 255), 1)
					
			x, y = self.determine_positions(circles)

		self.xy_coordinates = np.append(self.xy_coordinates, np.array([[x, y]]), axis=0)
		
		#?DRAW
		canvas = self.draw_canvas(canvas, draw)

		return (x, y), canvas

	def mark_positions(self, frame, mark_num=4, frame_num=None, ball_color='yellow'):
		bounce_i = None

		if frame_num is not None:
			q = self.xy_coordinates[frame_num-mark_num+1:frame_num+1, :]
			for i in range(frame_num - mark_num + 1, frame_num + 1):
				if i in self.bounces_indices:
					bounce_i = i - frame_num + mark_num - 1
					break
		else:
			q = self.xy_coordinates[-mark_num:, :]
        
		pil_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

		for i in range(q.shape[0]):
			if q[i, 0] is not None:
				draw_x = q[i, 0]
				draw_y = q[i, 1]
				bbox = (draw_x - 2, draw_y - 2, draw_x + 2, draw_y + 2)
				if bounce_i is not None and i == bounce_i:
					pil_image = cv2.ellipse(pil_image, (bbox[0], bbox[1]), (4, 4), 0, 0, 360, (0, 0, 255), 1)

			frame = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
		return frame