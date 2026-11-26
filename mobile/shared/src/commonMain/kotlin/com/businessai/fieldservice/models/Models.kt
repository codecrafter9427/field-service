package com.businessai.fieldservice.models

/**
 * Shared domain models for technician agenda + job detail (M4).
 * Maps to FastAPI `/assignments/agenda` and work-order detail payloads.
 */
data class WorkOrderSummary(
    val id: String,
    val title: String,
    val customerName: String,
    val status: String,
    val scheduledStartIso: String?,
    val priority: String,
)

data class AgendaDay(
    val dateIso: String,
    val jobs: List<WorkOrderSummary>,
    val source: String = "demo",
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
    val notes: List<String> = emptyList(),
)

data class LoginSession(
    val accessToken: String,
    val displayName: String,
    val role: String,
    val email: String,
)
