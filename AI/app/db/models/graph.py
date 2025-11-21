from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, int_pk


class GraphNode(Base):
    __tablename__ = "graph_nodes"

    id: Mapped[int_pk]
    node_type: Mapped[str] = mapped_column(String(64))
    label: Mapped[str] = mapped_column(String(255))
    embedding_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    properties: Mapped[dict] = mapped_column(JSONB, default=dict)

    outgoing_edges: Mapped[list["GraphEdge"]] = relationship(
        "GraphEdge", back_populates="source_node", foreign_keys="GraphEdge.source_id"
    )
    incoming_edges: Mapped[list["GraphEdge"]] = relationship(
        "GraphEdge", back_populates="target_node", foreign_keys="GraphEdge.target_id"
    )


class GraphEdge(Base):
    __tablename__ = "graph_edges"

    id: Mapped[int_pk]
    source_id: Mapped[int] = mapped_column(ForeignKey("graph_nodes.id", ondelete="CASCADE"))
    target_id: Mapped[int] = mapped_column(ForeignKey("graph_nodes.id", ondelete="CASCADE"))
    relation_type: Mapped[str] = mapped_column(String(64))
    properties: Mapped[dict] = mapped_column(JSONB, default=dict)

    source_node: Mapped[GraphNode] = relationship(
        "GraphNode", foreign_keys=[source_id], back_populates="outgoing_edges"
    )
    target_node: Mapped[GraphNode] = relationship(
        "GraphNode", foreign_keys=[target_id], back_populates="incoming_edges"
    )

