import { useContext } from "react";
import { useNavigate, Link } from "react-router-dom";
import { logout as apiLogout, getUser } from "../services/api";
import AppContext from "../context/appContext";
import favicon from "../nursing_favicon.ico";
import "./footer.css";

function Footer() {
  const navigate = useNavigate();
  const [appState] = useContext(AppContext);
  
  const user = getUser();
  const bedsOccupied = appState?.beds ? appState.beds.filter(bed => bed.bed_active).length : 0;
  const canRegister = user?.is_superuser === true || (user?.is_leader === true && user?.role === 'doctor');

  const handleLogout = async () => {
    if (window.confirm("¿Está seguro de que desea cerrar sesión?")) {
      apiLogout();
      navigate("/login");
    }
  };

  return (
    <footer className="app-footer">
      <div className="footer-content">
        <div className="footer-section">
          <img src={favicon} alt="Logo" width="28" height="28" className="footer-logo" />
          <span className="footer-label">Usuario:</span>
          <span className="footer-value">{user?.username || "Anónimo"}</span>
        </div>
        
        <div className="footer-section">
          <span className="footer-label">Camas Ocupadas:</span>
          <span className="footer-value">{bedsOccupied}</span>
        </div>

        {canRegister && (
          <div className="footer-section">
            <Link to="/register" className="btn btn-sm btn-primary" title="Registrar nuevo usuario">
              Nuevo Usuario
            </Link>
          </div>
        )}

        <div className="footer-section">
          <button
            className="btn btn-sm btn-danger"
            onClick={handleLogout}
            title="Cerrar sesión"
          >
            Logout
          </button>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
