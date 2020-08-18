import numpy as np


def min_max(in_real):
    min_val = in_real[0]
    max_val = in_real[0]
    for price in in_real:
        if min_val > price:
            min_val = price
        if max_val < price:
            max_val = price
    return min_val, max_val


def ichimoku_cloud(in_real):
    length = len(in_real)
    tenkan = [0] * min(9, length)
    kijun = [0] * min(26, length)
    senkou_a = [0] * min(26, length)
    senkou_b = [0] * min(52, length)
    chikou = [0] * min(26, length)
    for i in range(len(in_real)):
        if i >= 9:
            min_val, max_val = min_max(in_real[i-9:i])
            tenkan.append((min_val + max_val) / 2)
        if i >= 26:
            min_val, max_val = min_max(in_real[i-26:i])
            kijun.append((min_val + max_val) / 2)
            senkou_a.append((tenkan[i] + kijun[i]) / 2)
            chikou.append(in_real[i-26])
        if i >= 52:
            min_val, max_val = min_max(in_real[i-52:i])
            senkou_b.append((min_val + max_val) / 2)

    senkou_a = ([0] * 26) + senkou_a[:-26]
    senkou_b = ([0] * 26) + senkou_b[:-26]
    return tenkan, kijun, senkou_a, senkou_b, chikou
