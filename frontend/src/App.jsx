import { useState } from "react";
import ChatBox from "./components/ChatBox";
import FileUploader from "./components/FileUpload";
import Header from "./components/Header";

function App() {
  const [dataset, setDataset] = useState(null);

  const handleFileUploaded = (data) => {
    setDataset(data);
  };

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <Header dataset={dataset} />
      
      <div style={{ 
        flex: 1, 
        display: "flex",
        backgroundColor: "#f8f9fa",
        flexDirection: "column",
      }}>
        {dataset ? (
          <ChatBox />
        ) : (
          <div style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            height: "100%",
            color: "#666",
            textAlign: "center"
          }}>
            <div style={{marginBottom: "20px" }}></div>
            <img src="/logo.png" alt="Logo" />
            <h2 style={{ fontSize: "50px" }}>Conversational Exploratory Data Analysis</h2>
            {!dataset && <FileUploader onFileUploaded={handleFileUploaded} />}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;