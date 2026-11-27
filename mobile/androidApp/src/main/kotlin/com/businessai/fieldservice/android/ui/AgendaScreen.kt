package com.businessai.fieldservice.android.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.businessai.fieldservice.agenda.AgendaRepository
import com.businessai.fieldservice.models.ConflictResolution
import com.businessai.fieldservice.models.JobDetail
import com.businessai.fieldservice.models.SyncBadge
import com.businessai.fieldservice.models.WorkOrderSummary
import com.businessai.fieldservice.platformName
import com.businessai.fieldservice.sync.FileQueueStore
import com.businessai.fieldservice.sync.OfflineQueue
import java.io.File

private val STATUSES =
    listOf(
        "scheduled",
        "en_route",
        "in_progress",
        "waiting_for_parts",
        "completed",
        "cancelled",
    )

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AgendaScreen() {
    val context = LocalContext.current
    val repository =
        remember {
            val store =
                FileQueueStore(
                    File(context.filesDir, "offline_sync_queue.txt"),
                )
            AgendaRepository(queue = OfflineQueue(store))
        }

    var agenda by remember { mutableStateOf(repository.todayAgenda()) }
    var selectedJobId by remember { mutableStateOf<String?>(null) }
    var detail by remember { mutableStateOf<JobDetail?>(null) }
    var noteDraft by remember { mutableStateOf("") }
    var statusMessage by remember { mutableStateOf<String?>(null) }

    fun reloadAgenda() {
        agenda = repository.todayAgenda()
    }

    fun openJob(id: String) {
        selectedJobId = id
        detail = repository.jobDetail(id)
        noteDraft = ""
        statusMessage = null
    }

    fun refreshDetail() {
        val id = selectedJobId ?: return
        detail = repository.jobDetail(id)
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        if (detail == null) "Technician agenda" else "Job · offline sync",
                    )
                },
            )
        },
    ) { padding ->
        Column(
            modifier =
                Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(horizontal = 16.dp),
        ) {
            if (detail == null) {
                Text(
                    text = "Platform: ${platformName()} · source=${agenda.source}",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(bottom = 4.dp),
                )
                Text(
                    text = repository.healthHint(),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(bottom = 4.dp),
                )
                Text(
                    text = "Pending ops: ${repository.pendingCount()} · Date: ${agenda.dateIso}",
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.padding(bottom = 8.dp),
                )
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    modifier = Modifier.padding(bottom = 12.dp),
                ) {
                    Button(
                        onClick = {
                            val result = repository.drainQueue()
                            statusMessage = result.message
                            reloadAgenda()
                        },
                    ) {
                        Text("Sync now")
                    }
                    TextButton(onClick = { reloadAgenda() }) {
                        Text("Refresh")
                    }
                }
                statusMessage?.let {
                    Text(
                        it,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.padding(bottom = 8.dp),
                    )
                }
                LazyColumn(
                    contentPadding = PaddingValues(bottom = 24.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    items(agenda.jobs, key = { it.id }) { job ->
                        AgendaJobCard(job) { openJob(job.id) }
                    }
                }
            } else {
                val current = detail!!
                Column(
                    modifier =
                        Modifier
                            .fillMaxSize()
                            .verticalScroll(rememberScrollState())
                            .padding(bottom = 24.dp),
                ) {
                    Text(
                        text = "← Back to agenda",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.primary,
                        modifier =
                            Modifier
                                .padding(bottom = 8.dp)
                                .clickable {
                                    selectedJobId = null
                                    detail = null
                                    reloadAgenda()
                                },
                    )
                    SyncBadgeChip(current.syncBadge)
                    Text(current.title, style = MaterialTheme.typography.headlineSmall)
                    Text(
                        "${current.status} · ${current.priority}",
                        style = MaterialTheme.typography.bodyMedium,
                        modifier = Modifier.padding(top = 4.dp, bottom = 8.dp),
                    )
                    Text(
                        current.description ?: "No description",
                        style = MaterialTheme.typography.bodyMedium,
                    )
                    Text(
                        "Tech: ${current.technicianName ?: "—"}",
                        style = MaterialTheme.typography.bodySmall,
                        modifier = Modifier.padding(top = 8.dp),
                    )
                    Text(
                        "Window: ${current.scheduledStartIso ?: "—"} → ${current.scheduledEndIso ?: "—"}",
                        style = MaterialTheme.typography.bodySmall,
                    )
                    Text(
                        "updated_at: ${current.updatedAt}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )

                    Text(
                        "Status (queues offline)",
                        style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.padding(top = 16.dp, bottom = 6.dp),
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        STATUSES.take(3).forEach { s ->
                            TextButton(
                                onClick = {
                                    detail = repository.changeStatus(current.id, s)
                                    statusMessage = "Queued status → $s"
                                },
                            ) { Text(s) }
                        }
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        STATUSES.drop(3).forEach { s ->
                            TextButton(
                                onClick = {
                                    detail = repository.changeStatus(current.id, s)
                                    statusMessage = "Queued status → $s"
                                },
                            ) { Text(s) }
                        }
                    }

                    Text(
                        "Checklist",
                        style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.padding(top = 16.dp, bottom = 6.dp),
                    )
                    if (current.checklists.isEmpty()) {
                        Text("No checklists", style = MaterialTheme.typography.bodySmall)
                    } else {
                        current.checklists.forEach { cl ->
                            Text(cl.name, style = MaterialTheme.typography.bodyMedium)
                            cl.items.forEach { item ->
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    modifier = Modifier.fillMaxWidth(),
                                ) {
                                    Checkbox(
                                        checked = item.isCompleted,
                                        onCheckedChange = { checked ->
                                            detail =
                                                repository.toggleChecklist(
                                                    current.id,
                                                    item.id,
                                                    checked,
                                                )
                                            statusMessage =
                                                "Queued checklist ${item.label}"
                                        },
                                    )
                                    Text(
                                        buildString {
                                            append(item.label)
                                            if (item.pending) append(" · pending")
                                        },
                                        style = MaterialTheme.typography.bodyMedium,
                                    )
                                }
                            }
                        }
                    }

                    Text(
                        "Notes",
                        style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.padding(top = 16.dp, bottom = 6.dp),
                    )
                    OutlinedTextField(
                        value = noteDraft,
                        onValueChange = { noteDraft = it },
                        modifier = Modifier.fillMaxWidth(),
                        label = { Text("Add note (works offline)") },
                    )
                    Button(
                        onClick = {
                            if (noteDraft.isBlank()) return@Button
                            detail = repository.addNote(current.id, noteDraft)
                            noteDraft = ""
                            statusMessage = "Queued note"
                        },
                        modifier = Modifier.padding(top = 8.dp),
                    ) {
                        Text("Queue note")
                    }
                    current.notes.forEach { note ->
                        Text(
                            buildString {
                                append("• ")
                                append(note.text)
                                if (note.pending) append(" · pending")
                            },
                            style = MaterialTheme.typography.bodyMedium,
                            modifier = Modifier.padding(top = 4.dp),
                        )
                    }

                    Text(
                        "Sync",
                        style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.padding(top = 16.dp, bottom = 6.dp),
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(
                            onClick = {
                                val result = repository.drainQueue()
                                statusMessage = result.message
                                refreshDetail()
                            },
                        ) { Text("Drain queue") }
                        TextButton(onClick = { refreshDetail() }) { Text("Reload") }
                    }
                    statusMessage?.let {
                        Text(
                            it,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.primary,
                            modifier = Modifier.padding(top = 6.dp),
                        )
                    }

                    val conflicts = repository.conflicts(current.id)
                    if (conflicts.isNotEmpty()) {
                        Text(
                            "Conflicts (choose — never silent overwrite)",
                            style = MaterialTheme.typography.titleMedium,
                            color = MaterialTheme.colorScheme.error,
                            modifier = Modifier.padding(top = 16.dp, bottom = 6.dp),
                        )
                        conflicts.forEach { c ->
                            Surface(
                                color = MaterialTheme.colorScheme.errorContainer,
                                modifier =
                                    Modifier
                                        .fillMaxWidth()
                                        .padding(bottom = 8.dp),
                            ) {
                                Column(Modifier.padding(12.dp)) {
                                    Text(c.localSummary, style = MaterialTheme.typography.bodyMedium)
                                    Text(
                                        c.serverSummary,
                                        style = MaterialTheme.typography.bodySmall,
                                        modifier = Modifier.padding(top = 4.dp),
                                    )
                                    Row(
                                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                                        modifier = Modifier.padding(top = 8.dp),
                                    ) {
                                        Button(
                                            onClick = {
                                                detail =
                                                    repository.resolveConflict(
                                                        c.op.id,
                                                        ConflictResolution.KEEP_LOCAL,
                                                    )
                                                statusMessage =
                                                    "Keep local — will retry with fresh base"
                                            },
                                        ) { Text("Keep local") }
                                        TextButton(
                                            onClick = {
                                                detail =
                                                    repository.resolveConflict(
                                                        c.op.id,
                                                        ConflictResolution.TAKE_SERVER,
                                                    )
                                                statusMessage = "Took server version"
                                            },
                                        ) { Text("Take server") }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun AgendaJobCard(job: WorkOrderSummary, onClick: () -> Unit) {
    Surface(
        tonalElevation = 2.dp,
        modifier =
            Modifier
                .fillMaxWidth()
                .clickable(onClick = onClick),
    ) {
        Column(Modifier.padding(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text(job.title, style = MaterialTheme.typography.titleMedium)
                SyncBadgeChip(job.syncBadge)
            }
            Text(job.customerName, style = MaterialTheme.typography.bodyMedium)
            Text(
                "${job.status} · ${job.priority} · ${job.scheduledStartIso ?: "unscheduled"}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun SyncBadgeChip(badge: SyncBadge) {
    if (badge == SyncBadge.NONE) return
    val (label, color) =
        when (badge) {
            SyncBadge.PENDING -> "Pending" to Color(0xFFB8860B)
            SyncBadge.SYNCING -> "Syncing" to Color(0xFF1565C0)
            SyncBadge.CONFLICT -> "Conflict" to Color(0xFFC62828)
            SyncBadge.FAILED -> "Failed" to Color(0xFF6A1B9A)
            SyncBadge.NONE -> return
        }
    Text(
        label,
        style = MaterialTheme.typography.labelMedium,
        color = color,
    )
}
