import axios from "axios";
import { useState } from "react";
import "./styles/FileUpload.css";

export default function FileUploader({ onFileUploaded }) {
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = async (file) => {
    if (!file || !file.name.endsWith('.csv')) {
      alert("Please upload a CSV file");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post("http://localhost:5000/upload", formData);
      onFileUploaded(res.data);
    } catch (error) {
      alert("Upload failed");
      console.error(error);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    handleFile(file);
  };

  const handleFileInput = (e) => {
    const file = e.target.files[0];
    if (file) handleFile(file);
  };

  return (
    <div
      className={`file-uploader ${isDragging ? "dragging" : ""}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <label htmlFor="csv-input" className="upload-button">
        <input
          id="csv-input"
          type="file"
          accept=".csv"
          onChange={handleFileInput}
          className="hidden-input"
        />
        <span className="upload-text">
          Drag CSV files here or click to browse!
        </span>
      </label>
    </div>
  );
}
