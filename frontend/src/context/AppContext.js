import { createContext } from 'react';

export const AppContext = createContext({
  user: { username: 'User' },
  setUser: () => {},
  apiKey: '',
  setApiKey: () => {},
  defaultModel: 'claude-3-opus-20240229',
  setDefaultModel: () => {},
  serverUrl: 'http://localhost:8000',
  setServerUrl: () => {},
  darkMode: false,
  setDarkMode: () => {},
  useRag: false,
  setUseRag: () => {},
  apiService: null
});