from app.db import Base, engine
from app.models import tables  # Import your models

Base.metadata.create_all(bind=engine)
print("✅ Tables created successfully!")
