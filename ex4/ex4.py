import numpy as np


def hungarian_alg(cost_matrix):
    n = len(cost_matrix)

    u = [0] * (n + 1)
    v = [0] * (n + 1)
    p = [0] * (n + 1)
    way = [0] * (n + 1)

    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [float('inf')] * (n + 1)
        used = [False] * (n + 1)

        while True:
            used[j0] = True
            i0 = p[j0]
            delta = float('inf')
            j1 = 0

            for j in range(1, n + 1):
                if not used[j]:
                    cur = cost_matrix[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j

            for j in range(n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta

            j0 = j1
            if p[j0] == 0:
                break

        # Восстанавливаем путь
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    matching = []
    total_cost = 0
    for j in range(1, n + 1):
        if p[j] != 0:
            row = p[j] - 1
            col = j - 1
            matching.append((row, col))
            total_cost += cost_matrix[row][col]

    return total_cost, matching


if __name__ == "__main__":
    w = np.array([
        [3, 14, 5, 6, 7],
        [1, 9, 7, 4, 3],
        [8, 7, 4, 6, 3],
        [5, 6, 9, 13, 15],
        [19, 14, 16, 8, 12]
    ])

    cost, pairs = hungarian_alg(w)
    print(f"Минимальный вес: {cost}")
    for u, v in pairs:
        print(f"Row {u} - Col {v} ({w[u, v]})")
