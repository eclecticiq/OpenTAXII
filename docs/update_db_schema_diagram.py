#!/bin/env python3
import os
import sys

current_dir = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(current_dir, "..")))

from opentaxii.persistence.sqldb.models import Base
from sqla_graphs import TableGrapher

grapher = TableGrapher(
    style={"node_table_header": {"bgcolor": "#000080"}},
    graph_options={"size": "30,30!"},  # inches, this maps to 2880px
)
graph = grapher.graph(tables=Base.metadata.tables.values())
graph.write_png(os.path.join(current_dir, "db_schema_diagram.png"), prog="dot")
