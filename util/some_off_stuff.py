import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit


def sine_function(x, A, f, phi, C):
    return A * np.sin(2 * np.pi * f * x + phi) + C


def fit_sine_function(x, y):
    # Гармоническая функция синуса

    # Аппроксимация гармонической функцией
    params, params_covariance = curve_fit(sine_function, x, y)

    # Извлечение параметров аппроксимации
    A_fit, f_fit, phi_fit, C_fit = params

    # Возвращаем коэффициенты аппроксимации
    return A_fit, f_fit, phi_fit, C_fit


# Пример использования


def generate_smooth_curve(start, end, num_points, window_size=10):
    # Generate some random values
    x = np.linspace(start, end, num_points)
    y = np.random.uniform(start, end, num_points)

    # calculating filter with sliding window

    weights = np.repeat(1.0, window_size) / window_size

    # fill edges with values
    padded_y = np.pad(y, (window_size - 1, window_size - 1), mode="edge")

    # applying filter to values
    smoothed_y = np.convolve(padded_y, weights, "valid")

    # interpolate to restore amount of points
    xp = np.linspace(start, end, len(smoothed_y))
    fp = np.interp(x, xp, smoothed_y)

    return fp


def calculate_slope(x1, y1, x2, y2):
    slope = (y2 - y1) / (x2 - x1)
    return slope


def rising_then_drop(smooth_curve, break_value, rise_part=5, drop_part=5):
    # calculate point where thing start getting weird
    n_arr = len(smooth_curve)
    break_point = np.random.random() / 5 + 0.2
    # 1/5 of array size
    # gradual rise
    rise_pos = int(n_arr * break_point)
    # drop to zero
    drop_pos = int(rise_pos + n_arr / rise_part)
    # rise to normal value
    up_pos = int(drop_pos + n_arr / drop_part)
    # avg smooth val
    avg_val = np.average(smooth_curve)
    # slope calc
    # slope = calculate_slope(rise_pos, avg_val, drop_pos, break_value)
    # adding rise section
    smooth_curve[rise_pos:drop_pos] = smooth_curve[rise_pos:drop_pos] + np.linspace(
        0, break_value - avg_val, drop_pos - rise_pos
    )
    # adding zero section
    smooth_curve[drop_pos:up_pos] = 0


def sudden_drop_out(smooth_curve):
    pass


# Пример использования функции
n = 300
x = np.linspace(0, 100, n)
y = np.zeros_like(x)
k = 10
for _ in range(10):
    y_tmp = np.random.random(k) * 2 + 4  # Добавляем шум к синусоиде
    y += sine_function(
        x, *fit_sine_function(np.arange(0, n + 1, n / (k - 1), dtype=int), y_tmp)
    )
y /= 10

plt.plot(x, y)
plt.show()


# параметры для плавного отказа
y = generate_smooth_curve(2, 6, n, 10)
plt.plot(x, y, "--r")
rising_then_drop(y, 10, 3, 10)
plt.plot(x, y, "-b")
plt.grid()
plt.show()
# параметры для жёского отказа
y = generate_smooth_curve(3, 6, n, 20)
plt.plot(x, y, "--r")
rising_then_drop(y, 10, 20, 10)
plt.plot(x, y, "-b")
plt.grid()
plt.show()
