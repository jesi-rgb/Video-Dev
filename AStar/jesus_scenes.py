from geopandas import GeoDataFrame
from manim import Circle, FadeIn, FadeOut, config
from networkx import MultiDiGraph
from osmnx import graph_from_place, graph_to_gdfs, plot_graph

import sys

import pandas as pd
from pandas import DataFrame

sys.path.insert(1, "common/")

from reducible_colors import *
from classes import CustomLabel

from astar_scene import AGraph, AstarAnimationTools


class Introduction(AstarAnimationTools):
    def construct(self):

        G: MultiDiGraph = graph_from_place("Baeza, Jaén, España", network_type="drive")
        gdfs: GeoDataFrame = graph_to_gdfs(G, node_geometry=False)[0]
        gdfs_layout = gdfs[["x", "y"]].to_dict()

        edges = list(filter(lambda x: type(x) is tuple, list(G.edges)))

        print(edges)
        graph = AGraph(G.nodes, edges)

        # manhattan_graph = AGraph(G.nodes, G.edges)
        # self.play(FadeIn(manhattan_graph))
        # self.wait()
