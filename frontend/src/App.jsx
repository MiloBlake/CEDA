import { useState } from "react";
import ChatBox from "./components/ChatBox";
import FileUploader from "./components/FileUpload";
import Header from "./components/Header";

function App() {
  const [dataset, setDataset] = useState(null);
  const [welcomeMessage, setWelcomeMessage] = useState(null);

  const handleFileUploaded = (data) => {
    setDataset(data);
    setWelcomeMessage(data.message);
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
          <ChatBox welcomeMessage={`File uploaded!

Welcome to CEDA. Here's what you can do:

Perform calculations: average, sum, min, max, count
Generate visualisations: bar, scatter, line, pie, histogram, box plot
Selection Analysis: Select part of a chart, then type 'analyse' to get AI insights!

Examples:
• 'list columns' - See all available data columns
• 'average [column]' - Calculate average of a column
• 'bar chart of [column] vs [column]' - Create visualisations
• 'analyse' - Get LLM analysis of your selection`} />
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