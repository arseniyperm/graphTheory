import networkx as nx
import matplotlib.pyplot as plt

from planar import check_planarity


def visualize_planar_graph(G, embedding):

    # Получаем координаты из готовой укладки.
    pos = nx.planar_layout(embedding)

    plt.figure(figsize=(9, 7))

    nx.draw_networkx(
        G,
        pos=pos,
        node_color="lightblue",
        edge_color="black",
        node_size=800,
        font_size=12,
        font_weight="bold",
        width=1.5
    )

    plt.title("Planar graph embedding")
    plt.axis("off")
    plt.tight_layout()
    plt.show()


def test_graph(G, name):

    print(f"\nПроверка графа: {name}")
    print(f"Вершины: {G.number_of_nodes()}")
    print(f"Рёбра: {G.number_of_edges()}")

    planar, embedding = check_planarity(G)

    if planar:

        print("Результат: граф планарен")

        visualize_planar_graph(G, embedding)

    else:

        print("Результат: граф непланарен")


# Тест 1. Цикл
G1 = nx.cycle_graph(6)

# Тест 2. Полный граф K4
G2 = nx.complete_graph(4)

# Тест 3. Полный граф K5
G3 = nx.complete_graph(5)

# Тест 4. Полный двудольный граф K3,3
G4 = nx.complete_bipartite_graph(3, 3)

# Тест 5. Планарная решётка
G5 = nx.grid_2d_graph(4, 4)


test_graph(G1, "Цикл C6")
test_graph(G2, "Полный граф K4")
test_graph(G3, "Полный граф K5")
test_graph(G4, "Полный двудольный граф K3,3")
test_graph(G5, "Решётка 4x4")
