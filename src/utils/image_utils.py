import numpy as np

def normalize_tensor(t):
    mn = t.min()
    mx = t.max()
    if mn == mx:
        return np.zeros_like(t)
    else:
        result = np.copy(t).astype('float64')
        result -= mn
        result /= (mx-mn)

        return result