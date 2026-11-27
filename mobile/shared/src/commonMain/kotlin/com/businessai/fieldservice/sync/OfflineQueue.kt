package com.businessai.fieldservice.sync

import com.businessai.fieldservice.models.SyncEntityType
import com.businessai.fieldservice.models.SyncOp
import com.businessai.fieldservice.models.SyncOpStatus
import com.businessai.fieldservice.models.SyncOperation

/**
 * In-memory + pluggable persistence for UUID offline operations.
 * Drain order is FIFO; conflicts are never auto-cleared.
 */
class OfflineQueue(
    private val store: QueueStore = InMemoryQueueStore(),
) {
    private val ops: MutableList<SyncOp> = store.load().toMutableList()

    fun snapshot(): List<SyncOp> = ops.toList()

    fun pendingCount(workOrderId: String? = null): Int =
        ops.count {
            (workOrderId == null || it.workOrderId == workOrderId) &&
                it.status in setOf(SyncOpStatus.PENDING, SyncOpStatus.SYNCING, SyncOpStatus.FAILED)
        }

    fun conflictCount(workOrderId: String? = null): Int =
        ops.count {
            (workOrderId == null || it.workOrderId == workOrderId) &&
                it.status == SyncOpStatus.CONFLICT
        }

    fun opsForWorkOrder(workOrderId: String): List<SyncOp> =
        ops.filter { it.workOrderId == workOrderId }

    fun enqueue(op: SyncOp) {
        require(op.status == SyncOpStatus.PENDING) { "New ops must start PENDING" }
        ops += op
        persist()
    }

    fun update(op: SyncOp) {
        val idx = ops.indexOfFirst { it.id == op.id }
        require(idx >= 0) { "Unknown op ${op.id}" }
        ops[idx] = op
        persist()
    }

    fun remove(opId: String) {
        ops.removeAll { it.id == opId }
        persist()
    }

    fun removeSynced() {
        ops.removeAll { it.status == SyncOpStatus.SYNCED }
        persist()
    }

    /** FIFO drain candidates: pending + failed (retryable), not conflict. */
    fun drainCandidates(): List<SyncOp> =
        ops.filter {
            it.status == SyncOpStatus.PENDING || it.status == SyncOpStatus.FAILED
        }

    fun markSyncing(opId: String) {
        mutate(opId) { it.copy(status = SyncOpStatus.SYNCING) }
    }

    fun markSynced(opId: String) {
        mutate(opId) { it.copy(status = SyncOpStatus.SYNCED, lastError = null, serverSnapshotJson = null) }
    }

    fun markConflict(opId: String, serverSnapshotJson: String, message: String) {
        mutate(opId) {
            it.copy(
                status = SyncOpStatus.CONFLICT,
                lastError = message,
                serverSnapshotJson = serverSnapshotJson,
            )
        }
    }

    fun markFailed(opId: String, message: String) {
        mutate(opId) {
            it.copy(
                status = SyncOpStatus.FAILED,
                retryCount = it.retryCount + 1,
                lastError = message,
            )
        }
    }

    /** Keep-local: reset to PENDING with refreshed base so drain can retry. */
    fun resolveKeepLocal(opId: String, freshBaseUpdatedAt: String?) {
        mutate(opId) {
            it.copy(
                status = SyncOpStatus.PENDING,
                baseUpdatedAt = freshBaseUpdatedAt ?: it.baseUpdatedAt,
                serverSnapshotJson = null,
                lastError = null,
            )
        }
    }

    /** Take-server: drop the local op (caller refreshes job from server). */
    fun resolveTakeServer(opId: String) {
        remove(opId)
    }

    private fun mutate(opId: String, transform: (SyncOp) -> SyncOp) {
        val idx = ops.indexOfFirst { it.id == opId }
        require(idx >= 0) { "Unknown op $opId" }
        ops[idx] = transform(ops[idx])
        persist()
    }

    private fun persist() {
        store.save(ops.toList())
    }

    companion object {
        fun notePayload(note: String, clientOccurredAt: String): String =
            """{"note":"${escape(note)}","client_occurred_at":"$clientOccurredAt"}"""

        fun statusPayload(status: String): String =
            """{"status":"$status"}"""

        fun checklistPayload(isCompleted: Boolean): String =
            """{"is_completed":$isCompleted}"""

        private fun escape(value: String): String =
            value.replace("\\", "\\\\").replace("\"", "\\\"")
    }
}

interface QueueStore {
    fun load(): List<SyncOp>
    fun save(ops: List<SyncOp>)
}

/** Default store for tests and platforms without file I/O yet. */
class InMemoryQueueStore(
    initial: List<SyncOp> = emptyList(),
) : QueueStore {
    private var data: List<SyncOp> = initial

    override fun load(): List<SyncOp> = data

    override fun save(ops: List<SyncOp>) {
        data = ops.toList()
    }
}

/**
 * Compact line-oriented serializer so Android can persist without kotlinx.serialization.
 * Format per line: id|entityType|entityId|workOrderId|operation|status|retry|base|localTs|payload|error|server
 */
object SyncOpCodec {
    private const val SEP = "\u001f"

    fun encodeAll(ops: List<SyncOp>): String =
        ops.joinToString("\n") { encode(it) }

    fun decodeAll(text: String): List<SyncOp> =
        text
            .lineSequence()
            .map { it.trim() }
            .filter { it.isNotEmpty() }
            .mapNotNull { runCatching { decode(it) }.getOrNull() }
            .toList()

    fun encode(op: SyncOp): String =
        listOf(
            op.id,
            op.entityType.name,
            op.entityId,
            op.workOrderId,
            op.operation.name,
            op.status.name,
            op.retryCount.toString(),
            op.baseUpdatedAt.orEmpty(),
            op.localTimestamp,
            op.payloadJson.replace("\n", "\\n"),
            op.lastError.orEmpty().replace(SEP, " "),
            op.serverSnapshotJson.orEmpty().replace("\n", "\\n"),
        ).joinToString(SEP)

    fun decode(line: String): SyncOp {
        val p = line.split(SEP)
        require(p.size >= 10) { "Bad SyncOp line" }
        return SyncOp(
            id = p[0],
            entityType = SyncEntityType.valueOf(p[1]),
            entityId = p[2],
            workOrderId = p[3],
            operation = SyncOperation.valueOf(p[4]),
            status = SyncOpStatus.valueOf(p[5]),
            retryCount = p[6].toIntOrNull() ?: 0,
            baseUpdatedAt = p[7].ifBlank { null },
            localTimestamp = p[8],
            payloadJson = p[9].replace("\\n", "\n"),
            lastError = p.getOrNull(10)?.ifBlank { null },
            serverSnapshotJson = p.getOrNull(11)?.ifBlank { null }?.replace("\\n", "\n"),
        )
    }
}
