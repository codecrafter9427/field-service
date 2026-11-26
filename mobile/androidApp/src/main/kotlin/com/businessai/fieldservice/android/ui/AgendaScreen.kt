package com.businessai.fieldservice.android.ui

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
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.businessai.fieldservice.agenda.AgendaRepository
import com.businessai.fieldservice.platformName

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AgendaScreen(
    repository: AgendaRepository = remember { AgendaRepository() },
) {
    val agenda = remember { repository.todayAgenda() }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Technician agenda") },
            )
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp),
        ) {
            Text(
                text = "Platform: ${platformName()} · Demo stubs only",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(bottom = 8.dp),
            )
            Text(
                text = "Date: ${agenda.dateIso}",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.padding(bottom = 12.dp),
            )
            Text(
                text = "Offline sync, signatures, and live API jobs are Coming Soon.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(bottom = 12.dp),
            )
            LazyColumn(
                contentPadding = PaddingValues(bottom = 24.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                items(agenda.jobs, key = { it.id }) { job ->
                    Card(
                        modifier = Modifier.fillMaxWidth(),
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
        }
    }
}
