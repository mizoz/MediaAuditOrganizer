// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};
use std::sync::{Arc, Mutex};
use std::fs;

// Import shared types from lib
use media_audit_organizer_lib::{TaskStatus, AppState};

// ===== DATA STRUCTURES =====

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SubAgent {
    pub id: String,
    pub name: String,
    pub status: String,
    pub progress: Option<u8>,
    pub logs: Option<Vec<String>>,
    pub eta: Option<String>,
    pub last_updated: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DriveInfo {
    pub id: String,
    pub name: String,
    pub mount_point: String,
    pub total_space: u64,
    pub used_space: u64,
    pub available_space: u64,
    pub is_target: Option<bool>,
    pub is_source: Option<bool>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Asset {
    pub id: String,
    pub filename: String,
    pub path: String,
    pub asset_type: String,
    pub size: u64,
    pub created_at: String,
    pub modified_at: String,
    pub camera_model: Option<String>,
    pub resolution: Option<String>,
    pub duration: Option<u64>,
    pub hash: Option<String>,
    pub is_duplicate: Option<bool>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowPhase {
    pub id: u32,
    pub name: String,
    pub description: String,
    pub status: String,
    pub progress: u8,
    pub dependencies: Option<Vec<u32>>,
    pub started_at: Option<String>,
    pub completed_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConfirmationItem {
    pub id: String,
    pub title: String,
    pub description: String,
    pub file_count: u64,
    pub total_size: u64,
    pub risk_level: String,
    pub details: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConfirmationGate {
    pub id: String,
    pub phase: u32,
    pub items: Vec<ConfirmationItem>,
    pub requires_approval: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommandResponse<T> {
    pub success: bool,
    pub data: Option<T>,
    pub error: Option<String>,
}

// ===== TAURI COMMANDS =====

#[tauri::command]
fn get_agent_status() -> Result<Vec<SubAgent>, String> {
    // In production, this would query the Python sidecar
    // For now, return mock data
    Ok(vec![
        SubAgent {
            id: "SA-01".to_string(),
            name: "env-validator".to_string(),
            status: "success".to_string(),
            progress: Some(100),
            logs: Some(vec!["Environment validated".to_string()]),
            eta: None,
            last_updated: chrono::Utc::now().to_rfc3339(),
        },
        SubAgent {
            id: "SA-05".to_string(),
            name: "audit-executor".to_string(),
            status: "processing".to_string(),
            progress: Some(67),
            logs: Some(vec!["Scanning...".to_string()]),
            eta: Some("15 minutes".to_string()),
            last_updated: chrono::Utc::now().to_rfc3339(),
        },
    ])
}

#[tauri::command]
fn get_workflow_phases() -> Result<Vec<WorkflowPhase>, String> {
    Ok(vec![
        WorkflowPhase {
            id: 1,
            name: "Environment Validation".to_string(),
            description: "Validate Python environment and dependencies".to_string(),
            status: "completed".to_string(),
            progress: 100,
            dependencies: None,
            started_at: None,
            completed_at: None,
        },
        WorkflowPhase {
            id: 5,
            name: "Audit Execution".to_string(),
            description: "Execute comprehensive media audit".to_string(),
            status: "active".to_string(),
            progress: 67,
            dependencies: Some(vec![4]),
            started_at: None,
            completed_at: None,
        },
    ])
}

#[tauri::command]
fn scan_drives() -> Result<Vec<DriveInfo>, String> {
    // In production, this would scan actual system drives
    Ok(vec![
        DriveInfo {
            id: "drive-1".to_string(),
            name: "Samsung T7 Shield 2TB".to_string(),
            mount_point: "/media/az/SAMSUNG_T7_1".to_string(),
            total_space: 2000000000000,
            used_space: 1450000000000,
            available_space: 550000000000,
            is_target: None,
            is_source: Some(true),
        },
        DriveInfo {
            id: "drive-3".to_string(),
            name: "Seagate IronWolf 12TB".to_string(),
            mount_point: "/media/az/IRONWOLF_12TB".to_string(),
            total_space: 12000000000000,
            used_space: 3200000000000,
            available_space: 8800000000000,
            is_target: Some(true),
            is_source: None,
        },
    ])
}

#[tauri::command]
fn query_database(
    filters: Option<serde_json::Value>,
    page: Option<u32>,
    page_size: Option<u32>,
) -> Result<serde_json::Value, String> {
    // In production, this would query the SQLite database
    // For now, return mock data structure
    Ok(serde_json::json!({
        "assets": [],
        "total": 0,
        "page": page.unwrap_or(1),
        "page_size": page_size.unwrap_or(100),
        "total_pages": 0
    }))
}

#[tauri::command]
fn run_audit(source: String, target: String, dry_run: bool) -> Result<CommandResponse<serde_json::Value>, String> {
    log::info!("Running audit: source={}, target={}, dry_run={}", source, target, dry_run);
    
    // In production, this would spawn the Python sidecar
    // let output = Command::new("python")
    //     .arg("../scripts/audit_drive.py")
    //     .arg("--source")
    //     .arg(&source)
    //     .arg("--target")
    //     .arg(&target)
    //     .output()
    //     .map_err(|e| e.to_string())?;
    
    Ok(CommandResponse {
        success: true,
        data: Some(serde_json::json!({
            "message": "Audit started",
            "source": source,
            "target": target,
            "dry_run": dry_run
        })),
        error: None,
    })
}

#[tauri::command]
fn run_deduplication(source: String, action: String) -> Result<CommandResponse<serde_json::Value>, String> {
    log::info!("Running deduplication: source={}, action={}", source, action);
    
    Ok(CommandResponse {
        success: true,
        data: Some(serde_json::json!({
            "message": "Deduplication started",
            "source": source,
            "action": action
        })),
        error: None,
    })
}

#[tauri::command]
fn approve_phase(phase_id: u32) -> Result<CommandResponse<bool>, String> {
    log::info!("Approving phase: {}", phase_id);
    
    Ok(CommandResponse {
        success: true,
        data: Some(true),
        error: None,
    })
}

#[tauri::command]
fn reject_phase(phase_id: u32, reason: String) -> Result<CommandResponse<bool>, String> {
    log::info!("Rejecting phase {}: {}", phase_id, reason);
    
    Ok(CommandResponse {
        success: true,
        data: Some(false),
        error: None,
    })
}

#[tauri::command]
fn get_system_info() -> Result<serde_json::Value, String> {
    let info = serde_json::json!({
        "platform": std::env::consts::OS,
        "arch": std::env::consts::ARCH,
        "rust_version": env!("CARGO_PKG_VERSION"),
    });
    Ok(info)
}

// ===== TASK MANAGEMENT COMMANDS =====

#[tauri::command]
fn get_task_status(task_id: String, state: tauri::State<AppState>) -> Result<TaskStatus, String> {
    let tasks = state.tasks.lock().map_err(|e| e.to_string())?;
    
    tasks.get(&task_id)
        .cloned()
        .ok_or_else(|| format!("Task {} not found", task_id))
}

#[tauri::command]
fn list_active_tasks(state: tauri::State<AppState>) -> Result<Vec<TaskStatus>, String> {
    let tasks = state.tasks.lock().map_err(|e| e.to_string())?;
    
    let active: Vec<TaskStatus> = tasks
        .values()
        .filter(|t| t.status == "running" || t.status == "pending")
        .cloned()
        .collect();
    
    Ok(active)
}

#[tauri::command]
fn cancel_task(task_id: String, state: tauri::State<AppState>) -> Result<bool, String> {
    let mut tasks = state.tasks.lock().map_err(|e| e.to_string())?;
    
    if let Some(task) = tasks.get_mut(&task_id) {
        if task.status == "running" || task.status == "pending" {
            task.status = "cancelled".to_string();
            task.completed_at = Some(chrono::Utc::now().to_rfc3339());
            
            // Try to cancel the actual process (if we have a PID stored)
            // For now, just mark as cancelled
            log::info!("Task {} cancelled", task_id);
            return Ok(true);
        }
        return Err(format!("Task {} is not running", task_id));
    }
    
    Err(format!("Task {} not found", task_id))
}

#[tauri::command]
fn get_task_logs(task_id: String, lines: u32, state: tauri::State<AppState>) -> Result<String, String> {
    let tasks = state.tasks.lock().map_err(|e| e.to_string())?;
    
    let task = tasks.get(&task_id)
        .ok_or_else(|| format!("Task {} not found", task_id))?;
    
    let log_file = task.log_file.as_ref()
        .ok_or_else(|| format!("No log file for task {}", task_id))?;
    
    // Read last N lines from log file
    let content = fs::read_to_string(log_file)
        .map_err(|e| format!("Failed to read log file: {}", e))?;
    
    let all_lines: Vec<&str> = content.lines().collect();
    let start = if all_lines.len() > lines as usize {
        all_lines.len() - lines as usize
    } else {
        0
    };
    
    Ok(all_lines[start..].join("\n"))
}

// ===== MAIN FUNCTION =====

fn main() {
    // Initialize logging
    env_logger::init();
    
    // Initialize shared state for task management
    let app_state = AppState {
        tasks: Arc::new(Mutex::new(std::collections::HashMap::new())),
    };
    
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_process::init())
        .manage(app_state)
        .invoke_handler(tauri::generate_handler![
            get_agent_status,
            get_workflow_phases,
            scan_drives,
            query_database,
            run_audit,
            run_deduplication,
            approve_phase,
            reject_phase,
            get_system_info,
            get_task_status,
            list_active_tasks,
            cancel_task,
            get_task_logs,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
