
#imports
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import CubicSpline, interp1d
plt.rcParams['figure.figsize'] = (12,8)

x = np.arange(-10,10)
y = 1/(1+x**2)

# apply cubic spline interpolation
cs = CubicSpline(x, y)
# Apply Linear interpolation
linear_int = interp1d(x, y, kind="linear")
  
xs = np.arange(-10, 10)
ys = linear_int(xs)


print(ys, "\n\n", y)

# plot linear interpolation
plt.plot(x, y, 'o', label='data')
plt.plot(xs, ys, "-",  label="S", color='green')
plt.legend(loc='upper right', ncol=1)
plt.title('Linear Interpolation')
plt.show()



# plot cubic spline interpolation
plt.plot(x, y, 'o', label='data')
plt.plot(xs, 1/(1+(xs**2)), label='true')
plt.plot(xs, cs(xs), label="S")
plt.plot(xs, cs(xs, 1), label="S'")
plt.plot(xs, cs(xs, 2), label="S''")
plt.plot(xs, cs(xs, 3), label="S'''")
plt.ylim(-1.5, 1.5)
plt.legend(loc='upper right', ncol=1)
plt.title('Cubic Spline Interpolation')
plt.show()