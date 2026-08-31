import { useEffect, useContext, useState } from "react";
import { useNavigate, Routes, Route } from "react-router-dom";
import "./App.css";
import "./bootstrap.css";
import { fetchLoad, logout } from "./services/api";
import { appManager } from "./services/websocket";
import Sketch from "./components/rooms-beds-sketch/Sketch";
import CallsList from "./components/calls-list/CallsList";
import TasksList from "./components/tasks-list/TasksList";
import Footer from "./components/Footer";
import AppContext from "./context/appContext";
import EventsList from "./components/events-list/EventsList";

function HealthApp() {
  const [appState, setAppState] = useContext(AppContext);
  const [localAppState, setLocalAppState] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const places = {
    numBeds: 4,
    numRooms: 30,
  };

  const handleApp = (msg) => {
    if (msg) {
      setAppState(msg);
      setLocalAppState(msg);
    }
  };

  useEffect(() => {
    const init = async () => {
      try {
        const data = await fetchLoad();
        setAppState(data);
        setLocalAppState(data);
      } catch (error) {
        console.error("Failed to load initial data:", error);
        logout();
        navigate("/login");
      } finally {
        setLoading(false);
      }
    };

    init();
    
    const ws = appManager({ handleApp });
    
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [navigate, setAppState]);

  if (loading) {
    return (
      <>
        <p className="bg-info text-white loading-text">Loading ... </p>
        <p className="bg-info text-white loading-text">
          Please wait a moment.
        </p>
        <p className="bg-secondary text-white loading-text">
          If this takes too long then you can press F5
        </p>
      </>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <div className="container justify-content-center" style={{ flex: 1 }}>
        <Routes>
          <Route path="/" element={
            <div className="row">
              <div className="col-2">
                <TasksList key={"tasksComponent"} places={places} />
              </div>
              <div className="col-8">
                <Sketch key={"sketchComponent"} places={places} />
              </div>
              <div className="col-2">
                <CallsList key={"callsComponent"} places={places} />
              </div>
            </div>
          } />
          <Route path="/events" element={<EventsList />} />
          <Route path="/events/:id" element={<EventsList />} />
        </Routes>
      </div>
      <Footer />
    </div>
  );
}

export default HealthApp;
