from sqlalchemy import Column, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=True)  # stored as whatsapp:+27821234567

    shifts = relationship("Shift", back_populates="member", cascade="all, delete-orphan")


class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    role = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String, nullable=True)  # None | pending | accepted | rejected

    member = relationship("Member", back_populates="shifts")

    __table_args__ = (
        UniqueConstraint("member_id", "role", "date", name="unique_shift"),
    )
