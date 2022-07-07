import pickle
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from scipy.interpolate import interp1d
from scipy.signal import find_peaks

class StatusPredicter():

    def predictFallBallPositon(self, ball_positions, verbose=False):
        """Topun ve oyuncuların konumunu kullanarak önemli bilgileri çıkart"""

        #!TOPUN KONUMLARI INTERPOLASYONU
        #//########################################################################################
        
        if len(ball_positions)<1:
            return []
        
        ball_positions = np.array(ball_positions)
        ball_x, ball_y = ball_positions[:, 0], ball_positions[:, 1]

        # Delete None Values
        ball_y = ball_y[ball_y != None]
        ball_x = ball_x[ball_x != None]

        # Savitzky-Golay Filter
        smooth_y = signal.savgol_filter(ball_y, 41, 2)  # 41-3, 41,2, 5-3
        smooth_x = signal.savgol_filter(ball_x, 41, 2)

        array_length = len(smooth_y)

        indexes = np.arange(0, array_length)
        ball_f_y = interp1d(indexes, smooth_y, kind='cubic', fill_value="extrapolate")
        ball_f_x = interp1d(indexes, smooth_x, kind='cubic', fill_value="extrapolate")
        xnew = np.linspace(0, array_length, num=array_length, endpoint=True)

        intp1d_ball_coordinates_y = ball_f_y(xnew)
        intp1d_ball_coordinates_x = ball_f_x(xnew)

        if verbose:
            fig = plt.figure()
            plt.plot(np.arange(0, array_length), smooth_y, 'o',xnew, intp1d_ball_coordinates_y, '-r')
            plt.legend(['data', 'inter'], loc='best')
            plt.savefig("data/graphs/ball_interpolation.png", bbox_inches='tight')
            plt.show()
            pickle.dump(fig, open('data/figures/ball_interpolation.fig.pickle', 'wb'))

        #* Topun Y eksenindeki local maximumları göster
        peaks, _ = find_peaks(intp1d_ball_coordinates_y)
        
        if verbose:
            plt.plot(intp1d_ball_coordinates_y)
            plt.plot(peaks, intp1d_ball_coordinates_y[peaks], "x")
            plt.savefig("data/graphs/ball_local_maxs.png", bbox_inches='tight')
            plt.show()

        if len(peaks) < 1:
            return

        x = intp1d_ball_coordinates_x[peaks]
        y = intp1d_ball_coordinates_y[peaks]
        arr = list(zip(x, y))

        return arr