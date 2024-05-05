from pathlib import Path

import geopandas as gpd  # type: ignore
import momepy
import networkx as nx
import pandana as pdna
from shapely.ops import unary_union  # type: ignore


def get_roads_data(
    file_path: Path | str,
    layer: str | None = None,
    crs: int | None = None,
    subset_fields: list | None = None,
    subset_categories: list | None = None,
) -> gpd.GeoDataFrame:
    file_path = Path(file_path)
    if file_path.suffix == ".shp":
        roads = gpd.read_file(file_path, layer=layer)
    elif file_path.suffix == ".gpkg":
        roads = gpd.read_file(file_path, layer=layer)
    else:
        raise ValueError("File type not supported. Please use shapefile or geopackage.")

    if crs:
        roads = roads.to_crs(crs)
    if subset_fields:
        subset_fields.append("geometry")
        roads = roads[subset_fields]
    if subset_categories:
        roads = roads[roads["fclass"].isin(subset_categories)]
    return roads


def fix_topology(gdf: gpd.GeoDataFrame, crs: int, len_segments: int = 1000):
    gdf = gdf.to_crs(f"EPSG:{crs}")
    merged = unary_union(gdf.geometry)
    geom = merged.segmentize(max_segment_length=len_segments)
    roads_multi = gpd.GeoDataFrame(
        data={"id": [1], "geometry": [geom]}, crs=f"EPSG:{crs}"
    )
    gdf_roads = roads_multi.explode(ignore_index=True)
    gdf_roads["length"] = gdf_roads.length
    return gdf_roads


def make_graph(gdf: gpd.GeoDataFrame) -> pdna.Network:
    G_prep = momepy.gdf_to_nx(gdf, approach="primal")
    components = list(nx.connected_components(G_prep))
    largest_component = max(components, key=len)
    G = G_prep.subgraph(largest_component)

    nodes, edges, _ = momepy.nx_to_gdf(G, points=True, lines=True, spatial_weights=True)
    net = pdna.Network(
        nodes.geometry.x,
        nodes.geometry.y,
        edges.node_start,
        edges.node_end,
        edges[["length"]],
    )
    net.precompute(5000)
    return net, edges


# - ROADS ---------------------------------------------------------------------

# - BOUNDARIES ---------------------------------------------------------------------
# Read shapefile or geopackage and subset by administrative level

# calculate the centroid based on pop or geometric centroid

# ------ ACLED ---------------------------------------------------------------------
# Access api and get the data for the dates required

# Save the data to a csv

# Convert to point dataset
