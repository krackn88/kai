import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Button, 
  List, 
  ListItem, 
  ListItemText, 
  Divider,
  Badge,
  IconButton,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Switch,
  FormControlLabel,
  Alert,
  Chip,
  CircularProgress,
  useTheme
} from '@mui/material';
import { 
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  GitHub as GitHubIcon,
  Sync as SyncIcon,
  SyncDisabled as SyncDisabledIcon,
  CloudDone as CloudDoneIcon,
  CloudOff as CloudOffIcon,
  ArrowUpward as PushIcon,
  ArrowDownward as PullIcon,
  MoreVert as MoreIcon
} from '@mui/icons-material';
import gitHubSyncService from '../../services/GitHubSyncService';

/**
 * GitHub Repository Sync Panel Component
 * 
 * Displays and manages GitHub repository synchronization status and settings.
 */
const GitHubSyncPanel = () => {
  const theme = useTheme();
  
  // Component state
  const [repositories, setRepositories] = useState([]);
  const [syncStatus, setSyncStatus] = useState({
    status: 'disconnected',
    method: null
  });
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settings, setSettings] = useState({
    useWebhooks: true,
    usePolling: true,
    pollingInterval: 60,
    autoSync: true
  });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [syncHistory, setSyncHistory] = useState([]);
  const [newRepoUrl, setNewRepoUrl] = useState('');
  
  // Initialize service and set up event listeners
  useEffect(() => {
    // Set up event listeners
    const handleRepoUpdate = (data) => {
      console.log('Repository update event:', data);
      
      // Update repositories list
      setRepositories(prevRepos => {
        const existingRepoIndex = prevRepos.findIndex(
          repo => repo.name === data.repository
        );
        
        if (existingRepoIndex >= 0) {
          // Update existing repository
          const updatedRepos = [...prevRepos];
          updatedRepos[existingRepoIndex] = {
            ...updatedRepos[existingRepoIndex],
            lastUpdate: new Date().toISOString(),
            hasChanges: true,
            lastEvent: data
          };
          return updatedRepos;
        } else {
          // Add new repository
          return [
            ...prevRepos,
            {
              name: data.repository,
              lastUpdate: new Date().toISOString(),
              hasChanges: true,
              lastEvent: data
            }
          ];
        }
      });
      
      // Add to sync history
      setSyncHistory(prev => [
        {
          timestamp: new Date().toISOString(),
          repository: data.repository,
          source: data.source,
          details: data
        },
        ...prev.slice(0, 19)  // Keep last 20 entries
      ]);
      
      // Clear any errors
      setError(null);
    };
    
    const handleConnectionStatus = (data) => {
      console.log('Connection status event:', data);
      setSyncStatus(data);
      
      if (data.status === 'error') {
        setError('Connection error. Check network or server status.');
      } else if (data.status === 'connected') {
        setError(null);
      }
    };
    
    const handleSyncError = (data) => {
      console.error('Sync error event:', data);
      setError(data.error);
      
      // Add to sync history
      setSyncHistory(prev => [
        {
          timestamp: new Date().toISOString(),
          error: true,
          details: data
        },
        ...prev.slice(0, 19)  // Keep last 20 entries
      ]);
    };
    
    // Register event listeners
    gitHubSyncService.addEventListener('repo-updated', handleRepoUpdate);
    gitHubSyncService.addEventListener('connection-status', handleConnectionStatus);
    gitHubSyncService.addEventListener('sync-error', handleSyncError);
    
    // Start service
    gitHubSyncService.startSync({
      useWebhooks: settings.useWebhooks,
      usePolling: settings.usePolling,
      pollingInterval: settings.pollingInterval * 1000  // Convert to ms
    });
    
    // Fetch initial repositories
    fetchRepositories();
    
    // Cleanup on unmount
    return () => {
      gitHubSyncService.removeEventListener('repo-updated', handleRepoUpdate);
      gitHubSyncService.removeEventListener('connection-status', handleConnectionStatus);
      gitHubSyncService.removeEventListener('sync-error', handleSyncError);
      gitHubSyncService.stopSync();
    };
  }, []);  // Empty dependency array for initialization
  
  // Fetch repositories
  const fetchRepositories = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/github/repos');
      const data = await response.json();
      
      if (data.repositories) {
        setRepositories(data.repositories);
      }
    } catch (error) {
      console.error('Error fetching repositories:', error);
      setError('Failed to fetch repositories. ' + error.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Handle manual sync
  const handleManualSync = async (repoName) => {
    try {
      setLoading(true);
      await gitHubSyncService.syncRepository(repoName);
      setLoading(false);
    } catch (error) {
      setError('Manual sync failed: ' + error.message);
      setLoading(false);
    }
  };
  
  // Handle sync all repositories
  const handleSyncAll = async () => {
    try {
      setLoading(true);
      for (const repo of repositories) {
        await gitHubSyncService.syncRepository(repo.name);
      }
      setLoading(false);
    } catch (error) {
      setError('Sync all failed: ' + error.message);
      setLoading(false);
    }
  };
  
  // Handle settings changes
  const handleSettingChange = (setting, value) => {
    setSettings(prev => ({
      ...prev,
      [setting]: value
    }));
  };
  
  // Apply settings
  const applySettings = () => {
    gitH