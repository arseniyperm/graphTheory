from collections import defaultdict
import networkx as nx


class Interval:
    """Интервал обратных рёбер"""

    def __init__(self, low=None, high=None):
        self.low = low
        self.high = high

    def empty(self):
        return self.low is None and self.high is None

    def copy(self):
        return Interval(self.low, self.high)

    def conflicting(self, edge, state):
        return (
            not self.empty()
            and state.lowpt[self.high] > state.lowpt[edge]
        )


class ConflictPair:
    """Пара конфликтующих интервалов"""

    def __init__(self, left=None, right=None):
        self.left = left if left is not None else Interval()
        self.right = right if right is not None else Interval()

    def swap(self):
        self.left, self.right = self.right, self.left

    def lowest(self, state):
        if self.left.empty():
            return state.lowpt[self.right.low]

        if self.right.empty():
            return state.lowpt[self.left.low]

        return min(
            state.lowpt[self.left.low],
            state.lowpt[self.right.low]
        )


class LRPlanarity:
    """
    Left-Right Planarity Test

    Результат:
        PlanarEmbedding, если граф планарен
        None, если граф непланарен
    """

    def __init__(self, graph):
        self.n = len(graph)

        # Список смежности исходного графа
        self.adj = {
            v: list(dict.fromkeys(
                w for w in graph[v] if w != v
            ))
            for v in graph
        }

        self.nodes = list(graph)

        # Удаляем повторяющиеся неориентированные рёбра
        self.adj = {
            v: list(dict.fromkeys(self.adj[v]))
            for v in self.nodes
        }

        self.m = sum(len(x) for x in self.adj.values()) // 2

        # Ориентированный DFS-граф
        self.DG = {v: [] for v in self.nodes}

        # DFS-информация.
        self.height = {v: None for v in self.nodes}
        self.parent_edge = {v: None for v in self.nodes}

        self.roots = []

        # Lowpoint-информация
        self.lowpt = {}
        self.lowpt2 = {}
        self.nesting_depth = {}

        # Упорядоченные списки смежности
        self.ordered_adjs = {}

        # Стек конфликтных пар
        self.S = []

        self.stack_bottom = {}
        self.lowpt_edge = {}

        # Ссылки и стороны рёбер.
        self.ref = defaultdict(lambda: None)
        self.side = defaultdict(lambda: 1)

        self.left_ref = {}
        self.right_ref = {}

        # Итоговое вложение.
        self.embedding = None

    def edge_exists(self, u, v):
        return v in self.DG[u]

    def top(self):
        return self.S[-1] if self.S else None


    # 1. DFS-ориентация и вычисление lowpoint
    def dfs_orientation(self, v):

        e = self.parent_edge[v]

        for w in self.adj[v]:

            # Ребро уже было ориентировано
            if self.edge_exists(v, w) or self.edge_exists(w, v):
                continue

            self.DG[v].append(w)

            vw = (v, w)

            self.lowpt[vw] = self.height[v]
            self.lowpt2[vw] = self.height[v]

            if self.height[w] is None:

                # Ребро DFS-дерева
                self.parent_edge[w] = vw
                self.height[w] = self.height[v] + 1

                self.dfs_orientation(w)

            else:

                # Обратное ребро
                self.lowpt[vw] = self.height[w]

            # Вычисление nesting_depth
            self.nesting_depth[vw] = 2 * self.lowpt[vw]

            if self.lowpt2[vw] < self.height[v]:
                self.nesting_depth[vw] += 1

            # Обновление lowpoint родительского ребра
            if e is not None:

                if self.lowpt[vw] < self.lowpt[e]:

                    self.lowpt2[e] = min(
                        self.lowpt[e],
                        self.lowpt2[vw]
                    )

                    self.lowpt[e] = self.lowpt[vw]

                elif self.lowpt[vw] > self.lowpt[e]:

                    self.lowpt2[e] = min(
                        self.lowpt2[e],
                        self.lowpt[vw]
                    )

                else:

                    self.lowpt2[e] = min(
                        self.lowpt2[e],
                        self.lowpt2[vw]
                    )


    # 2. Стабильная сортировка по nesting_depth
    def order_adjacencies(self, signed=False):
        """
        Стабильная сортировка рёбер по nesting_depth
        """

        n = max(1, self.n)

        offset = 2 * n + 1
        buckets = [[] for _ in range(4 * n + 3)]

        for v in self.nodes:
            for w in self.DG[v]:

                key = self.nesting_depth[(v, w)]

                if signed:
                    key = self.sign((v, w))

                buckets[key + offset].append((v, w))

        result = {v: [] for v in self.nodes}

        for bucket in buckets:
            for v, w in bucket:
                result[v].append(w)

        self.ordered_adjs = result


    # 3. Добавление ограничений
    def add_constraints(self, ei, e):

        P = ConflictPair()

        # 1) объединяем правые интервалы
        while True:

            Q = self.S.pop()

            if not Q.left.empty():
                Q.swap()

            if not Q.left.empty():
                return False

            if self.lowpt[Q.right.low] > self.lowpt[e]:

                if P.right.empty():

                    P.right = Q.right.copy()

                else:

                    self.ref[P.right.low] = Q.right.high

                P.right.low = Q.right.low

            else:

                self.ref[Q.right.low] = self.lowpt_edge[e]

            if self.top() is self.stack_bottom[ei]:
                break

        # 2) объединяем конфликтующие интервалы
        while (
            self.top().left.conflicting(ei, self)
            or self.top().right.conflicting(ei, self)
        ):

            Q = self.S.pop()

            if Q.right.conflicting(ei, self):
                Q.swap()

            if Q.right.conflicting(ei, self):
                return False

            self.ref[P.right.low] = Q.right.high

            if Q.right.low is not None:
                P.right.low = Q.right.low

            if P.left.empty():

                P.left = Q.left.copy()

            else:

                self.ref[P.left.low] = Q.left.high

            P.left.low = Q.left.low

        if not (P.left.empty() and P.right.empty()):
            self.S.append(P)

        return True


    # 4. Удаление обратных рёбер
    def remove_back_edges(self, e):

        u = e[0]

        # Удаляем конфликтные пары, возвращающиеся к родителю
        while (
            self.S
            and self.top().lowest(self) == self.height[u]
        ):

            P = self.S.pop()

            if P.left.low is not None:
                self.side[P.left.low] = -1

        if self.S:

            P = self.S.pop()

            # Обрезаем левый интервал
            while (
                P.left.high is not None
                and P.left.high[1] == u
            ):

                P.left.high = self.ref[P.left.high]

            if P.left.high is None and P.left.low is not None:

                self.ref[P.left.low] = P.right.low
                self.side[P.left.low] = -1
                P.left.low = None

            # Обрезаем правый интервал
            while (
                P.right.high is not None
                and P.right.high[1] == u
            ):

                P.right.high = self.ref[P.right.high]

            if P.right.high is None and P.right.low is not None:

                self.ref[P.right.low] = P.left.low
                self.side[P.right.low] = -1
                P.right.low = None

            self.S.append(P)

        # Определяем относительную сторону родительского ребра
        if self.lowpt[e] < self.height[u]:

            hl = self.top().left.high
            hr = self.top().right.high

            if (
                hl is not None
                and (
                    hr is None
                    or self.lowpt[hl] > self.lowpt[hr]
                )
            ):

                self.ref[e] = hl

            else:

                self.ref[e] = hr


    # 5. DFS-проверка конфликтов
    def dfs_testing(self, v):

        e = self.parent_edge[v]

        for i, w in enumerate(self.ordered_adjs[v]):

            ei = (v, w)

            self.stack_bottom[ei] = self.top()

            if self.parent_edge[w] == ei:

                # Ребро дерева: рекурсивно проверяем потомка
                if not self.dfs_testing(w):
                    return False

            else:

                # Обратное ребро
                self.lowpt_edge[ei] = ei

                self.S.append(
                    ConflictPair(
                        right=Interval(ei, ei)
                    )
                )

            # Интеграция новых рёбер возврата
            if self.lowpt[ei] < self.height[v]:

                if i == 0:

                    self.lowpt_edge[e] = self.lowpt_edge[ei]

                else:

                    if not self.add_constraints(ei, e):
                        return False

        # После обработки потомков удаляем обратные рёбра
        if e is not None:
            self.remove_back_edges(e)

        return True


    # 6. Вычисление абсолютных сторон рёбер
    def sign(self, e):

        if self.ref[e] is not None:

            self.side[e] *= self.sign(self.ref[e])
            self.ref[e] = None

        return self.side[e]


    # 7. Построение планарной укладки
    def dfs_embedding(self, v):

        for w in self.ordered_adjs[v]:

            ei = (v, w)

            if self.parent_edge[w] == ei:

                # Добавляем ребро дерева в начало списка соседей потомка
                self.embedding.add_half_edge_first(w, v)

                self.left_ref[v] = w
                self.right_ref[v] = w

                self.dfs_embedding(w)

            else:

                # Размещаем обратное ребро слева или справа
                if self.side[ei] == 1:
                    self.embedding.add_half_edge(w, v, ccw=self.right_ref[w])

                else:
                    self.embedding.add_half_edge(w, v, cw=self.left_ref[w])
                    self.left_ref[w] = v


    # 8. Главный метод
    def check(self):

        # Быстрая проверка по формуле Эйлера
        if self.n > 2 and self.m > 3 * self.n - 6:
            return None

        # DFS-ориентация
        for v in self.nodes:

            if self.height[v] is None:

                self.height[v] = 0
                self.roots.append(v)

                self.dfs_orientation(v)

        # Сортировка рёбер по nesting_depth
        self.order_adjacencies()

        # Проверка конфликтов
        for root in self.roots:

            if not self.dfs_testing(root):
                return None

        # Вычисляем абсолютные стороны рёбер
        for v in self.nodes:
            for w in self.DG[v]:
                self.sign((v, w))

        # Сортировка с учётом стороны ребра
        self.order_adjacencies(signed=True)

        # Создаём объект комбинаторной укладки
        self.embedding = nx.PlanarEmbedding()

        self.embedding.add_nodes_from(self.nodes)

        # Инициализируем порядок полурёбер
        for v in self.nodes:
            previous_node = None

            for w in self.ordered_adjs[v]:
                self.embedding.add_half_edge(v, w, ccw=previous_node)
                previous_node = w

        # Строим окончательное вложение
        for root in self.roots:
            self.dfs_embedding(root)

        return self.embedding


def check_planarity(graph):
    """
    Проверяет планарность графа.

    Возвращает:
        (True, embedding) — граф планарен.
        (False, None) — граф непланарен.
    """

    algorithm = LRPlanarity(graph)
    embedding = algorithm.check()

    if embedding is None:
        return False, None

    embedding.check_structure()

    return True, embedding