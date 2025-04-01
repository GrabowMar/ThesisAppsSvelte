import { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [tasks, setTasks] = useState({});
  const [columns, setColumns] = useState([]);
  const [showNewTaskModal, setShowNewTaskModal] = useState(false);
  const [newTaskData, setNewTaskData] = useState({ title: '', description: '' });
  const [filterText, setFilterText] = useState('');

  // Fetch initial data
  useEffect(() => {
    fetch('/api/boards/default')
      .then(res => res.json())
      .then(data => {
        setColumns(data.columns);
        setTasks(data.tasks);
      });
  }, []);

  // Handle drag-end event
  const handleDragEnd = (result) => {
    if (!result.destination) return;

    fetch(`/api/tasks/${result.draggableId}/move`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        newColumnId: result.destination.droppableId,
        newIndex: result.destination.index
      })
    }).then(() => {
      const updatedTasks = { ...tasks };
      const task = updatedTasks[result.draggableId];
      
      // Remove from old column
      const sourceColumn = columns.find(c => c.id === task.column);
      sourceColumn.taskIds.splice(result.source.index, 1);
      
      // Add to new column
      const destColumn = columns.find(c => c.id === result.destination.droppableId);
      destColumn.taskIds.splice(result.destination.index, 0, result.draggableId);
      task.column = result.destination.droppableId;
      
      setColumns([...columns]);
    });
  };

  // Create new task
  const createTask = () => {
    fetch('/api/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newTaskData)
    })
      .then(res => res.json())
      .then(task => {
        setTasks({ ...tasks, [task.id]: task });
        setShowNewTaskModal(false);
      });
  };

  // Filtered tasks
  const filteredTasks = Object.values(tasks).filter(task =>
    task.title.toLowerCase().includes(filterText.toLowerCase()) ||
    task.description.toLowerCase().includes(filterText.toLowerCase())
  );

  return (
    <main>
      <div className="header">
        <h1>Kanban Board</h1>
        <div className="controls">
          <input
            type="text"
            placeholder="Filter tasks..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
          />
          <button onClick={() => setShowNewTaskModal(true)}>New Task</button>
        </div>
      </div>

      <DragDropContext onDragEnd={handleDragEnd}>
        <div className="board">
          {columns.map(column => (
            <Droppable key={column.id} droppableId={column.id}>
              {(provided) => (
                <div
                  className="column"
                  ref={provided.innerRef}
                  {...provided.droppableProps}
                >
                  <h2>{column.title}</h2>
                  <div className="tasks-list">
                    {column.taskIds
                      .filter(taskId => filteredTasks.some(t => t.id === taskId))
                      .map((taskId, index) => {
                        const task = tasks[taskId];
                        return (
                          <Draggable key={task.id} draggableId={task.id} index={index}>
                            {(provided) => (
                              <div
                                className="task-card"
                                ref={provided.innerRef}
                                {...provided.draggableProps}
                                {...provided.dragHandleProps}
                              >
                                <h3>{task.title}</h3>
                                <p>{task.description}</p>
                              </div>
                            )}
                          </Draggable>
                        );
                      })}
                    {provided.placeholder}
                  </div>
                </div>
              )}
            </Droppable>
          ))}
        </div>
      </DragDropContext>

      {showNewTaskModal && (
        <div className="modal">
          <div className="modal-content">
            <h2>Create New Task</h2>
            <input
              type="text"
              placeholder="Title"
              value={newTaskData.title}
              onChange={(e) => setNewTaskData({ ...newTaskData, title: e.target.value })}
            />
            <textarea
              placeholder="Description"
              value={newTaskData.description}
              onChange={(e) => setNewTaskData({ ...newTaskData, description: e.target.value })}
            />
            <button onClick={createTask}>Create</button>
            <button onClick={() => setShowNewTaskModal(false)}>Cancel</button>
          </div>
        </div>
      )}
    </main>
  );
};

// Mounting logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
