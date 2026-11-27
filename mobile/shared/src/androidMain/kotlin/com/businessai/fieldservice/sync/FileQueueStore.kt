package com.businessai.fieldservice.sync

import com.businessai.fieldservice.models.SyncOp
import java.io.File

/**
 * Persists the offline UUID op queue as a text file under app storage.
 */
class FileQueueStore(
    private val file: File,
) : QueueStore {
    override fun load(): List<SyncOp> {
        if (!file.exists()) return emptyList()
        return SyncOpCodec.decodeAll(file.readText(Charsets.UTF_8))
    }

    override fun save(ops: List<SyncOp>) {
        file.parentFile?.mkdirs()
        file.writeText(SyncOpCodec.encodeAll(ops), Charsets.UTF_8)
    }
}
