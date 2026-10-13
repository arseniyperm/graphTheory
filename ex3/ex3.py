def reachCount(v, link, visited):
    visited[v] = True

    for neighbor in link[v]:
        if not visited[neighbor]:
            reachCount(neighbor, link, visited)


def checkNext(u, v, link, v_num):
    if len(link[u]) == 1:
        return True

    visited = [False] * v_num
    reachCount(u, link, visited)
    count1 = sum(visited)

    link[u].remove(v)
    link[v].remove(u)

    visited = [False] * v_num
    reachCount(u, link, visited)
    count2 = sum(visited)

    link[u].append(v)
    link[v].append(u)

    return count1 == count2


def getEuler(u, link, path, v_num):
    for i in range(len(link[u])):
        next = link[u][i]
        if checkNext(u, next, link, v_num):
            path.append([u, next])
            link[u].remove(next)
            link[next].remove(u)
            getEuler(next, link, path, v_num)
            break


def startEuler(v_num, link):
    start = 0
    for i in range(v_num):
        if len(link[i]) % 2 != 0:
            start = i
            break

    path = []
    getEuler(start, link, path, v_num)
    return path


def export_to_dot(adj, filename="graph.dot", directed=False):
    kind = "digraph" if directed else "graph"
    arrow = "->" if directed else "--"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"{kind} G {{\n")
        f.write('    layout=dot;\n')
        f.write('    node [shape=circle];\n')

        for u in range(len(adj)):
            f.write(f'    {u};\n')

        seen = set()
        for u in range(len(adj)):
            for v in adj[u]:
                if not directed:
                    key = (min(u, v), max(u, v))
                    if key in seen:
                        continue
                    seen.add(key)
                f.write(f'    {u} {arrow} {v};\n')
        f.write("}\n")


if __name__ == "__main__":
    v_num = 6
    link = [[1, 2],
            [0, 2, 4],
            [0, 1, 3, 5],
            [2, 5],
            [1, 5],
            [4, 2, 3]]
    export_to_dot(link)

    res = startEuler(v_num, link)

    for i in range(len(res)):
        print(f"{res[i][0]}-{res[i][1]}", end="")
        if i != len(res) - 1:
            print(", ", end="")
