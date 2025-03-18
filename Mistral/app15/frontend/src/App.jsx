import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import axios from 'axios';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import './App.css';

const App = () => {
  const [boards, setBoards] = useState([]);
  const [currentBoard, setCurrentBoard] = useState(null);
  const [newBoardName, setNewBoardName] = useState('');
  const [newColumnName, setNewColumnName] = useState('');
  const [newTaskName, setNewTaskName] = useState('');
  const [filter, setFilter] = useState('');

  useEffect(() => {
    fetchBoards();
  }, []);

  const fetchBoards = async () => {
    const response = await axios.get('http://localhost:5349/boards');
    setBoards(response.data);
  };

  const createBoard = async () => {
    const response = await axios.post('http://localhost:5349/boards', {
      id: Date.now().toString(),
      name: newBoardName,
    });
    fetchBoards();
    setNewBoardName('');
  };

  const createColumn = async (boardId) => {
    const response = await axios.post(`http://localhost:5349/boards/${boardId}/columns`, {
      id: Date.now().toString(),
      name: newColumnName,
    });
    fetchBoards();
    setNewColumnName('');
  };

  const createTask = async (boardId, columnId) => {
    const response = await axios.post(`http://localhost:5349/boards/${boardId}/columns/${columnId}/tasks`, {
      id: Date.now().toString(),
      name: newTaskName,
    });
    fetchBoards();
    setNewTaskName('');
  };

  const updateTask = async (boardId, columnId, taskId, newName) => {
    const response = await axios.put(`http://localhost:5349/boards/${boardId}/columns/${columnId}/tasks/${taskId}`, {
      name: newName,
    });
    fetchBoards();
  };

  const deleteTask = async (boardId, columnId, taskId) => {
    const response = await axios.delete(`http://localhost:5349/boards/${boardId}/columns/${columnId}/tasks/${taskId}`);
    fetchBoards();
  };

  const onDragEnd = (result) => {
    const { source, destination } = result;
    if (!destination) return;

    const boardId = currentBoard.id;
    const sourceColumnId = source.droppableId;
    const destColumnId = destination.droppableId;

    const sourceTasks = boards[boardId].columns[sourceColumnId].tasks;
    const destTasks = boards[boardId].columns[destColumnId].tasks;

    const [movedTask] = sourceTasks.splice(source.index, 1);
    destTasks.splice(destination.index, 0, movedTask);

    setBoards({
      ...boards,
      [boardId]: {
        ...boards[boardId],
        columns: {
          ...boards[boardId].columns,
          [sourceColumnId]: {
            ...boards[boardId].columns[sourceColumnId],
            tasks: sourceTasks,
          },
          [destColumnId]: {
            ...boards[boardId].columns[destColumnId],
            tasks: destTasks,
          },
        },
      },
    });
  };

  return (
    <div className="app">
      <div className="board-selector">
        <select onChange={(e) => setCurrentBoard(boards.find(b => b.id === e.target.value))}>
          {boards.map(board => (
            <option key={board.id} value={board.id}>{board.name}</option>
          ))}
        </select>
        <input
          type="text"
          value={newBoardName}
          onChange={(e) => setNewBoardName(e.target.value)}
          placeholder="New Board Name"
        />
        <button onClick={createBoard}>Create Board</button>
      </div>
      {currentBoard && (
        <div className="board">
          <h2>{currentBoard.name}</h2>
          <input
            type="text"
            value={newColumnName}
            onChange={(e) => setNewColumnName(e.target.value)}
            placeholder="New Column Name"
          />
          <button onClick={() => createColumn(currentBoard.id)}>Create Column</button>
          <DragDropContext onDragEnd={onDragEnd}>
            {Object.keys(currentBoard.columns).map(columnId => (
              <Droppable droppableId={columnId} key={columnId}>
                {(provided) => (
                  <div
                    className="column"
                    {...provided.droppableProps}
                    ref={provided.innerRef}
                  >
                    <h3>{currentBoard.columns[columnId].name}</h3>
                    {currentBoard.columns[columnId].tasks.map((task, index) => (
                      <Draggable key={task.id} draggableId={task.id} index={index}>
                        {(provided) => (
                          <div
                            className="task"
                            {...provided.draggableProps}
                            {...provided.dragHandleProps}
                            ref={provided.innerRef}
                          >
                            <input
                              type="text"
                              value={task.name}
                              onChange={(e) => updateTask(currentBoard.id, columnId, task.id, e.target.value)}
                            />
                            <button onClick={() => deleteTask(currentBoard.id, columnId, task.id)}>Delete</button>
                          </div>
                        )}
                      </Draggable>
                    ))}
                    {provided.placeholder}
                    <input
                      type="text"
                      value={newTaskName}
                      onChange={(e) => setNewTaskName(e.target.value)}
                      placeholder="New Task Name"
                    />
                    <button onClick={() => createTask(currentBoard.id, columnId)}>Create Task</button>
                  </div>
                )}
              </Droppable>
            ))}
          </DragDropContext>
        </div>
      )}
    </div>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
