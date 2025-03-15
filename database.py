from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL (Modify according to your credentials)
DATABASE_URL = "postgresql://postgres:newpassword@localhost:5432/invoice_db"


# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# Invoice Table Model
class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    extracted_data = Column(Text, nullable=False)

# Create the table
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
