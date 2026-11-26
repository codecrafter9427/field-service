package com.businessai.fieldservice.android.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.businessai.fieldservice.agenda.AgendaRepository
import com.businessai.fieldservice.models.JobDetail
import com.businessai.fieldservice.platformName

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AgendaScreen(
    repository: AgendaRepository = remember { AgendaRepository() },
) {
    val agenda = remember { repository.todayAgenda() }
    var selectedJobId by remember { mutableStateOf<String?>(null) }
    val detail: JobDetail? =
        remember(selectedJobId) {
            selectedJobId?.let { repository.jobDetail(it) }
        }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        if (detail == null) "Technician agenda" else "Job detail",
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
                    modifier = Modifier.padding(bottom = 8.dp),
                )
                Text(
                    text = "Date: ${agenda.dateIso}",
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.padding(bottom = 12.dp),
                )
                LazyColumn(
                    contentPadding = PaddingValues(bottom = 24.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    items(agenda.jobs, key = { it.id }) { job ->
                        Card(
                            modifier =
                                Modifier
                                    .fillMaxWidth()
                                    .clickable { selectedJobId = job.id },
                            colors = CardDefaults.cardColors(),
                        ) {
                            Column(Modifier.padding(14.dp)) {
                                Text(job.title, style = MaterialTheme.typography.titleMedium)
                                Text(job.customerName, style = MaterialTheme.typography.bodyMedium)
                                Text(
                                    "${job.status} · ${job.priority} · ${job.scheduledStartIso ?: "unscheduled"}",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                )
                            }
                        }
                    }
                }
            } else {
                Text(
                    text = "Tap back text below to return to agenda",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier =
                        Modifier
                            .padding(bottom = 8.dp)
                            .clickable { selectedJobId = null },
                )
                Text(detail.title, style = MaterialTheme.typography.headlineSmall)
                Text(
                    "${detail.status} · ${detail.priority}",
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.padding(top = 4.dp, bottom = 8.dp),
                )
                Text(
                    detail.description ?: "No description",
                    style = MaterialTheme.typography.bodyMedium,
                )
                Text(
                    "Tech: ${detail.technicianName ?: "—"}",
                    style = MaterialTheme.typography.bodySmall,
                    modifier = Modifier.padding(top = 8.dp),
                )
                Text(
                    "Window: ${detail.scheduledStartIso ?: "—"} → ${detail.scheduledEndIso ?: "—"}",
                    style = MaterialTheme.typography.bodySmall,
                )
                Text(
                    "Notes",
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.padding(top = 16.dp, bottom = 6.dp),
                )
                detail.notes.forEach { note ->
                    Text("• $note", style = MaterialTheme.typography.bodyMedium)
                }
                if (detail.notes.isEmpty()) {
                    Text("No notes", style = MaterialTheme.typography.bodySmall)
                }
            }
        }
    }
}
