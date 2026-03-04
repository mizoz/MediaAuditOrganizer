// Library module for shared types and helper functions
// This is required by Cargo.toml for the cdylib/staticlib builds

use serde::{Deserialize, Serialize};
use std::sync::{Arc, Mutex};
use tauri::Manager;

// Re-export types used by both lib and main
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskStatus {
    pub task_id: String,
    pub task_type: String,
    pub status: String, // pending, running, completed, failed, cancelled
    pub progress_pct: u8,
    pub started_at: String,
    pub completed_at: Option<String>,
    pub last_heartbeat: String,
    pub estimated_completion: Option<String>,
    pub files_processed: Option<u64>,
    pub files_total: Option<u64>,
    pub errors: Option<u64>,
    pub log_file: Option<String>,
}

// Shared state for task management
pub struct AppState {
    pub tasks: Arc<Mutex<std::collections::HashMap<String, TaskStatus>>>,
}

// Helper function to register a new task (called from Python sidecar or other sources)
pub fn register_task(
    state: &tauri::State<AppState>,
    task_id: String,
    task_type: String,
    log_file: Option<String>,
) -> Result<(), String> {
    let mut tasks = state.tasks.lock().map_err(|e| e.to_string())?;
    
    let now = chrono::Utc::now().to_rfc3339();
    let task = TaskStatus {
        task_id: task_id.clone(),
        task_type,
        status: "running".to_string(),
        progress_pct: 0,
        started_at: now.clone(),
        completed_at: None,
        last_heartbeat: now,
        estimated_completion: None,
        files_processed: None,
        files_total: None,
        errors: None,
        log_file,
    };
    
    tasks.insert(task_id, task);
    Ok(())
}

// Helper function to update task progress (called from Python sidecar or other sources)
pub fn update_task_progress(
    state: &tauri::State<AppState>,
    task_id: &str,
    progress_pct: u8,
    files_processed: Option<u64>,
    files_total: Option<u64>,
) -> Result<(), String> {
    let mut tasks = state.tasks.lock().map_err(|e| e.to_string())?;
    
    if let Some(task) = tasks.get_mut(task_id) {
        task.progress_pct = progress_pct;
        task.files_processed = files_processed;
        task.files_total = files_total;
        task.last_heartbeat = chrono::Utc::now().to_rfc3339();
    }
    
    Ok(())
}

// Helper function to complete a task (called from Python sidecar or other sources)
pub fn complete_task(
    state: &tauri::State<AppState>,
    task_id: &str,
    success: bool,
    errors: Option<u64>,
) -> Result<(), String> {
    let mut tasks = state.tasks.lock().map_err(|e| e.to_string())?;
    
    if let Some(task) = tasks.get_mut(task_id) {
        task.status = if success { "completed" } else { "failed" }.to_string();
        task.progress_pct = 100;
        task.completed_at = Some(chrono::Utc::now().to_rfc3339());
        task.errors = errors;
    }
    
    Ok(())
}
