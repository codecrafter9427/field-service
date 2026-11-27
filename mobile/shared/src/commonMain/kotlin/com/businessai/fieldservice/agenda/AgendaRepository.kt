package com.businessai.fieldservice.agenda

import com.businessai.fieldservice.api.ApiClient
import com.businessai.fieldservice.models.AgendaDay
import com.businessai.fieldservice.models.ConflictResolution
import com.businessai.fieldservice.models.ConflictView
import com.businessai.fieldservice.models.JobDetail
import com.businessai.fieldservice.models.JobNote
import com.businessai.fieldservice.models.SyncBadge
import com.businessai.fieldservice.models.WorkOrderSummary
import com.businessai.fieldservice.sync.DrainResult
import com.businessai.fieldservice.sync.OfflineQueue
import com.businessai.fieldservice.sync.SyncRepository

/**
 * Technician agenda + job detail + M5 offline sync facade.
 *
 * Tries live API; falls back to demo stubs for agenda/login when unreachable.
 * Offline drafts always go to the UUID queue (never demo-only memory).
 */
class AgendaRepository(
    private val api: ApiClient = ApiClient(),
    private val preferLive: Boolean = true,
    queue: OfflineQueue = OfflineQueue(),
) {
    val sync: SyncRepository = SyncRepository(api, queue)

    fun todayAgenda(
        email: String = ApiClient.DEMO_TECH_EMAIL,
        password: String = ApiClient.DEMO_PASSWORD,
    ): AgendaDay {
        if (preferLive) {
            try {
                api.demoLogin(email, password)
                val day = api.fetchAgenda()
                return day.copy(
                    jobs =
                        day.jobs.map { job ->
                            job.copy(syncBadge = sync.badgeFor(job.id))
                        },
                )
            } catch (_: Exception) {
                // Fall through to demo stubs
            }
        }
        return demoAgenda().copy(
            jobs =
                demoAgenda().jobs.map { job ->
                    job.copy(syncBadge = sync.badgeFor(job.id))
                },
        )
    }

    fun jobDetail(
        workOrderId: String,
        email: String = ApiClient.DEMO_TECH_EMAIL,
        password: String = ApiClient.DEMO_PASSWORD,
    ): JobDetail {
        sync.cachedJob(workOrderId)?.let { return it }

        if (preferLive) {
            try {
                if (api.accessToken == null) {
                    api.demoLogin(email, password)
                }
                val remote = api.fetchJobDetail(workOrderId)
                sync.cacheJob(remote)
                return sync.cachedJob(workOrderId) ?: remote
            } catch (_: Exception) {
                // Fall through — if we have a cached offline draft, prefer it
                sync.cachedJob(workOrderId)?.let { return it }
            }
        }
        val demo = demoJobDetail(workOrderId)
        sync.cacheJob(demo)
        return sync.cachedJob(workOrderId) ?: demo
    }

    fun addNote(workOrderId: String, text: String): JobDetail {
        // Ensure cache is warm
        jobDetail(workOrderId)
        return sync.addNoteOffline(workOrderId, text)
    }

    fun toggleChecklist(workOrderId: String, itemId: String, isCompleted: Boolean): JobDetail {
        jobDetail(workOrderId)
        return sync.toggleChecklistOffline(workOrderId, itemId, isCompleted)
    }

    fun changeStatus(workOrderId: String, status: String): JobDetail {
        jobDetail(workOrderId)
        return sync.changeStatusOffline(workOrderId, status)
    }

    fun drainQueue(): DrainResult = sync.drain()

    fun conflicts(workOrderId: String): List<ConflictView> = sync.conflictsFor(workOrderId)

    fun resolveConflict(opId: String, resolution: ConflictResolution): JobDetail? =
        sync.resolveConflict(opId, resolution)

    fun pendingCount(): Int = sync.queueSnapshot().count {
        it.status.name in setOf("PENDING", "FAILED", "SYNCING")
    }

    fun healthHint(): String = api.healthHint()

    private fun demoAgenda(): AgendaDay =
        AgendaDay(
            dateIso = "2026-11-26",
            source = "demo",
            jobs =
                listOf(
                    WorkOrderSummary(
                        id = "00000000-0000-4000-8000-000000000101",
                        title = "HVAC filter check (demo)",
                        customerName = "Acme Facilities (demo)",
                        status = "scheduled",
                        scheduledStartIso = "2026-11-26T09:00:00Z",
                        priority = "normal",
                    ),
                    WorkOrderSummary(
                        id = "00000000-0000-4000-8000-000000000102",
                        title = "Pump seal inspection (demo)",
                        customerName = "River Plant (demo)",
                        status = "en_route",
                        scheduledStartIso = "2026-11-26T13:00:00Z",
                        priority = "high",
                    ),
                ),
        )

    private fun demoJobDetail(workOrderId: String): JobDetail =
        JobDetail(
            id = workOrderId,
            title = "Demo job detail",
            status = "scheduled",
            priority = "normal",
            description = "Offline/demo fallback — start API on :8003 for live data.",
            customerId = "00000000-0000-4000-8000-000000000001",
            technicianName = "Demo Tech",
            scheduledStartIso = "2026-11-26T09:00:00Z",
            scheduledEndIso = "2026-11-26T11:00:00Z",
            updatedAt = "2026-11-26T08:00:00Z",
            notes =
                listOf(
                    JobNote(
                        id = "demo-note",
                        text = "Demo note — connect to API for real activities.",
                    ),
                ),
            checklists = emptyList(),
            syncBadge = SyncBadge.NONE,
        )
}
