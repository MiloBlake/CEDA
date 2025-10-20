import axios from "axios";

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
    <div>
      <input type="file" onChange={uploadFile} />
    </div>
  );
}
