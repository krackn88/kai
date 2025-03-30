import React from 'react';
import { 
  Box, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Paper, 
  Chip, 
  CircularProgress,
  Typography,
  Tooltip
} from '@mui/material';
import {
  Check as CheckIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  SyncAlt as SyncAltIcon,
  HistoryToggleOff as ManualIcon,
  Autorenew as AutoIcon
} from '@mui/icons-material';

/**
 * Component for displaying GitHub sync history in a table format
 */
const SyncHistoryTable = ({ history, isLoading }) => {
  // If loading, show spinner
  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" my={3}>
        <CircularProgress />
      </Box>
    );
  }

  // If no history, show message
  if (!history || history.length === 0) {
    return (
      <Box textAlign="center" my={3}>
        <Typography variant="body1" color="textSecondary">
          No synchronization history available
        </Typography>
      </Box>
    );
  }

  // Get sync type icon
  const getSyncTypeIcon = (type) => {
    switch (type) {
      case 'manual':
        return <ManualIcon fontSize="small" />;
      case 'auto':
        return <AutoIcon fontSize="small" />;
      case 'webhook':
        return <SyncAltIcon fontSize="small" />;
      default:
        return <SyncAltIcon fontSize="small" />;
    }
  };

  // Get status chip for the sync operation
  const getStatusChip = (status) => {
    switch (status) {
      case 'success':
        return <Chip 
          icon={<CheckIcon />} 
          label="Success" 
          size="small" 
          color="success" 
          variant="outlined" 
        />;
      case 'error':
        return <Chip 
          icon={<ErrorIcon />} 
          label="Failed" 
          size="small" 
          color="error" 
          variant="outlined" 
        />;
      case 'in_progress':
        return <Chip 
          icon={<CircularProgress size={16} />} 
          label="In Progress" 
          size="small" 
          color="primary" 
          variant="outlined" 
        />;
      default:
        return <Chip 
          icon={<ScheduleIcon />} 
          label="Unknown" 
          size="small" 
          variant="outlined" 
        />;
    }
  };

  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell><strong>Timestamp</strong></TableCell>
            <TableCell><strong>Type</strong></TableCell>
            <TableCell><strong>Repository</strong></TableCell>
            <TableCell><strong>Branch</strong></TableCell>
            <TableCell><strong>Status</strong></TableCell>
            <TableCell><strong>Changes</strong></TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {history.map((item, index) => (
            <TableRow key={index} hover>
              <TableCell>
                {new Date(item.timestamp).toLocaleString()}
              </TableCell>
              <TableCell>
                <Tooltip title={`${item.sync_type.charAt(0).toUpperCase() + item.sync_type.slice(1)} Sync`}>
                  <Box display="flex" alignItems="center">
                    {getSyncTypeIcon(item.sync_type)}
                    <Box ml={1}>{item.sync_type}</Box>
                  </Box>
                </Tooltip>
              </TableCell>
              <TableCell>{item.repository}</TableCell>
              <TableCell>{item.branch || 'main'}</TableCell>
              <TableCell>{getStatusChip(item.status)}</TableCell>
              <TableCell>
                {item.changes ? (
                  <Tooltip title={`${item.changes.added || 0} added, ${item.changes.modified || 0} modified, ${item.changes.deleted || 0} deleted`}>
                    <Chip 
                      label={`${item.changes.added + item.changes.modified + item.changes.deleted} files`} 
                      size="small" 
                      variant="outlined" 
                    />
                  </Tooltip>
                ) : (
                  <Typography variant="body2" color="textSecondary">
                    No changes
                  </Typography>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default SyncHistoryTable;