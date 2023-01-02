import numpy as np
from numba import jit


@jit(nopython=True)
def HampelFilter(input_series, window_size, n_sigmas=3):
    n = len(input_series)
    new_series = input_series.copy()
    k = 1.4826 # Gauss dağılımı için ölçek
    
    indices = []
    for i in range((window_size),(n - window_size)):
        x0 = np.median(input_series[(i - window_size):(i + window_size)])
        S0 = k * np.median(np.abs(input_series[(i - window_size):(i + window_size)] - x0))
        if (np.abs(input_series[i] - x0) > n_sigmas * S0):
            new_series[i] = x0
            indices.append(i)
    
    return new_series, indices