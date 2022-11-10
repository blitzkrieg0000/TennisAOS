from scipy import signal
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import CubicSpline, interp1d
from scipy.signal import find_peaks

plt.rcParams['figure.figsize'] = (12,8)
ball_positions = [[None, None], [None, None], [879, 525], [None, None], [906.5, 505.5], [905.5, 504.5], [933.5, 483.5], [932.5, 484.5], [None, None], [960.5, 465.5], [959.5, 465.5], [982.5, 448.5], [983.5, 450.5], [1005.5, 440.5], [1004.5, 440.5], [None, None], [1022.5, 433.5], [1024.5, 433.5], [1043.5, 425.5], [1042.5, 424.5], [1042, 424], [1060.5, 418.5], [1059.5, 417.5], [1076.5, 416.5], [1076, 417], [1091.5, 412.5], [1093.5, 414.5], [None, None], [1107.5, 412.5], [1105.5, 413.5], [1123.5, 414.5], [1122.5, 414.5], [None, None], [1130.5, 400.5], [1131, 400], [1140.5, 377.5], [1142.5, 377.5], [1149.5, 357.5], [1149, 358], [1148.5, 359.5], [1156.5, 337.5], [1156.5, 339.5], [1162.5, 327.5], [1164.5, 327.5], [None, None], [1173.5, 309.5], [1172.5, 308.5], [1177.5, 297.5], [1176.5, 298.5], [1184.5, 288.5], [1186.5, 288.5], [None, None], [1192.5, 279.5], [1194.5, 280.5], [1200.5, 271.5], [1199.5, 269.5], [None, None], [1202.5, 267.5], [1204.5, 267.5], [1211.5, 260.5]]
ball_positions = np.array(ball_positions)
ball_x, ball_y = ball_positions[:, 0], ball_positions[:, 1]
ball_y = ball_y[ball_y != None]
ball_x = ball_x[ball_x != None]


window = 5
smooth_y = signal.savgol_filter(ball_y, window, 3)  # 31-3, 41-3, 5-3
smooth_x = signal.savgol_filter(ball_x, window, 3)


array_length = len(smooth_y)

indexes = np.arange(0, array_length)
ball_f_y = interp1d(indexes, smooth_y, kind='cubic', fill_value="extrapolate")
ball_f_x = interp1d(indexes, smooth_x, kind='cubic', fill_value="extrapolate")
cs = CubicSpline(indexes, smooth_y)


xnew = np.linspace(0, array_length, num=array_length, endpoint=True)
intp1d_ball_coordinates_y = ball_f_y(xnew)
intp1d_ball_coordinates_x = ball_f_x(xnew)
css = cs(xnew)


fig = plt.figure()
plt.plot(indexes, ball_y, "o", label="data")
plt.plot(indexes, ball_y, "-r", label="original Y")
plt.legend(loc='best', ncol=1)


fig = plt.figure()
plt.plot(indexes, smooth_y, "o", label="data")
plt.plot(indexes, smooth_y, "-r", label="savgol")
plt.legend(loc='best', ncol=1)


fig = plt.figure()
plt.plot(xnew, intp1d_ball_coordinates_y, 'o', label="data")
plt.plot(xnew, intp1d_ball_coordinates_y, "-r", label="intp1d_cubic_y")
plt.legend(loc='best', ncol=1)


# fig = plt.figure()
# plt.plot(xnew, css, 'o', label="data")
# plt.plot(xnew, css, "-r", label="cubic spline")
# plt.legend(loc='best', ncol=1)


#* Topun Y eksenindeki local maximumları göster
peaks, _ = find_peaks(intp1d_ball_coordinates_y)
print(peaks)
fig = plt.figure()
plt.plot(xnew, intp1d_ball_coordinates_y, "-r", label="intp1d_cubic_y")
plt.plot(xnew[peaks], intp1d_ball_coordinates_y[peaks], "x", label="peaks")
plt.legend(loc='best', ncol=1)
plt.show()


x = intp1d_ball_coordinates_x[peaks]
y = intp1d_ball_coordinates_y[peaks]
arr = list(zip(x, y))
