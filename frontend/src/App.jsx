import { useState } from "react";
import ChatBox from "./components/ChatBox";
import FileUpload from "./components/FileUpload";

function App() {
  const [columns, setColumns] = useState([]);

  const handleFileUploaded = (metadata) => {
    setColumns(metadata.columns);
  };

  return (
    <div style={{ fontFamily: "sans-serif", padding: 20 }}>
      <h1>Data Analysis Chatbot</h1>
      <FileUpload onFileUploaded={handleFileUploaded} />
      {columns.length > 0 && (
        <p>
          Uploaded dataset
          {columns.join(", ")}
        </p>
      )}
      <ChatBox />
    </div>
  );
}

export default App;
