import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { getEvents, getEvent, getUser } from "../../services/api";
import "./events-list.css";

function EventsList() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [events, setEvents] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortField, setSortField] = useState("time");
  const [sortOrder, setSortOrder] = useState("desc");

  const user = getUser();
  const isSuperuser = user?.is_superuser === true;

  useEffect(() => {
    if (!isSuperuser) {
      setLoading(false);
      return;
    }

    const fetchEvents = async () => {
      try {
        const data = await getEvents();
        setEvents(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, [isSuperuser]);

  useEffect(() => {
    if (!id || !isSuperuser) {
      setSelectedEvent(null);
      return;
    }

    const fetchEvent = async () => {
      try {
        const data = await getEvent(id);
        setSelectedEvent(data);
      } catch (err) {
        setError(err.message);
      }
    };

    fetchEvent();
  }, [id, isSuperuser]);

  const parseSemicolonData = (dataStr) => {
    if (!dataStr || dataStr === "No Before" || dataStr === "No After") {
      return [];
    }
    return dataStr.split(";").filter(item => item.trim() !== "");
  };

  const filteredRecords = events.filter((event) => {
    const searchLower = searchTerm.toLowerCase();
    return (
      event.loged_user?.toLowerCase().includes(searchLower) ||
      event.action?.toLowerCase().includes(searchLower) ||
      event.before?.toLowerCase().includes(searchLower) ||
      event.after?.toLowerCase().includes(searchLower)
    );
  });

  const sortedRecords = [...filteredRecords].sort((a, b) => {
    let aVal, bVal;

    switch (sortField) {
      case "time":
        aVal = new Date(a.time);
        bVal = new Date(b.time);
        break;
      case "user":
        aVal = a.loged_user || "";
        bVal = b.loged_user || "";
        break;
      case "action":
        aVal = a.action || "";
        bVal = b.action || "";
        break;
      default:
        return 0;
    }

    if (sortOrder === "asc") {
      return aVal > bVal ? 1 : -1;
    }
    return aVal < bVal ? 1 : -1;
  });

  const handleSort = (field) => {
    if (sortField === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortOrder("desc");
    }
  };

  const formatDateTime = (isoString) => {
    if (!isoString) return "";
    const date = new Date(isoString);
    return date.toLocaleString('es-AR');
  };

  const getSortIndicator = (field) => {
    if (sortField !== field) return "";
    return sortOrder === "asc" ? " ▲" : " ▼";
  };

  const exportToCsv = () => {
    const rows = [["Fecha/Hora", "Usuario", "Acción", "Antes", "Después"]];
    
    sortedRecords.forEach((event) => {
      const before = event.before === "No Before" ? "" : event.before.replace(/;/g, ", ");
      const after = event.after === "No After" ? "" : event.after.replace(/;/g, ", ");
      rows.push([
        formatDateTime(event.time),
        event.loged_user,
        event.action,
        before,
        after,
      ]);
    });

    const escapeCsv = (str) => {
      if (str === null || str === undefined) return "";
      const escaped = String(str).replace(/"/g, '""');
      return `"${escaped}"`;
    };

    const csvContent = rows
      .map((row) => row.map(escapeCsv).join(","))
      .join("\n");

    const blob = new Blob(["\ufeff" + csvContent], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `eventos_${new Date().toISOString().split("T")[0]}.csv`);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  if (!isSuperuser) {
    return (
      <div className="container mt-4">
        <div className="alert alert-danger">
          <h4>Acceso Denegado</h4>
          <p>No tienes permisos de superusuario para acceder a esta página.</p>
          <Link to="/" className="btn btn-primary">Volver al Inicio</Link>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="container mt-4">
        <div className="text-center">
          <p className="text-info">Cargando eventos...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mt-4">
        <div className="alert alert-danger">
          <h4>Error</h4>
          <p>{error}</p>
          <button onClick={() => window.location.reload()} className="btn btn-primary">
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="events-container">
      <div className="events-header">
        <h2>Eventos del Sistema</h2>
        <Link to="/" className="btn btn-secondary btn-sm">
          Volver al Inicio
        </Link>
      </div>

      <div className="events-controls mb-3">
        <div className="row">
          <div className="col-md-6">
            <input
              type="text"
              className="form-control"
              placeholder="Buscar en eventos..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="col-md-6 d-flex justify-content-between align-items-center">
            <span className="text-muted">
              Mostrando {sortedRecords.length} de {events.length} eventos
            </span>
            <button
              className="btn btn-sm btn-success"
              onClick={exportToCsv}
              title="Exportar a CSV"
            >
              Exportar CSV
            </button>
          </div>
        </div>
      </div>

      <div className="events-content">
        <div className="events-list-section">
          <div className="events-table-wrapper">
            <table className="table table-striped table-hover">
              <thead className="thead-dark">
                <tr>
                  <th
                    onClick={() => handleSort("time")}
                    style={{ cursor: "pointer" }}
                  >
                    Fecha/Hora{getSortIndicator("time")}
                  </th>
                  <th
                    onClick={() => handleSort("user")}
                    style={{ cursor: "pointer" }}
                  >
                    Usuario{getSortIndicator("user")}
                  </th>
                  <th
                    onClick={() => handleSort("action")}
                    style={{ cursor: "pointer" }}
                  >
                    Acción{getSortIndicator("action")}
                  </th>
                  <th>Antes</th>
                  <th>Después</th>
                </tr>
              </thead>
              <tbody>
                {sortedRecords.map((event) => (
                  <tr
                    key={event.id}
                    onClick={() => navigate(`/events/${event.id}`)}
                    className={selectedEvent?.id === event.id ? "table-primary" : ""}
                    style={{ cursor: "pointer" }}
                  >
                    <td>{formatDateTime(event.time)}</td>
                    <td>{event.loged_user}</td>
                    <td>{event.action}</td>
                    <td className="text-truncate" style={{ maxWidth: "150px" }}>
                      {event.before === "No Before" ? "-" : event.before.substring(0, 50)}
                      {event.before.length > 50 ? "..." : ""}
                    </td>
                    <td className="text-truncate" style={{ maxWidth: "150px" }}>
                      {event.after === "No After" ? "-" : event.after.substring(0, 50)}
                      {event.after.length > 50 ? "..." : ""}
                    </td>
                  </tr>
                ))}
                {sortedRecords.length === 0 && (
                  <tr>
                    <td colSpan="5" className="text-center text-muted">
                      No se encontraron eventos
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {selectedEvent && (
          <div className="event-detail-section">
            <div className="card">
              <div className="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                <h5 className="mb-0">Detalle del Evento #{selectedEvent.id}</h5>
                <button
                  className="btn btn-sm btn-light"
                  onClick={() => navigate("/events")}
                >
                  Cerrar
                </button>
              </div>
              <div className="card-body">
                <div className="row mb-3">
                  <div className="col-md-6">
                    <strong>Usuario:</strong> {selectedEvent.loged_user}
                  </div>
                  <div className="col-md-6">
                    <strong>Acción:</strong> {selectedEvent.action}
                  </div>
                </div>
                <div className="row mb-3">
                  <div className="col-md-12">
                    <strong>Fecha/Hora:</strong> {formatDateTime(selectedEvent.time)}
                  </div>
                </div>

                <hr />

                <div className="event-data-columns">
                  <div className="event-data-column">
                    <h6 className="text-muted mb-2 column-header">Datos Anteriores (Antes):</h6>
                    <div className="data-list">
                      {parseSemicolonData(selectedEvent.before).length > 0 ? (
                        <ul className="list-group">
                          {parseSemicolonData(selectedEvent.before).map((item, index) => (
                            <li key={`before-${index}`} className="list-group-item">
                              {item}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-muted">No hay datos anteriores</p>
                      )}
                    </div>
                  </div>

                  <div className="event-data-column">
                    <h6 className="text-muted mb-2 column-header">Datos Nuevos (Después):</h6>
                    <div className="data-list">
                      {parseSemicolonData(selectedEvent.after).length > 0 ? (
                        <ul className="list-group">
                          {parseSemicolonData(selectedEvent.after).map((item, index) => (
                            <li key={`after-${index}`} className="list-group-item">
                              {item}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-muted">No hay datos nuevos</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default EventsList;
