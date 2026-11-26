package com.businessai.fieldservice.models

/**
 * Shared domain stubs for technician agenda.
 * Full entities land with backend models + sync.
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
)
