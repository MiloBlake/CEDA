import axios from "axios";
import "./styles/FileUpload.css";

export default function FileUploader({ onFileUploaded }) {
  const uploadFile = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    const res = await axios.post("http://localhost:5000/upload", formData);
    onFileUploaded(res.data);
  };

  return (
    <div className="file-uploader">
      <label className="upload-button">
        Upload CSV
        <input
          type="file"
          accept=".csv"
          onChange={uploadFile}
          className="hidden-input"
        />
      </label>
      <span className="upload-text">
        Upload your dataset to get started!
      </span>
    </div>
  );
}
