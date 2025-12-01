from sqlalchemy import Boolean, Column, Integer, String, Text, text

from database import Base


class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(255), nullable=False)
    url = Column(String(2048), nullable=False)
    ordem = Column(Integer, nullable=False, default=0)
    descricao = Column(Text, nullable=True)
    icone = Column(String(255), nullable=True)
    publicado = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
        default=True,
    )
