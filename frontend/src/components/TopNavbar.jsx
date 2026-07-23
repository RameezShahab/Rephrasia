function TopNavbar() {
  return (
    <div style={{
      height: "60px",
      background: "#105252",
      color: "white",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "0 20px"
    }}>
      <h2 style={{ color: "#2fc4d4" }}>
  RephrasiaAI
</h2>
      <div>
        <span style={{ marginRight: "15px" }}>Profile</span>
        <button style={{
          padding: "6px 12px",
          background: "#2fc4d4",
          border: "none",
          color: "white",
          borderRadius: "5px"
        }}>
          Logout
        </button>
      </div>
    </div>
  );
}
export default TopNavbar;
