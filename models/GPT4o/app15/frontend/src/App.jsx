import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";

const API_BASE = "http://localhost:5269/api";

function App() {
  const [board, setBoard] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch board data from the backend
  useEffect(() => {
    fetch(`${API_BASE}/board`)
      .then((res) => res.json())
      .then((data) => {
        setBoard(data.columns);
        setLoading(false);
      })
      .catch((err) => console.error("Error fetching board:", err));
  }, []);

  // Create new task
  const createTask = (columnId, title, description) => {
    const newTask = { column_id: columnId, title, description };
    fetch(`${API_BASE}/task`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(newTask),
    })
      .then((res) => res.json())
      .then((task) => {
        setBoard((prevBoard) =>
          prevBoard.map((col) =>
            col.id === columnId ? { ...col, tasks: [...col.tasks, task] } : col
          )
        );
      })
      .catch((err) => console.error("Error creating task:", err));
  };

  // Drag-and-drop logic
  const onDragEnd = (taskId, targetColId) => {
    fetch(`${API_BASE}/task/${taskId}/move`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_column_id: targetColId }),
    })
      .then((res) => {
        if (res.ok) {
          setBoard((prevBoard) => {
            // Remove task from original column
            let taskToMove;
            const updatedBoard = prevBoard.map((col) => {
              if (col.tasks.some((task) => task.id === taskId)) {
                taskToMove = col.tasks.find((task) => task.id === taskId);
                return {
                  ...col,
                  tasks: col.tasks.filter((task) => task.id !== taskId),
                };
              }
              return col;
            });

            // Add task to target column
            return updatedBoard.map((col) =>
              col.id === targetColId
                ? { ...col, tasks: [...(col.tasks || []), taskToMove] }
                : col
            );
          });
        }
      })
      .catch((err) => console.error("Error moving task:", err));
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="kanban-board">
      {board.map((col) => (
        <div className="column" key={col.id}>
          <h2>{col.name}</h2>
          {col.tasks.map((task) => (
            <div
              className="task"
              key={task.id}
              draggable
              onDragEnd={() => onDragEnd(task.id, col.id)}
            >
              <h3>{task.title}</h3>
              <p>{task.description}</p>
            </div>
          ))}
          <button onClick={() => createTask(col.id, "New Task", "Task details")}>
            Add Task
          </button>
        </div>
      ))}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
