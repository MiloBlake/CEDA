import { useState } from "react";
import ChatBox from "./components/ChatBox";
import FileUploader from "./components/FileUpload";

function App() {
  const [datasetUploaded, setDatasetUploaded] = useState(false);

  const handleFileUploaded = (data) => {
    setDatasetUploaded(true);
    alert("File uploaded successfully!");
  };

  return (
    <div style={{ padding: 20, maxWidth: 800, margin: "0 auto" }}>
      {!datasetUploaded ? (
        <FileUploader onFileUploaded={handleFileUploaded} />
      ) : (
        <ChatBox />
      )}
    </div>
  );
}

export default App;