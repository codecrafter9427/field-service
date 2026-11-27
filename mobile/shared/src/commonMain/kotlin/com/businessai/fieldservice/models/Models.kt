package com.businessai.fieldservice.models

/**
 * Shared domain models for technician agenda + job detail + M5 offline sync.
 */

data class WorkOrderSummary(
    val id: String,
    val title: String,
    val customerName: String,
    val status: String,
    val scheduledStartIso: String?,
    val priority: String,
    val syncBadge: SyncBadge = SyncBadge.NONE,
)

data class AgendaDay(
    val dateIso: String,
    val jobs: List<WorkOrderSummary>,
    val source: String = "demo",
)

data class JobNote(
    val id: String?,
    val text: String,
    val activityType: String = "note",
    val pending: Boolean = false,
    val clientOperationId: String? = null,
)

data class ChecklistItemView(
    val id: String,
    val label: String,
    val isCompleted: Boolean,
    val updatedAt: String,
    val pending: Boolean = false,
)

data class ChecklistView(
    val id: String,
    val name: String,
    val items: List<ChecklistItemView>,
)

data class JobDetail(
    val id: String,
    val title: String,
    val status: String,
    val priority: String,
    val description: String?,
    val customerId: String,
    val technicianName: String?,
    val scheduledStartIso: String?,
    val scheduledEndIso: String?,
    val updatedAt: String,
    val notes: List<JobNote> = emptyList(),
    val checklists: List<ChecklistView> = emptyList(),
    val syncBadge: SyncBadge = SyncBadge.NONE,
)

data class LoginSession(
    val accessToken: String,
    val displayName: String,
    val role: String,
    val email: String,
)

enum class SyncBadge {
    NONE,
    PENDING,
    SYNCING,
    CONFLICT,
    FAILED,
}

enum class SyncOpStatus {
    PENDING,
    SYNCING,
    SYNCED,
    CONFLICT,
    FAILED,
}

enum class SyncEntityType {
    NOTE,
    CHECKLIST_ITEM,
    WORK_ORDER_STATUS,
}

enum class SyncOperation {
    CREATE,
    UPDATE,
}

enum class ConflictResolution {
    KEEP_LOCAL,
    TAKE_SERVER,
}

/**
 * UUID-keyed offline mutation queued locally until drain succeeds or conflicts.
 */
data class SyncOp(
    val id: String,
    val entityType: SyncEntityType,
    val entityId: String,
    val workOrderId: String,
    val operation: SyncOperation,
    val payloadJson: String,
    val baseUpdatedAt: String?,
    val localTimestamp: String,
    val status: SyncOpStatus = SyncOpStatus.PENDING,
    val retryCount: Int = 0,
    val lastError: String? = null,
    val serverSnapshotJson: String? = null,
)

data class ConflictView(
    val op: SyncOp,
    val localSummary: String,
    val serverSummary: String,
)
