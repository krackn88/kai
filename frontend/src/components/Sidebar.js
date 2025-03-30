import React, { useContext } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { AppContext } from '../context/AppContext';

// Import icons
import { 
  FaHome, 
  FaComment, 
  FaTools, 
  FaDatabase, 
  FaCog,
  FaMoon,
  FaSun
} from 'react-icons/fa';

function Sidebar() {
  const { darkMode, setDarkMode, user } = useContext(AppContext);
  const location = useLocation();
  
  // Check if a route is active
  const isActive = (path) => location.pathname === path;
  
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>Claude Agent</h2>
        <div className="theme-toggle" onClick={() => setDarkMode(!darkMode)}>
          {darkMode ? <FaSun /> : <FaMoon />}
        </div>
      </div>
      
      <div className="user-info">
        <div className="avatar">
          {user.username.charAt(0).toUpperCase()}
        </div>
        <div className="username">{user.username}</div>
      </div>
      
      <nav className="sidebar-nav">
        <Link to="/" className={`nav-item ${isActive('/') ? 'active' : ''}`}>
          <FaHome />
          <span>Home</span>
        </Link>
        
        <Link to="/chat" className={`nav-item ${isActive('/chat') ? 'active' : ''}`}>
          <FaComment />
          <span>Chat</span>
        </Link>
        
        <Link to="/tools" className={`nav-item ${isActive('/tools') ? 'active' : ''}`}>
          <FaTools />
          <span>Tools</span>
        </Link>
        
        <Link to="/rag" className={`nav-item ${isActive('/rag') ? 'active' : ''}`}>
          <FaDatabase />
          <span>Knowledge Base</span>
        </Link>
        
        <Link to="/settings" className={`nav-item ${isActive('/settings') ? 'active' : ''}`}>
          <FaCog />
          <span>Settings</span>
        </Link>
      </nav>
      
      <div className="sidebar-footer">
        <p>Anthropic-Powered Agent v1.7.0</p>
      </div>
    </div>
  );
}

export default Sidebar;