import React, { useState, useEffect, useContext } from 'react';
import { Box, Button, Card, CardContent, CardHeader, CircularProgress, Divider, 
         FormControl, FormControlLabel, Grid, IconButton, InputAdornment, InputLabel, 
         MenuItem, Select, Switch, TextField, Typography, Alert, Tooltip, Paper } from '@mui/material';
import { AppContext } from '../../context/AppContext';
import { 
  Refresh as RefreshIcon, 
  Save as SaveIcon, 
  GitHub as GitHubIcon,
  Sync as SyncIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  CloudUpload as CloudUploadIcon
} from '@mui/icons-material';
import axios from 'axios';
import SyncHistoryTable from './SyncHistoryTable';
import SyncSettingsDialog from './SyncSettingsDialog';

/**
 * GitHub Sync Panel Component
 * 
 * Provides a user interface for managing GitHub repository synchronization
 * including manual sync triggers, status monitoring, and configuration.
 */
const GitHubSyncPanel = () => {
  const { apiService, serverUrl, apiKey } = useContext(AppContext);
  
  // State management
  const [syncConfig, setSyncConfig] = useState({
    localDirectory: '',
    repoName: '',
    branch: 'main',
    commitInterval: 300,
    autoSync: true,
    useWebhooks: true,
    usePolling: true
  });
  
  const [connectionStatus, setConnectionStatus] = useState({
    status: 'disconnected',
    lastSync: null,
    method: null
  });
  
  const [syncHistory, setSyncHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  // Load configuration on component mount
  useEffect(() => {
    loadSyncConfig();
    loadSyncHistory();
    
    // Set up status polling
    const statusInterval = setInterval(checkSyncStatus, 10000);
    
    return () => {
      clearInterval(statusInterval);
    };
  }, []);

  // Load sync configuration from the server
  const loadSyncConfig = async () => {
    try {
      setIsLoading(true);
      
      // Using the apiService to get configuration
      const endpoint = '/github/sync/config';
      const response = await axios.get(`${serverUrl}${endpoint}`, {
        headers: {
          'X-API-Key': apiKey,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.data) {
        setSyncConfig({
          localDirectory: response.data.local_directory || '',
          repoName: response.data.repo_name || '',
          branch: response.data.branch || 'main',
          commitInterval: response.data.commit_interval || 300,
          autoSync: response.data.auto_sync || true,
          useWebhooks: response.data.use_webhooks || true,
          usePolling: response.data.use_polling || true
        });
      }
      
      setError(null);
    } catch (err) {
      console.error('Failed to load sync configuration:', err);
      setError('Failed to load sync configuration. Please check server connection.');
    } finally {
      setIsLoading(false);
    }
  };

  // Load sync history from the server
  const loadSyncHistory = async () => {
    try {
      setIsLoading(true);
      
      // Using the apiService to get sync history
      const endpoint = '/github/sync/history';
      const response = await axios.get(`${serverUrl}${endpoint}`, {
        headers: {
          'X-API-Key': apiKey,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.data && Array.isArray(response.data.history)) {
        setSyncHistory(response.data.history);
      }
      
      setError(null);
    } catch (err) {
      console.error('Failed to load sync history:', err);
      setError('Failed to load sync history. Please check server connection.');
    } finally {
      setIsLoading(false);
    }
  };

  // Check the current sync status
  const checkSyncStatus = async () => {
    try {
      // Using the apiService to check sync status
      const endpoint = '/github/sync/status';
      const response = await axios.get(`${serverUrl}${endpoint}`, {
        headers: {
          'X-API-Key': apiKey,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.data) {
        setConnectionStatus({
          status: response.data.status || 'disconnected',
          lastSync: response.data.last_sync || null,
          method: response.data.method || null
        });
      }
    } catch (err) {
      console.error('Failed to check sync status:', err);
      // Don't show error alert for status check failures, just update the status
      setConnectionStatus({
        status: 'error',
        lastSync: connectionStatus.lastSync,
        method: connectionStatus.method
      });
    }
  };

  // Save sync configuration to the server
  const saveSyncConfig = async () => {
    try {
      setIsLoading(true);
      
      // Using the apiService to save configuration
      const endpoint = '/github/sync/config';
      const response = await axios.post(`${serverUrl}${endpoint}`, {
        local_directory: syncConfig.localDirectory,
        repo_name: syncConfig.repoName,
        branch: syncConfig.branch,
        commit_interval: syncConfig.commitInterval,
        auto_sync: syncConfig.autoSync,
        use_webhooks: syncConfig.useWebhooks,
        use_polling: syncConfig.usePolling
      }, {
        headers: {
          'X-API-Key': apiKey,
          'Content-Type': 'application/json'
        }
      });
      
      setError(null);
    } catch (err) {
      console.error('Failed to save sync configuration:', err);
      setError('Failed to save configuration. Please check your settings and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Trigger a manual sync
  const triggerManualSync = async () => {
    try {
      setIsLoading(true);
      
      // Using the apiService to trigger manual sync
      const endpoint = '/github/sync/trigger';
      const response = await axios.post(`${serverUrl}${endpoint}`, {
        message: `Manual sync triggered at ${new Date().toISOString()}`
      }, {
        headers: {
          'X-API-Key': apiKey,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.data && response.data.success) {
        // Update sync history after successful sync
        loadSyncHistory();
      }
      
      setError(null);
    } catch (err) {
      console.error('Failed to trigger manual sync:', err);
      setError('Failed to trigger sync. Please check your configuration and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle input changes
  const handleInputChange = (e) => {
    const { name, value, checked, type } = e.target;
    setSyncConfig({
      ...syncConfig,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  // Render connection status indicator
  const renderStatusIndicator = () => {
    const statusColors = {
      connected: '#4caf50',  // Green
      connecting: '#ff9800', // Orange
      disconnected: '#f44336', // Red
      error: '#f44336' // Red
    };
    
    const statusText = {
      connected: 'Connected',
      connecting: 'Connecting...',
      disconnected: 'Disconnected',
      error: 'Connection Error'
    };
    
    return (
      <Box display="flex" alignItems="center">
        <Box
          sx={{
            width: 12,
            height: 12,
            borderRadius: '50%',
            backgroundColor: statusColors[connectionStatus.status] || '#9e9e9e',
            marginRight: 1
          }}
        />
        <Typography variant="body2">
          {statusText[connectionStatus.status] || 'Unknown'}
          {connectionStatus.method && ` (${connectionStatus.method})`}
        </Typography>
      </Box>
    );
  };

  return (
    <Box sx={{ maxWidth: '100%', mb: 3 }}>
      <Card>
        <CardHeader
          title={
            <Box display="flex" alignItems="center">
              <GitHubIcon sx={{ mr: 1 }} />
              <Typography variant="h6">GitHub Sync</Typography>
            </Box>
          }
          action={
            <Box>
              {renderStatusIndicator()}
              <Tooltip title="Sync Settings">
                <IconButton onClick={() => setShowSettings(true)}>
                  <SettingsIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Sync History">
                <IconButton onClick={() => setShowHistory(!showHistory)}>
                  <HistoryIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Refresh Status">
                <IconButton onClick={checkSyncStatus}>
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
            </Box>
          }
        />
        
        <Divider />
        
        <CardContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          {isLoading && (
            <Box display="flex" justifyContent="center" my={2}>
              <CircularProgress size={24} />
            </Box>
          )}
          
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Local Directory"
                name="localDirectory"
                value={syncConfig.localDirectory}
                onChange={handleInputChange}
                margin="normal"
                variant="outlined"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Tooltip title="The local directory to sync with GitHub">
                        <Box component="span">📁</Box>
                      </Tooltip>
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Repository Name"
                name="repoName"
                value={syncConfig.repoName}
                onChange={handleInputChange}
                margin="normal"
                variant="outlined"
                placeholder="username/repo"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <GitHubIcon fontSize="small" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Branch"
                name="branch"
                value={syncConfig.branch}
                onChange={handleInputChange}
                margin="normal"
                variant="outlined"
                placeholder="main"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Commit Interval (seconds)"
                name="commitInterval"
                type="number"
                value={syncConfig.commitInterval}
                onChange={handleInputChange}
                margin="normal"
                variant="outlined"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Tooltip title="Minimum time between auto-commits">
                        <Box component="span">⏱️</Box>
                      </Tooltip>
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap' }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={syncConfig.autoSync}
                      onChange={handleInputChange}
                      name="autoSync"
                      color="primary"
                    />
                  }
                  label="Auto Sync"
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={syncConfig.useWebhooks}
                      onChange={handleInputChange}
                      name="useWebhooks"
                      color="primary"
                    />
                  }
                  label="Use Webhooks"
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={syncConfig.usePolling}
                      onChange={handleInputChange}
                      name="usePolling"
                      color="primary"
                    />
                  }
                  label="Use Polling"
                />
              </Box>
            </Grid>
          </Grid>
          
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={saveSyncConfig}
              disabled={isLoading}
            >
              Save Configuration
            </Button>
            
            <Button
              variant="contained"
              color="secondary"
              startIcon={<SyncIcon />}
              onClick={triggerManualSync}
              disabled={isLoading || !syncConfig.repoName}
            >
              Sync Now
            </Button>
          </Box>
          
          {connectionStatus.lastSync && (
            <Typography variant="body2" sx={{ mt: 2, fontStyle: 'italic' }}>
              Last synchronized: {new Date(connectionStatus.lastSync).toLocaleString()}
            </Typography>
          )}
        </CardContent>
      </Card>
      
      {showHistory && (
        <Paper sx={{ mt: 2, p: 2 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Sync History</Typography>
            <Button 
              startIcon={<RefreshIcon />}
              onClick={loadSyncHistory}
              disabled={isLoading}
            >
              Refresh
            </Button>
          </Box>
          <SyncHistoryTable history={syncHistory} isLoading={isLoading} />
        </Paper>
      )}
      
      <SyncSettingsDialog 
        open={showSettings}
        onClose={() => setShowSettings(false)}
        config={syncConfig}
        onChange={setSyncConfig}
        onSave={saveSyncConfig}
        isLoading={isLoading}
      />
    </Box>
  );
};

export default GitHubSyncPanel;