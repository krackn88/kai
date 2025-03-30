import React, { useState } from 'react';
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  FormControlLabel,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Switch,
  TextField,
  Typography,
  Alert,
  Tooltip,
  CircularProgress
} from '@mui/material';
import {
  Close as CloseIcon,
  Save as SaveIcon,
  GitHub as GitHubIcon,
  WebhookIcon,
  AccessTime as AccessTimeIcon,
  Security as SecurityIcon
} from '@mui/icons-material';

/**
 * Dialog component for advanced GitHub sync settings
 */
const SyncSettingsDialog = ({ open, onClose, config, onChange, onSave, isLoading }) => {
  const [localConfig, setLocalConfig] = useState({ ...config });
  const [showTokenSection, setShowTokenSection] = useState(false);
  
  // Reset local config when dialog opens
  React.useEffect(() => {
    if (open) {
      setLocalConfig({ ...config });
    }
  }, [open, config]);
  
  // Handle input changes
  const handleInputChange = (e) => {
    const { name, value, checked, type } = e.target;
    setLocalConfig({
      ...localConfig,
      [name]: type === 'checkbox' ? checked : value
    });
  };
  
  // Apply changes and save
  const handleSave = () => {
    onChange(localConfig);
    onSave();
    onClose();
  };
  
  return (
    <Dialog 
      open={open} 
      onClose={onClose}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box display="flex" alignItems="center">
            <GitHubIcon sx={{ mr: 1 }} />
            <Typography variant="h6">GitHub Sync Settings</Typography>
          </Box>
          <IconButton onClick={onClose} edge="end">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <Divider />
      
      <DialogContent>
        <Grid container spacing={3}>
          {/* Repository Section */}
          <Grid item xs={12}>
            <Typography variant="subtitle1" gutterBottom>
              <strong>Repository Configuration</strong>
            </Typography>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Local Directory"
              name="localDirectory"
              value={localConfig.localDirectory}
              onChange={handleInputChange}
              variant="outlined"
              placeholder="C:\path\to\directory or /path/to/directory"
              helperText="Absolute path to the local directory to sync"
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Repository Name"
              name="repoName"
              value={localConfig.repoName}
              onChange={handleInputChange}
              variant="outlined"
              placeholder="username/repo"
              helperText="Format: username/repository or organization/repository"
              InputProps={{
                startAdornment: (
                  <GitHubIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                ),
              }}
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Branch"
              name="branch"
              value={localConfig.branch}
              onChange={handleInputChange}
              variant="outlined"
              placeholder="main"
              helperText="Branch to sync with (default: main)"
            />
          </Grid>
          
          {/* Sync Behavior Section */}
          <Grid item xs={12} sx={{ mt: 2 }}>
            <Divider />
            <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
              <strong>Sync Behavior</strong>
            </Typography>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Commit Interval"
              name="commitInterval"
              type="number"
              value={localConfig.commitInterval}
              onChange={handleInputChange}
              variant="outlined"
              InputProps={{
                endAdornment: <Typography variant="body2" color="textSecondary">seconds</Typography>,
                startAdornment: (
                  <AccessTimeIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                ),
              }}
              helperText="Minimum time between automatic commits (in seconds)"
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <FormControl fullWidth variant="outlined">
              <InputLabel>Sync Mode</InputLabel>
              <Select
                label="Sync Mode"
                name="syncMode"
                value={localConfig.syncMode || "auto"}
                onChange={handleInputChange}
              >
                <MenuItem value="auto">Automatic (recommended)</MenuItem>
                <MenuItem value="manual">Manual only</MenuItem>
                <MenuItem value="scheduled">Scheduled</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={localConfig.autoSync}
                    onChange={handleInputChange}
                    name="autoSync"
                    color="primary"
                  />
                }
                label="Enable automatic synchronization"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={localConfig.useWebhooks}
                    onChange={handleInputChange}
                    name="useWebhooks"
                    color="primary"
                  />
                }
                label="Use webhooks for real-time updates (recommended)"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={localConfig.usePolling}
                    onChange={handleInputChange}
                    name="usePolling"
                    color="primary"
                  />
                }
                label="Use polling as fallback"
              />
            </Box>
          </Grid>
          
          {/* Authentication Section (Hidden by default) */}
          <Grid item xs={12} sx={{ mt: 2 }}>
            <Divider />
            <Box display="flex" justifyContent="space-between" alignItems="center" mt={2}>
              <Typography variant="subtitle1" gutterBottom>
                <strong>Authentication Settings</strong>
              </Typography>
              <Button 
                size="small" 
                onClick={() => setShowTokenSection(!showTokenSection)}
                startIcon={<SecurityIcon />}
              >
                {showTokenSection ? 'Hide Token Settings' : 'Show Token Settings'}
              </Button>
            </Box>
          </Grid>
          
          {showTokenSection && (
            <Grid item xs={12}>
              <Alert severity="info" sx={{ mb: 2 }}>
                For security reasons, GitHub tokens are stored in environment variables on the server.
                The token should have 'repo' scope for private repositories.
              </Alert>
              
              <Typography variant="body2" paragraph>
                To use a GitHub Personal Access Token (PAT):
              </Typography>
              
              <Box component="ol" sx={{ ml: 2 }}>
                <li>
                  <Typography variant="body2">
                    Create a PAT with 'repo' scope at{' '}
                    <a href="https://github.com/settings/tokens" target="_blank" rel="noopener noreferrer">
                      https://github.com/settings/tokens
                    </a>
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    Set the <code>GITHUB_TOKEN</code> environment variable on your server
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    Restart the agent application
                  </Typography>
                </li>
              </Box>
            </Grid>
          )}
          
          {/* Advanced Settings */}
          <Grid item xs={12} sx={{ mt: 2 }}>
            <Divider />
            <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
              <strong>Advanced Settings</strong>
            </Typography>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Webhook Secret"
              name="webhookSecret"
              type="password"
              value={localConfig.webhookSecret || ''}
              onChange={handleInputChange}
              variant="outlined"
              placeholder="Optional webhook secret"
              helperText="Secret token for GitHub webhook verification"
              InputProps={{
                startAdornment: (
                  <Tooltip title="Used to verify webhook payloads from GitHub">
                    <WebhookIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                  </Tooltip>
                ),
              }}
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Rate Limit Pause"
              name="rateLimitPause"
              type="number"
              value={localConfig.rateLimitPause || 60}
              onChange={handleInputChange}
              variant="outlined"
              InputProps={{
                endAdornment: <Typography variant="body2" color="textSecondary">seconds</Typography>
              }}
              helperText="Pause duration when GitHub API rate limit is hit"
            />
          </Grid>
        </Grid>
      </DialogContent>
      
      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose} disabled={isLoading}>
          Cancel
        </Button>
        <Button 
          onClick={handleSave} 
          variant="contained" 
          color="primary"
          startIcon={isLoading ? <CircularProgress size={20} /> : <SaveIcon />}
          disabled={isLoading}
        >
          Save Changes
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SyncSettingsDialog;