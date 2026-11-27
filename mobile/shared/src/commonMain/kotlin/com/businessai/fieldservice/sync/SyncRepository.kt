package com.businessai.fieldservice.sync

import com.businessai.fieldservice.api.ApiClient
import com.businessai.fieldservice.api.ConflictException
import com.businessai.fieldservice.api.HttpException
import com.businessai.fieldservice.api.JsonLite
import com.businessai.fieldservice.api.toConflictOrRethrow
import com.businessai.fieldservice.currentTimeIso
import com.businessai.fieldservice.models.ConflictResolution
import com.businessai.fieldservice.models.ConflictView
import com.businessai.fieldservice.models.JobDetail
import com.businessai.fieldservice.models.JobNote
import com.businessai.fieldservice.models.SyncBadge
import com.businessai.fieldservice.models.SyncEntityType
import com.businessai.fieldservice.models.SyncOp
import com.businessai.fieldservice.models.SyncOpStatus
import com.businessai.fieldservice.models.SyncOperation
import com.businessai.fieldservice.randomUuid

/**
 * Orchestrates offline apply + UUID queue drain + visible conflict handling.
 * Notes are append-only (idempotent). Status/checklist never silent-overwrite.
 */
class SyncRepository(
    private val api: ApiClient,
    private val queue: OfflineQueue = OfflineQueue(),
) {
    private val jobCache = mutableMapOf<String, JobDetail>()
    private var lastDrainMessage: String? = null

    fun queueSnapshot(): List<SyncOp> = queue.snapshot()

    fun lastDrainMessage(): String? = lastDrainMessage

    fun badgeFor(workOrderId: String): SyncBadge {
        if (queue.conflictCount(workOrderId) > 0) return SyncBadge.CONFLICT
        val ops = queue.opsForWorkOrder(workOrderId)
        if (ops.any { it.status == SyncOpStatus.SYNCING }) return SyncBadge.SYNCING
        if (ops.any { it.status == SyncOpStatus.FAILED }) return SyncBadge.FAILED
        if (queue.pendingCount(workOrderId) > 0) return SyncBadge.PENDING
        return SyncBadge.NONE
    }

    fun conflictsFor(workOrderId: String): List<ConflictView> =
        queue.opsForWorkOrder(workOrderId)
            .filter { it.status == SyncOpStatus.CONFLICT }
            .map { op ->
                ConflictView(
                    op = op,
                    localSummary = localSummary(op),
                    serverSummary = serverSummary(op),
                )
            }

    fun cacheJob(detail: JobDetail) {
        jobCache[detail.id] = detail.copy(syncBadge = badgeFor(detail.id))
    }

    fun cachedJob(workOrderId: String): JobDetail? =
        jobCache[workOrderId]?.copy(syncBadge = badgeFor(workOrderId))

    fun ensureLoggedIn(
        email: String = ApiClient.DEMO_TECH_EMAIL,
        password: String = ApiClient.DEMO_PASSWORD,
    ) {
        if (api.accessToken == null) {
            api.demoLogin(email, password)
        }
    }

    fun addNoteOffline(workOrderId: String, noteText: String): JobDetail {
        val detail = requireJob(workOrderId)
        val opId = randomUuid()
        val occurred = currentTimeIso()
        val op =
            SyncOp(
                id = opId,
                entityType = SyncEntityType.NOTE,
                entityId = workOrderId,
                workOrderId = workOrderId,
                operation = SyncOperation.CREATE,
                payloadJson = OfflineQueue.notePayload(noteText.trim(), occurred),
                baseUpdatedAt = null,
                localTimestamp = occurred,
            )
        queue.enqueue(op)
        val updated =
            detail.copy(
                notes =
                    listOf(
                        JobNote(
                            id = null,
                            text = noteText.trim(),
                            pending = true,
                            clientOperationId = opId,
                        ),
                    ) + detail.notes,
                syncBadge = SyncBadge.PENDING,
            )
        jobCache[workOrderId] = updated
        return updated
    }

    fun toggleChecklistOffline(
        workOrderId: String,
        itemId: String,
        isCompleted: Boolean,
    ): JobDetail {
        val detail = requireJob(workOrderId)
        val item =
            detail.checklists.flatMap { it.items }.find { it.id == itemId }
                ?: error("Checklist item not in cache")
        val occurred = currentTimeIso()
        val op =
            SyncOp(
                id = randomUuid(),
                entityType = SyncEntityType.CHECKLIST_ITEM,
                entityId = itemId,
                workOrderId = workOrderId,
                operation = SyncOperation.UPDATE,
                payloadJson = OfflineQueue.checklistPayload(isCompleted),
                baseUpdatedAt = item.updatedAt,
                localTimestamp = occurred,
            )
        queue.enqueue(op)
        val updated =
            detail.copy(
                checklists =
                    detail.checklists.map { cl ->
                        cl.copy(
                            items =
                                cl.items.map { ci ->
                                    if (ci.id == itemId) {
                                        ci.copy(isCompleted = isCompleted, pending = true)
                                    } else {
                                        ci
                                    }
                                },
                        )
                    },
                syncBadge = SyncBadge.PENDING,
            )
        jobCache[workOrderId] = updated
        return updated
    }

    fun changeStatusOffline(workOrderId: String, status: String): JobDetail {
        val detail = requireJob(workOrderId)
        val occurred = currentTimeIso()
        val op =
            SyncOp(
                id = randomUuid(),
                entityType = SyncEntityType.WORK_ORDER_STATUS,
                entityId = workOrderId,
                workOrderId = workOrderId,
                operation = SyncOperation.UPDATE,
                payloadJson = OfflineQueue.statusPayload(status),
                baseUpdatedAt = detail.updatedAt,
                localTimestamp = occurred,
            )
        queue.enqueue(op)
        val updated =
            detail.copy(
                status = status,
                syncBadge = SyncBadge.PENDING,
            )
        jobCache[workOrderId] = updated
        return updated
    }

    /**
     * Drain pending/failed ops FIFO. Stops applying further ops for a work order
     * once a conflict is recorded (never silent overwrite).
     */
    fun drain(
        email: String = ApiClient.DEMO_TECH_EMAIL,
        password: String = ApiClient.DEMO_PASSWORD,
    ): DrainResult {
        var synced = 0
        var conflicts = 0
        var failed = 0
        val blockedWorkOrders = mutableSetOf<String>()

        try {
            ensureLoggedIn(email, password)
        } catch (e: Exception) {
            lastDrainMessage = "Login failed: ${e.message}"
            return DrainResult(0, 0, queue.pendingCount(), lastDrainMessage)
        }

        for (op in queue.drainCandidates()) {
            if (op.workOrderId in blockedWorkOrders) continue
            if (queue.conflictCount(op.workOrderId) > 0) {
                blockedWorkOrders += op.workOrderId
                continue
            }
            queue.markSyncing(op.id)
            try {
                when (op.entityType) {
                    SyncEntityType.NOTE -> {
                        val note = JsonLite.stringField(op.payloadJson, "note") ?: ""
                        val occurred =
                            JsonLite.stringField(op.payloadJson, "client_occurred_at")
                                ?: op.localTimestamp
                        api.postNote(op.workOrderId, note, op.id, occurred)
                    }
                    SyncEntityType.WORK_ORDER_STATUS -> {
                        val status = JsonLite.requiredString(op.payloadJson, "status")
                        val base = op.baseUpdatedAt ?: error("Missing base_updated_at")
                        api.patchStatus(op.workOrderId, status, base)
                    }
                    SyncEntityType.CHECKLIST_ITEM -> {
                        val completed = JsonLite.boolField(op.payloadJson, "is_completed") ?: false
                        val base = op.baseUpdatedAt ?: error("Missing base_updated_at")
                        api.patchChecklistItem(op.entityId, completed, base)
                    }
                }
                queue.markSynced(op.id)
                synced++
                refreshCacheFromServer(op.workOrderId)
            } catch (e: ConflictException) {
                queue.markConflict(op.id, e.serverSnapshotJson ?: "{}", e.message ?: "conflict")
                conflicts++
                blockedWorkOrders += op.workOrderId
            } catch (e: HttpException) {
                try {
                    e.toConflictOrRethrow()
                } catch (c: ConflictException) {
                    queue.markConflict(op.id, c.serverSnapshotJson ?: "{}", c.message ?: "conflict")
                    conflicts++
                    blockedWorkOrders += op.workOrderId
                } catch (other: HttpException) {
                    queue.markFailed(op.id, "HTTP ${other.statusCode}: ${other.message}")
                    failed++
                }
            } catch (e: Exception) {
                queue.markFailed(op.id, e.message ?: "drain failed")
                failed++
            }
        }
        queue.removeSynced()
        lastDrainMessage =
            "Synced $synced · conflicts $conflicts · failed $failed · pending ${queue.pendingCount()}"
        return DrainResult(synced, conflicts, failed, lastDrainMessage)
    }

    fun resolveConflict(
        opId: String,
        resolution: ConflictResolution,
    ): JobDetail? {
        val op = queue.snapshot().find { it.id == opId } ?: return null
        when (resolution) {
            ConflictResolution.TAKE_SERVER -> {
                queue.resolveTakeServer(opId)
                refreshCacheFromServer(op.workOrderId)
            }
            ConflictResolution.KEEP_LOCAL -> {
                // Re-fetch server to get fresh base, then re-queue with same payload
                val fresh = refreshCacheFromServer(op.workOrderId)
                val freshBase =
                    when (op.entityType) {
                        SyncEntityType.WORK_ORDER_STATUS -> fresh?.updatedAt
                        SyncEntityType.CHECKLIST_ITEM ->
                            fresh
                                ?.checklists
                                ?.flatMap { it.items }
                                ?.find { it.id == op.entityId }
                                ?.updatedAt
                        SyncEntityType.NOTE -> null
                    }
                queue.resolveKeepLocal(opId, freshBase)
            }
        }
        return cachedJob(op.workOrderId)
    }

    private fun refreshCacheFromServer(workOrderId: String): JobDetail? =
        runCatching {
            val remote = api.fetchJobDetail(workOrderId)
            // Re-apply still-pending local overlays
            val merged = applyPendingOverlay(remote)
            jobCache[workOrderId] = merged
            merged
        }.getOrNull()

    private fun applyPendingOverlay(remote: JobDetail): JobDetail {
        var detail = remote
        val pending = queue.opsForWorkOrder(remote.id).filter {
            it.status in setOf(SyncOpStatus.PENDING, SyncOpStatus.FAILED, SyncOpStatus.CONFLICT, SyncOpStatus.SYNCING)
        }
        for (op in pending) {
            when (op.entityType) {
                SyncEntityType.NOTE -> {
                    val note = JsonLite.stringField(op.payloadJson, "note") ?: continue
                    if (detail.notes.none { it.clientOperationId == op.id }) {
                        detail =
                            detail.copy(
                                notes =
                                    listOf(
                                        JobNote(
                                            id = null,
                                            text = note,
                                            pending = true,
                                            clientOperationId = op.id,
                                        ),
                                    ) + detail.notes,
                            )
                    }
                }
                SyncEntityType.WORK_ORDER_STATUS -> {
                    val status = JsonLite.stringField(op.payloadJson, "status") ?: continue
                    if (op.status != SyncOpStatus.CONFLICT) {
                        detail = detail.copy(status = status)
                    }
                }
                SyncEntityType.CHECKLIST_ITEM -> {
                    val completed = JsonLite.boolField(op.payloadJson, "is_completed") ?: continue
                    if (op.status == SyncOpStatus.CONFLICT) continue
                    detail =
                        detail.copy(
                            checklists =
                                detail.checklists.map { cl ->
                                    cl.copy(
                                        items =
                                            cl.items.map { item ->
                                                if (item.id == op.entityId) {
                                                    item.copy(isCompleted = completed, pending = true)
                                                } else {
                                                    item
                                                }
                                            },
                                    )
                                },
                        )
                }
            }
        }
        return detail.copy(syncBadge = badgeFor(remote.id))
    }

    private fun requireJob(workOrderId: String): JobDetail =
        jobCache[workOrderId] ?: error("Job $workOrderId not cached — open detail online first")

    private fun localSummary(op: SyncOp): String =
        when (op.entityType) {
            SyncEntityType.NOTE -> "Local note: ${JsonLite.stringField(op.payloadJson, "note")}"
            SyncEntityType.WORK_ORDER_STATUS ->
                "Local status: ${JsonLite.stringField(op.payloadJson, "status")}"
            SyncEntityType.CHECKLIST_ITEM -> {
                val done = JsonLite.boolField(op.payloadJson, "is_completed")
                "Local checklist: ${if (done == true) "complete" else "incomplete"}"
            }
        }

    private fun serverSummary(op: SyncOp): String {
        val snap = op.serverSnapshotJson ?: return "Server snapshot unavailable"
        return when (op.entityType) {
            SyncEntityType.WORK_ORDER_STATUS ->
                "Server status: ${JsonLite.stringField(snap, "status") ?: "?"} @ ${JsonLite.stringField(snap, "updated_at") ?: "?"}"
            SyncEntityType.CHECKLIST_ITEM -> {
                val done = JsonLite.boolField(snap, "is_completed")
                "Server checklist: ${if (done == true) "complete" else "incomplete"} @ ${JsonLite.stringField(snap, "updated_at") ?: "?"}"
            }
            SyncEntityType.NOTE -> "Server already has this note (idempotent)"
        }
    }
}

data class DrainResult(
    val synced: Int,
    val conflicts: Int,
    val failed: Int,
    val message: String?,
)
