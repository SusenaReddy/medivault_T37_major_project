import { Link } from "react-router-dom";

function Home() {
  return (
    <div style={{ textAlign: "center", marginTop: "100px" }}>
      <h1>Welcome to MediVault</h1>
      <p>Secure Healthcare Management Platform</p>
      <Link to="/roles">
        <button>Select Your Role</button>
      </Link>
    </div>
  );
}

export default Home;