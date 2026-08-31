import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { register as apiRegister } from "../services/api";
import "../App.css";
import "../bootstrap.css";
import "./register.css";
import favicon from "../nursing_favicon.ico";

function Register() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [isLeader, setIsLeader] = useState(false);
  const [role, setRole] = useState("nurse");
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      // Create preview URL
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");

    // Validation
    if (!username.trim()) {
      setError("El nombre de usuario es requerido");
      return;
    }

    if (!email.trim()) {
      setError("El email es requerido");
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError("El email no es válido");
      return;
    }

    if (!password) {
      setError("La contraseña es requerida");
      return;
    }

    if (password.length < 8) {
      setError("La contraseña debe tener al menos 8 caracteres");
      return;
    }

    if (password !== confirmation) {
      setError("Las contraseñas no coinciden");
      return;
    }

    setLoading(true);
    try {
      await apiRegister(username, email, password, isLeader, role, image);
      setMessage("¡Registro exitoso! Redirigiendo a inicio de sesión...");
      setTimeout(() => {
        navigate("/login");
      }, 2000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const clearImage = () => {
    setImage(null);
    setImagePreview(null);
  };

  return (
    <div className="row mt-4">
      <div className="col-4"></div>
      <div className="text-center col-4">
        <div className="brand-logo mb-3">
          <img src={favicon} alt="Logo" width="80" height="80" />
        </div>
        <h2>Registrar</h2>

        {message && <div className="alert alert-success">{message}</div>}
        {error && <div className="alert alert-danger">{error}</div>}

        <form onSubmit={handleSubmit} encType="multipart/form-data">
          <div className="form-group">
            <input
              autoFocus
              className="form-control"
              type="text"
              name="username"
              placeholder="Nombre de Usuario"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <input
              className="form-control"
              type="email"
              name="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <input
              className="form-control"
              type="password"
              name="password"
              placeholder="Contraseña"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <input
              className="form-control"
              type="password"
              name="confirmation"
              placeholder="Confirmar Contraseña"
              value={confirmation}
              onChange={(e) => setConfirmation(e.target.value)}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <select
              className="form-control"
              name="role"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              disabled={loading}
            >
              <option value="nurse">Enfermero</option>
              <option value="doctor">Médico</option>
              <option value="office">Oficina</option>
            </select>
          </div>

          <div className="form-check mb-3">
            <input
              type="checkbox"
              className="form-check-input"
              id="is-leader"
              name="is-leader"
              checked={isLeader}
              onChange={(e) => setIsLeader(e.target.checked)}
              disabled={loading}
            />
            <label 
              className="form-check-label register-checkbox-label" 
              htmlFor="is-leader"
            >
              Es Encargado
            </label>
          </div>

          <div className="form-group">
            <div>
              <h6 className="d-inline">Agregar Foto</h6>
              <small> (opcional)</small>
            </div>
            {imagePreview && (
              <div className="mb-3">
                <img
                  src={imagePreview}
                  alt="Preview"
                  style={{
                    maxWidth: "150px",
                    maxHeight: "150px",
                    borderRadius: "8px",
                    marginTop: "10px",
                  }}
                />
                <div>
                  <button
                    type="button"
                    className="btn btn-sm btn-danger mt-2"
                    onClick={clearImage}
                    disabled={loading}
                  >
                    Eliminar Foto
                  </button>
                </div>
              </div>
            )}
            <input
              className="form-control"
              type="file"
              name="image"
              accept="image/*"
              onChange={handleImageChange}
              disabled={loading}
            />
          </div>

          <button
            className="btn btn-primary"
            type="submit"
            disabled={loading}
          >
            {loading ? "Registrando..." : "Registrar"}
          </button>
        </form>
      </div>
      <div className="col-4"></div>
    </div>
  );
}

export default Register;
