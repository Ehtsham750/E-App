from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import SQLModel, Field, create_engine, Session, select
from e_aap import setting
from typing import Annotated
from contextlib import asynccontextmanager

# Create Model
class Todo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True) 
    content: str = Field(index=True, min_length=3, max_length=54)
    is_compleate: bool = Field(default=False)

# Create single engine for the entire application
connection_string = str(setting.DATABASE_URL).replace("postgresql", "postgresql+psycopg")
engine = create_engine(connection_string, connect_args={"sslmode": "require"}, pool_recycle=300, pool_size=10, echo=True)

# This will create tables
def create_tables():
    SQLModel.metadata.create_all(engine)

# Dependency to get a session
def get_session():
    with Session(engine) as session:
        yield session  # Yield the session, not the Session class

# First thing to do at the start of the application
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating Tables")
    create_tables()
    print("Tables are ready")
    yield

app = FastAPI(lifespan=lifespan, title="E-aap", version="0.0.1") 

@app.get('/')
async def root():
    return {"message": "WELCOME TO PP"}

@app.post('/todo/', response_model=Todo)
async def create_todo(todo: Todo, session: Annotated[Session, Depends(get_session)]):
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo

@app.get('/todo/', response_model=list[Todo])
async def get_all(session: Annotated[Session, Depends(get_session)]):
    result = session.execute(select(Todo))  # Correctly execute the query
    todos = result.scalars().all()  # Extract the list of todos
    if todos:  # Change 'todo' to 'todos' for clarity
        return todos
    else:
        raise HTTPException(status_code=404, detail="No task at this time")

@app.get('/todo/{id}', response_model=Todo)  # Fix the endpoint path
async def get_single_todo(id: int, session: Annotated[Session, Depends(get_session)]):
    result = session.execute(select(Todo).where(Todo.id == id))
    todo = result.scalar_one_or_none()  # Use scalar_one_or_none for better error handling
    if todo:
        return todo
    else:
        raise HTTPException(status_code=404, detail="No task at this time")

@app.put('/todo/{id}')  # Fix the endpoint path
async def edit_todo(id: int, todo: Todo, session: Annotated[Session, Depends(get_session)]):
    result = session.execute(select(Todo).where(Todo.id == id))
    existing_todo = result.scalar_one_or_none()
    if existing_todo:
        existing_todo.content = todo.content  # Fix typo from 'comtent' to 'content'
        existing_todo.is_compleate = todo.is_compleate  # Fix typo from 'is_completed' to 'is_compleate'
        session.commit()
        session.refresh(existing_todo)
        return existing_todo
    else:
        raise HTTPException(status_code=404, detail="No task at this time")

@app.delete('/todo/{id}')  # Fix the endpoint path
async def delete_todo(id: int, session: Annotated[Session, Depends(get_session)]):
    result = session.execute(select(Todo).where(Todo.id == id))
    todo = result.scalar_one_or_none()
    if todo:
        session.delete(todo)
        session.commit()
        return {"message": "Deleted as you asked"}
    else:
        raise HTTPException(status_code=404, detail="No task at this time")