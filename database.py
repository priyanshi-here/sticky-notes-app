from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://admin:r4-lZ5EvYVmh26402ekDiQaNdLaU_C@us-east-1.2ba28f65-c87b-4216-9b0c-fc4f7455d993.aws.yugabyte.cloud::5433/notesdb"
#postgresql+asyncpg://admin:r4-lZ5EvYVmh26402ekDiQaNdLaU_C@us-east-1.2ba28f65-c87b-4216-9b0c-fc4f7455d993.aws.yugabyte.cloud::5433/notesdb

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
