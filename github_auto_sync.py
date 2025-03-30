#!/usr/bin/env python3
"""
GitHub Repository Auto-Sync Tool

This script monitors a local directory and automatically pushes changes to a GitHub repository.
It uses PyGitHub for GitHub API interactions and gitpython for local git operations.

Features:
- Real-time file change detection
- Secure authentication via environment variables
- Comprehensive logging and error handling
- Configurable sync intervals with proper rate limiting
- Support for selective file syncing with .gitignore
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path
import git
from github import Github
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("github_sync.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("GitHubAutoSync")

class GitHubSyncConfig:
    """Configuration for GitHub synchronization"""
    
    def __init__(self, local_dir, repo_name, branch="main", 
                 commit_interval=300, rate_limit_pause=60):
        self.local_dir = Path(local_dir).resolve()
        self.repo_name = repo_name
        self.branch = branch
        self.commit_interval = commit_interval  # seconds
        self.rate_limit_pause = rate_limit_pause  # seconds
        
        # Get GitHub token from environment variables (NEVER hardcode)
        self.github_token = os.environ.get("GITHUB_TOKEN")
        if not self.github_token:
            logger.error("GITHUB_TOKEN environment variable not set!")
            raise ValueError("GITHUB_TOKEN environment variable is required")
            
        # Validate the local directory
        if not self.local_dir.exists() or not self.local_dir.is_dir():
            logger.error(f"Local directory does not exist: {self.local_dir}")
            raise ValueError(f"Invalid local directory: {self.local_dir}")
            
        logger.info(f"Configured sync for {self.local_dir} -> {self.repo_name}:{self.branch}")

class GitRepoManager:
    """Manages Git repository operations"""
    
    def __init__(self, config):
        self.config = config
        self.repo = self._get_or_init_repo()
        self.github = Github(config.github_token)
        self.gh_repo = self._get_or_create_github_repo()
        self.last_commit_time = 0
        
    def _get_or_init_repo(self):
        """Get existing git repo or initialize a new one"""
        try:
            repo = git.Repo(self.config.local_dir)
            logger.info(f"Using existing git repository at {self.config.local_dir}")
            return repo
        except git.InvalidGitRepositoryError:
            logger.info(f"Initializing new git repository at {self.config.local_dir}")
            repo = git.Repo.init(self.config.local_dir)
            
            # Configure git if this is a new repo
            with repo.config_writer() as config:
                config.set_value("user", "name", "GitHub Auto Sync")
                config.set_value("user", "email", "auto-sync@github.com")
                
            return repo
            
    def _get_or_create_github_repo(self):
        """Get or create GitHub repository"""
        user = self.github.get_user()
        
        try:
            repo = user.get_repo(self.config.repo_name.split('/')[-1])
            logger.info(f"Found existing GitHub repository: {repo.full_name}")
            return repo
        except Exception as e:
            if '/' in self.config.repo_name:  # Organization repo
                org_name, repo_name = self.config.repo_name.split('/')
                org = self.github.get_organization(org_name)
                try:
                    repo = org.get_repo(repo_name)
                    return repo
                except Exception:
                    logger.info(f"Creating new repository in organization {org_name}")
                    return org.create_repo(repo_name)
            else:  # User repo
                logger.info(f"Creating new repository: {self.config.repo_name}")
                return user.create_repo(self.config.repo_name)
    
    def setup_remote(self):
        """Set up git remote"""
        try:
            origin = self.repo.remote('origin')
            current_url = list(origin.urls)[0]
            expected_url = f"https://github.com/{self.gh_repo.full_name}.git"
            
            if current_url != expected_url:
                logger.info(f"Updating remote URL from {current_url} to {expected_url}")
                origin.set_url(expected_url)
        except ValueError:
            logger.info("Adding new remote 'origin'")
            self.repo.create_remote('origin', f"https://github.com/{self.gh_repo.full_name}.git")
    
    def ensure_branch_exists(self):
        """Ensure the configured branch exists"""
        try:
            # Check if branch exists locally
            self.repo.git.checkout(self.config.branch)
            logger.info(f"Checked out existing branch: {self.config.branch}")
        except git.GitCommandError:
            # Create branch if it doesn't exist
            logger.info(f"Creating new branch: {self.config.branch}")
            self.repo.git.checkout('-b', self.config.branch)
    
    def stage_changes(self):
        """Stage all changes for commit"""
        self.repo.git.add('.')
        return len(self.repo.index.diff('HEAD')) > 0
    
    def commit_changes(self, message=None):
        """Commit staged changes"""
        if not message:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message = f"Auto-sync update at {timestamp}"
            
        try:
            self.repo.git.commit('-m', message)
            logger.info(f"Committed changes: {message}")
            self.last_commit_time = time.time()
            return True
        except git.GitCommandError as e:
            if "nothing to commit" in str(e):
                logger.debug("No changes to commit")
                return False
            else:
                logger.error(f"Git commit error: {e}")
                raise
    
    def push_changes(self):
        """Push changes to GitHub"""
        try:
            # Set up credentials via environment
            # This uses the GITHUB_TOKEN environment variable
            remote_url = f"https://x-access-token:{self.config.github_token}@github.com/{self.gh_repo.full_name}.git"
            self.repo.git.push(remote_url, self.config.branch)
            logger.info(f"Pushed changes to {self.gh_repo.full_name}:{self.config.branch}")
            return True
        except git.GitCommandError as e:
            logger.error(f"Git push error: {e}")
            if "rate limit" in str(e).lower():
                logger.warning(f"Rate limit hit. Pausing for {self.config.rate_limit_pause} seconds")
                time.sleep(self.config.rate_limit_pause)
            raise

    def sync_if_needed(self, force=False):
        """Sync repository if changes exist or if forced"""
        if force or (time.time() - self.last_commit_time) >= self.config.commit_interval:
            has_changes = self.stage_changes()
            if has_changes or force:
                if self.commit_changes():
                    return self.push_changes()
        return False

class FileChangeHandler(FileSystemEventHandler):
    """Handles file system change events"""
    
    def __init__(self, repo_manager):
        self.repo_manager = repo_manager
        self.last_event_time = 0
        self.pending_sync = False
        self._ignored_patterns = self._load_gitignore()
        
    def _load_gitignore(self):
        """Load patterns from .gitignore file"""
        gitignore_path = self.repo_manager.config.local_dir / '.gitignore'
        patterns = []
        
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
        
        # Add default ignored files
        patterns.extend(['.git/', '.github_sync.log', '__pycache__/'])
        return patterns
    
    def _is_ignored(self, path):
        """Check if a path matches any gitignore pattern"""
        rel_path = str(Path(path).relative_to(self.repo_manager.config.local_dir))
        
        for pattern in self._ignored_patterns:
            if pattern.endswith('/'):
                # Directory pattern
                if rel_path.startswith(pattern) or rel_path + '/' == pattern:
                    return True
            else:
                # File pattern (simple matching for now)
                if rel_path == pattern or pattern in rel_path:
                    return True
        
        return False
    
    def on_any_event(self, event):
        """Handle any file system event"""
        if event.is_directory or self._is_ignored(event.src_path):
            return
            
        logger.debug(f"File event: {event.event_type} - {event.src_path}")
        
        current_time = time.time()
        # Avoid multiple commits for rapid successive events
        if current_time - self.last_event_time > 2:  # 2 second debounce
            self.pending_sync = True
            self.last_event_time = current_time

def run_auto_sync(config):
    """Run the auto-sync process"""
    repo_manager = GitRepoManager(config)
    repo_manager.setup_remote()
    repo_manager.ensure_branch_exists()
    
    # Initial sync
    logger.info("Performing initial sync...")
    repo_manager.sync_if_needed(force=True)
    
    # Set up file watcher
    event_handler = FileChangeHandler(repo_manager)
    observer = Observer()
    observer.schedule(event_handler, config.local_dir, recursive=True)
    observer.start()
    
    logger.info(f"Watching {config.local_dir} for changes...")
    try:
        while True:
            time.sleep(1)
            
            if event_handler.pending_sync:
                # Wait a bit after the last change before syncing
                if time.time() - event_handler.last_event_time > 5:  # 5 second grace period
                    logger.info("Changes detected, syncing...")
                    repo_manager.sync_if_needed()
                    event_handler.pending_sync = False
    except KeyboardInterrupt:
        logger.info("Stopping file watcher...")
        observer.stop()
    finally:
        observer.join()
        logger.info("Auto-sync stopped")

def main():
    parser = argparse.ArgumentParser(description="GitHub Repository Auto-Sync Tool")
    
    parser.add_argument("--dir", "-d", required=True, 
                      help="Local directory to sync")
    parser.add_argument("--repo", "-r", required=True,
                      help="GitHub repository name (format: username/repo or repo)")
    parser.add_argument("--branch", "-b", default="main",
                      help="Branch to sync with (default: main)")
    parser.add_argument("--interval", "-i", type=int, default=300,
                      help="Minimum interval between commits in seconds (default: 300)")
    
    args = parser.parse_args()
    
    try:
        config = GitHubSyncConfig(
            local_dir=args.dir,
            repo_name=args.repo,
            branch=args.branch,
            commit_interval=args.interval
        )
        
        run_auto_sync(config)
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()