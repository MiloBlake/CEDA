export default function Header() {
  return (
    <div
      style={{
        backgroundColor: "#a80050",
        color: "white",
        padding: "18px",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
        borderBottom: "1px solid rgba(255,255,255,0.2)",
      }}
    >
      <h1
        style={{
          margin: 0,
          fontSize: "26px",
          fontWeight: "600",
          letterSpacing: "0.5px",
        }}
      >
        Steffy
      </h1>
    </div>
  );
}
