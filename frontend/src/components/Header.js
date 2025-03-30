import React, { useContext } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { AppContext } from '../context/AppContext';
import { FaPlus } from 'react-icons/fa';

function Header() {
  const { defaultModel } = useContext(AppContext);
  const location = useLocation();
  const navigate = useNavigate();
  
  // Get title based on current route
  const getTitle = () => {
    const path = location.pathname;
    
    if (path === '/') return 'Home';
    if (path.startsWith('/chat')) return 'Chat';
    if (path === '/tools') return 'Tools';
    if (path === '/rag') return 'Knowledge Base';
    if (path === '/settings') return 'Settings';
    
    return 'Claude Agent';
  };
  
  // Determine if we should show the new chat button
  const showNewChatButton = location.pathname === '/' || location.pathname.startsWith('/chat');
  
  const handleNewChat = () => {
    navigate('/chat');
  };
  
  return (
    <div className="header">
      <h1>{getTitle()}</h1>
      
      {showNewChatButton && (
        <button className="new-chat-button" onClick={handleNewChat}>
          <FaPlus />
          <span>New Chat</span>
        </button>
      )}
      
      <div className="model-indicator">
        Using: {defaultModel}
      </div>
    </div>
  );
}

export default Header;