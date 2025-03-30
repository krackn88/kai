import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';

// Import components
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ChatView from './views/ChatView';
import HomeView from './views/HomeView';
import ToolsView from './views/ToolsView';
import RagView from './views/RagView';
import SettingsView from './views/SettingsView';

// Import context
import { AppContext } from './context/AppContext';

// Import API service
import ApiService from './services/ApiService';

function App() {
  // App state
  const [user, setUser] = useState({ username: 'User' });
  const [apiKey, setApiKey] = useState(localStorage.getItem('apiKey') || '');
  const [defaultModel, setDefaultModel] = useState(localStorage.getItem('defaultModel') || 'claude-3-opus-20240229');
  const [serverUrl, setServerUrl] = useState(localStorage.getItem('serverUrl') || 'http://localhost:8000');
  const [darkMode, setDarkMode] = useState(localStorage.getItem('darkMode') === 'true');
  const [useRag, setUseRag] = useState(localStorage.getItem('useRag') === 'true');
  
  // Initialize API service
  const apiService = new ApiService(serverUrl, apiKey);
  
  // Set up theme based on darkMode
  useEffect(() => {
    if (darkMode) {
      document.body.classList.add('dark-theme');
    } else {
      document.body.classList.remove('dark-theme');
    }
    localStorage.setItem('darkMode', darkMode);
  }, [darkMode]);
  
  // Store settings in localStorage
  useEffect(() => {
    localStorage.setItem('apiKey', apiKey);
    localStorage.setItem('defaultModel', defaultModel);
    localStorage.setItem('serverUrl', serverUrl);
    localStorage.setItem('useRag', useRag);
    
    // Update API service configuration
    apiService.setApiKey(apiKey);
    apiService.setBaseUrl(serverUrl);
  }, [apiKey, defaultModel, serverUrl, useRag, apiService]);
  
  // Context value
  const contextValue = {
    user,
    setUser,
    apiKey,
    setApiKey,
    defaultModel,
    setDefaultModel,
    serverUrl,
    setServerUrl,
    darkMode,
    setDarkMode,
    useRag,
    setUseRag,
    apiService
  };
  
  return (
    <AppContext.Provider value={contextValue}>
      <Router>
        <div className={`app ${darkMode ? 'dark-theme' : ''}`}>
          <Sidebar />
          <div className="main-content">
            <Header />
            <Routes>
              <Route path="/" element={<HomeView />} />
              <Route path="/chat" element={<ChatView />} />
              <Route path="/chat/:conversationId" element={<ChatView />} />
              <Route path="/tools" element={<ToolsView />} />
              <Route path="/rag" element={<RagView />} />
              <Route path="/settings" element={<SettingsView />} />
            </Routes>
          </div>
        </div>
      </Router>
    </AppContext.Provider>
  );
}

export default App;