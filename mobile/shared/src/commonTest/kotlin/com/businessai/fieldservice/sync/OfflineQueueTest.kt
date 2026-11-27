package com.businessai.fieldservice.sync

import com.businessai.fieldservice.models.SyncEntityType
import com.businessai.fieldservice.models.SyncOp
import com.businessai.fieldservice.models.SyncOpStatus
import com.businessai.fieldservice.models.SyncOperation
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class OfflineQueueTest {
    private fun noteOp(id: String = "op-1"): SyncOp =
        SyncOp(
            id = id,
            entityType = SyncEntityType.NOTE,
            entityId = "wo-1",
            workOrderId = "wo-1",
            operation = SyncOperation.CREATE,
            payloadJson = OfflineQueue.notePayload("hello", "2026-11-27T00:00:00Z"),
            baseUpdatedAt = null,
            localTimestamp = "2026-11-27T00:00:00Z",
        )

    @Test
    fun enqueueAndDrainOrderIsFifo() {
        val store = InMemoryQueueStore()
        val queue = OfflineQueue(store)
        queue.enqueue(noteOp("a"))
        queue.enqueue(noteOp("b"))
        assertEquals(listOf("a", "b"), queue.drainCandidates().map { it.id })
    }

    @Test
    fun conflictIsNotAutoCleared() {
        val queue = OfflineQueue()
        queue.enqueue(noteOp())
        queue.markConflict("op-1", """{"status":"en_route"}""", "stale")
        assertEquals(1, queue.conflictCount("wo-1"))
        assertTrue(queue.drainCandidates().isEmpty())
        assertEquals(SyncOpStatus.CONFLICT, queue.snapshot().single().status)
    }

    @Test
    fun keepLocalRequeuesWithFreshBase() {
        val queue = OfflineQueue()
        val op =
            SyncOp(
                id = "status-1",
                entityType = SyncEntityType.WORK_ORDER_STATUS,
                entityId = "wo-1",
                workOrderId = "wo-1",
                operation = SyncOperation.UPDATE,
                payloadJson = OfflineQueue.statusPayload("in_progress"),
                baseUpdatedAt = "old",
                localTimestamp = "2026-11-27T00:00:00Z",
            )
        queue.enqueue(op)
        queue.markConflict("status-1", """{"status":"en_route"}""", "stale")
        queue.resolveKeepLocal("status-1", "fresh-base")
        val pending = queue.drainCandidates().single()
        assertEquals(SyncOpStatus.PENDING, pending.status)
        assertEquals("fresh-base", pending.baseUpdatedAt)
    }

    @Test
    fun takeServerRemovesOp() {
        val queue = OfflineQueue()
        queue.enqueue(noteOp())
        queue.markConflict("op-1", "{}", "x")
        queue.resolveTakeServer("op-1")
        assertTrue(queue.snapshot().isEmpty())
    }

    @Test
    fun codecRoundTripPersistsQueue() {
        val original =
            SyncOp(
                id = "c1",
                entityType = SyncEntityType.CHECKLIST_ITEM,
                entityId = "item-1",
                workOrderId = "wo-1",
                operation = SyncOperation.UPDATE,
                payloadJson = OfflineQueue.checklistPayload(true),
                baseUpdatedAt = "2026-11-27T01:00:00Z",
                localTimestamp = "2026-11-27T01:01:00Z",
                status = SyncOpStatus.PENDING,
            )
        val encoded = SyncOpCodec.encodeAll(listOf(original))
        val decoded = SyncOpCodec.decodeAll(encoded).single()
        assertEquals(original.id, decoded.id)
        assertEquals(original.entityType, decoded.entityType)
        assertEquals(original.payloadJson, decoded.payloadJson)
        assertEquals(original.baseUpdatedAt, decoded.baseUpdatedAt)

        val store = InMemoryQueueStore()
        store.save(listOf(original))
        assertEquals(1, store.load().size)
    }

    @Test
    fun failedOpsRemainDrainable() {
        val queue = OfflineQueue()
        queue.enqueue(noteOp())
        queue.markFailed("op-1", "network")
        assertEquals(1, queue.pendingCount())
        assertEquals(SyncOpStatus.FAILED, queue.drainCandidates().single().status)
    }
}
